import os
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.logger import log
from utils.helpers import get_env
from utils.cache import get_cache_manager, generate_cache_key, CACHE_TTL

class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of sentence-transformers model
        """
        self.model_name = model_name or get_env(
            "EMBEDDING_MODEL",
            default="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        log.info(f"Loading embedding model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            log.info(f"Loaded model with dimension: {self.embedding_dim}")
        except Exception as e:
            log.error(f"Failed to load embedding model: {e}")
            raise
    
    async def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for texts (with caching)
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            numpy array of embeddings (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        # Check cache for each text
        cache = await get_cache_manager()
        cached_embeddings = []
        uncached_indices = []
        uncached_texts = []
        
        for i, text in enumerate(texts):
            cache_key = generate_cache_key("embedding", text, model=self.model_name)
            cached = await cache.get(cache_key)
            if cached is not None:
                cached_embeddings.append((i, np.array(cached)))
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        # If all cached, return in order
        if not uncached_texts:
            result = np.zeros((len(texts), self.embedding_dim))
            for idx, emb in cached_embeddings:
                result[idx] = emb
            return result
        
        # Generate embeddings for uncached texts
        try:
            new_embeddings = self.model.encode(
                uncached_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Cache new embeddings
            for text, embedding in zip(uncached_texts, new_embeddings):
                cache_key = generate_cache_key("embedding", text, model=self.model_name)
                await cache.set(
                    cache_key,
                    embedding.tolist(),  # Convert to list for JSON serialization
                    ttl=CACHE_TTL["embedding"]
                )
            
            # Combine cached and new embeddings
            if cached_embeddings:
                result = np.zeros((len(texts), self.embedding_dim))
                # Fill in cached embeddings
                for idx, emb in cached_embeddings:
                    result[idx] = emb
                # Fill in new embeddings
                for i, (orig_idx, _) in enumerate(zip(uncached_indices, uncached_texts)):
                    result[uncached_indices[i]] = new_embeddings[i]
                return result
            else:
                return new_embeddings
                
        except Exception as e:
            log.error(f"Error generating embeddings: {e}")
            raise
    
    async def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text (with caching)"""
        result = await self.encode([text])
        return result[0]
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim