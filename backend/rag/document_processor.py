import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import PyPDF2
import pdfplumber
from utils.logger import log

class DocumentProcessor:
    """Process PDF and text documents for RAG ingestion"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        log.info(f"Initialized DocumentProcessor (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    def process_pdf(self, file_path: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process PDF file and extract text chunks (optimized for speed)
        
        Args:
            file_path: Path to PDF file
            max_pages: Maximum number of pages to process (None = all pages)
            
        Returns:
            List of document chunks with metadata
        """
        try:
            log.info(f"Processing PDF: {file_path}")
            file_size = os.path.getsize(file_path)
            log.info(f"PDF file size: {file_size / 1024 / 1024:.2f} MB")
            
            # Try pdfplumber first (better for tables)
            text_parts = []
            total_pages = 0
            
            try:
                with pdfplumber.open(file_path) as pdf:
                    total_pages = len(pdf.pages)
                    log.info(f"PDF has {total_pages} pages")
                    
                    # Limit pages if specified
                    pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                    
                    # Fast sequential extraction (pdfplumber is already optimized)
                    # Parallel extraction doesn't help much due to GIL and file I/O
                    text_parts = []
                    for i, page in enumerate(pdf.pages[:pages_to_process]):
                        # Fast extraction - skip empty pages immediately
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(page_text)
                        
                        # Progress update every 50 pages (less frequent for speed)
                        if (i + 1) % 50 == 0:
                            log.info(f"Extracted {i + 1}/{pages_to_process} pages...")
                    
                    # Join all text parts efficiently (single operation)
                    text = "\n".join(text_parts)
                
            except Exception as e:
                log.warning(f"pdfplumber failed: {e}, trying PyPDF2")
                # Fallback to PyPDF2 (faster but less accurate)
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                    
                    # Fast PyPDF2 extraction
                    text_parts = []
                    for i, page in enumerate(pdf_reader.pages[:pages_to_process]):
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(page_text)
                    
                    text = "\n".join(text_parts)
            
            if not text or not text.strip():
                log.warning(f"No text extracted from PDF: {file_path}")
                return []
            
            log.info(f"Extracted {len(text)} characters from PDF")
            
            # Extract metadata
            file_name = Path(file_path).stem
            file_size = os.path.getsize(file_path)
            
            # Fast chunking
            log.info("Chunking text...")
            chunks = self._chunk_text_fast(text, file_name, file_path, file_size)
            
            log.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks
            
        except Exception as e:
            log.error(f"Error processing PDF {file_path}: {e}")
            import traceback
            log.error(traceback.format_exc())
            return []
    
    def process_text(self, text: str, source: str = "unknown") -> List[Dict[str, Any]]:
        """
        Process plain text and create chunks
        
        Args:
            text: Text content
            source: Source identifier
            
        Returns:
            List of document chunks
        """
        chunks = self._chunk_text(text, source, source, len(text))
        return chunks
    
    def _chunk_text_fast(
        self,
        text: str,
        source_name: str,
        source_path: str,
        source_size: int
    ) -> List[Dict[str, Any]]:
        """
        Fast chunking algorithm optimized for speed
        
        Args:
            text: Full text content
            source_name: Name of source document
            source_path: Path to source document
            source_size: Size of source document
            
        Returns:
            List of chunk dictionaries
        """
        # Fast text cleaning (minimal processing)
        if not text or not text.strip():
            return []
        
        # Normalize whitespace efficiently
        text = " ".join(text.split())
        
        if len(text) <= self.chunk_size:
            return [{
                "text": text,
                "metadata": {
                    "source": source_name,
                    "source_path": source_path,
                    "source_size": source_size,
                    "chunk_index": 0,
                    "total_chunks": 1,
                }
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        text_len = len(text)
        
        # Pre-calculate common values
        step_size = self.chunk_size - self.chunk_overlap
        
        while start < text_len:
            # Calculate end position
            end = min(start + self.chunk_size, text_len)
            
            # Fast boundary detection (only if not at end)
            if end < text_len:
                # Quick sentence boundary check (most common case first)
                last_period = text.rfind('. ', start, end)
                if last_period != -1:
                    end = last_period + 2
                else:
                    # Fallback to word boundary (faster than checking all punctuation)
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1:
                        end = last_space + 1
            
            # Extract chunk (avoid strip if possible)
            chunk_text = text[start:end]
            if chunk_text.strip():  # Only process non-empty chunks
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "source_path": source_path,
                        "source_size": source_size,
                        "chunk_index": chunk_index,
                        "char_start": start,
                        "char_end": end,
                    }
                })
                chunk_index += 1
            
            # Move start position with overlap (optimized)
            start += step_size
            if start >= end:
                start = end
        
        # Update total_chunks in metadata (batch update)
        total = len(chunks)
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = total
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        source_name: str,
        source_path: str,
        source_size: int
    ) -> List[Dict[str, Any]]:
        """Alias for fast chunking"""
        return self._chunk_text_fast(text, source_name, source_path, source_size)