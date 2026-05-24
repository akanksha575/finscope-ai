# PDF Upload Feature for Research Reports

## Overview

The FinScope AI research system now supports PDF file uploads. Users can upload a PDF document, ask a query, and the system will generate a research report based **entirely on the uploaded PDF** instead of web search.

## How It Works

### 1. **PDF Upload Endpoint**

**Endpoint:** `POST /api/research/start/pdf`

**Request Format:**
- Content-Type: `multipart/form-data`
- Fields:
  - `query` (string, required): Research query
  - `sector` (string, required): "IT" or "Pharma"
  - `pdf_file` (file, required): PDF file to upload
  - `selected_questions` (string, optional): JSON array of selected questions (default: "[]")

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/research/start/pdf" \
  -F "query=Analyze the revenue trends in this document" \
  -F "sector=IT" \
  -F "pdf_file=@/path/to/document.pdf" \
  -F "selected_questions=[]"
```

### 2. **PDF Processing Flow**

1. **Upload & Save**: PDF is saved to `./data/uploads/research/{uuid}_{filename}.pdf`
2. **Ingestion**: PDF is processed and ingested into the RAG (Retrieval-Augmented Generation) system
3. **Chunking**: PDF is split into searchable chunks with metadata
4. **Vectorization**: Chunks are embedded and stored in ChromaDB vector store
5. **Research**: Research queries use RAG retrieval instead of web search
6. **Report Generation**: Final report is generated based on PDF content

### 3. **RAG Integration**

When PDF mode is enabled (`use_pdf_only=True`):
- **Web search is disabled** - No external web queries are made
- **RAG retrieval is used** - All queries search the uploaded PDF
- **Hybrid retrieval** - Uses ColBERT + BM25 fusion for accurate results
- **Reranking** - Cross-encoder reranking ensures most relevant chunks

### 4. **State Management**

The research state now includes:
- `pdf_file_path`: Path to uploaded PDF file
- `use_pdf_only`: Boolean flag (True = PDF-only mode, False = web search mode)

## Architecture Changes

### Files Modified

1. **`api/routes/research.py`**
   - Added `/research/start/pdf` endpoint for PDF upload
   - Handles multipart form data
   - Ingests PDF into RAG before starting research

2. **`research/state.py`**
   - Added `pdf_file_path: Optional[str]`
   - Added `use_pdf_only: bool`

3. **`research/tool_executor.py`**
   - Added `use_pdf_only` parameter to `execute_sequential()`
   - Added `_execute_rag_search()` method
   - Switches between web search and RAG based on flag

4. **`research/orchestrator.py`**
   - Passes `use_pdf_only` flag to tool executor
   - Preserves PDF mode throughout workflow

5. **`api/routes/research_pdf_helper.py`** (NEW)
   - Helper function for PDF-based research execution
   - Separated to avoid circular imports

## Usage Examples

### Example 1: Upload PDF and Query

**Request:**
```json
POST /api/research/start/pdf
Content-Type: multipart/form-data

query: "What are the key financial highlights from Q3 2025?"
sector: "IT"
pdf_file: [PDF binary data]
```

**Response:**
```json
{
  "query_id": "uuid-here",
  "query": "What are the key financial highlights from Q3 2025?",
  "sector": "IT",
  "plan_type": "deep",
  "status": "completed",
  "report": {
    "title": "Research Report",
    "analysis": "...",
    "executive_summary": "...",
    "key_findings": [...]
  },
  "sources_used": ["pdf_rag"],
  "duration_seconds": 45.2
}
```

### Example 2: Using Python Requests

```python
import requests

url = "http://localhost:8000/api/research/start/pdf"

with open("annual_report.pdf", "rb") as pdf_file:
    files = {"pdf_file": pdf_file}
    data = {
        "query": "Analyze the revenue growth and operating margins",
        "sector": "Pharma",
        "selected_questions": "[]"
    }
    response = requests.post(url, files=files, data=data)
    result = response.json()
    print(result["report"]["analysis"])
```

## Benefits

1. **Document-Specific Analysis**: Reports are based solely on the uploaded document
2. **No External Dependencies**: No need for web search APIs
3. **Accurate Citations**: All citations reference the uploaded PDF
4. **Privacy**: PDF content stays on server (not sent to external APIs)
5. **Consistent Results**: Same PDF always produces consistent results

## Limitations

1. **Single PDF per Research**: Only one PDF can be uploaded per research session
2. **No Financial Data**: Financial data tool still uses external APIs (Yahoo Finance)
3. **PDF Size**: Large PDFs may take longer to process (configured via `PDF_MAX_PAGES` env var)
4. **Format Support**: Currently supports PDF format only

## Configuration

### Environment Variables

- `PDF_MAX_PAGES`: Maximum pages to process from PDF (default: 0 = all pages)

### Directory Structure

```
./data/uploads/research/  # PDF files stored here
```

## Error Handling

- **Invalid File Type**: Returns 400 if file is not a PDF
- **Empty PDF**: Returns 400 if no content extracted
- **Ingestion Failure**: Returns 500 if RAG ingestion fails
- **Processing Errors**: Errors are logged and returned in response

## Testing

To test the PDF upload feature:

1. **Prepare a PDF**: Create or use an existing PDF document
2. **Start the server**: `uvicorn main:app --reload`
3. **Upload PDF**: Use the `/api/research/start/pdf` endpoint
4. **Verify**: Check that report is based on PDF content, not web search

## Future Enhancements

- Support multiple PDF uploads per research session
- PDF format validation (encrypted, corrupted, etc.)
- Progress updates during PDF ingestion
- PDF preview before research starts
- Support for other document formats (DOCX, TXT, etc.)

## Notes

- PDFs are stored temporarily and can be cleaned up after research completes
- Vector store persists PDF chunks, so re-uploading same PDF may create duplicates
- PDF metadata (filename, upload time) is preserved in RAG chunks
