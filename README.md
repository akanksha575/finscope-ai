# FinScope AI v1.0

<div align="center">

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**Intelligent Financial Deep Research Agent for IT, Pharmaceutical, Architecture, and Energy Sectors**

[Features](#-features) • [Quick Start](#-quick-start) • [Docker](#-docker-quick-start-recommended) • [Architecture](#-architecture) • [API Usage](#-api-usage) • [Troubleshooting](#-troubleshooting)

</div>

---

## 📋 Overview

**FinScope AI** is an advanced AI-powered research platform that conducts deep financial analysis and generates comprehensive research reports for IT, Pharmaceutical, Architecture, and Energy companies. Built with LangGraph, FastAPI, Django, and React, it combines **Hybrid RAG** (ColBERT + BM25), web search, specialized sector agents, and iterative intelligence to deliver actionable insights.

The system intelligently classifies queries, creates detailed research plans, executes multi-step iterative research workflows, and produces professional reports with citations and sources. **All research prioritizes the most recent sources (2024-2025)** to ensure up-to-date financial analysis and market intelligence.

---

## ✨ Features

### 🔍 Core Capabilities

- **Intelligent Query Classification** - Automatically identifies IT, Pharma, Architecture, and Energy sector queries with confidence scoring using GPT-4o-mini
- **Deep Research Planning** - Generates comprehensive research plans with dynamically generated clarification questions
- **Iterative Research Execution** - Multi-step iterative research workflow using LangGraph with real-time progress tracking
- **Sector-Specific Agents** - Specialized AI agents (IT, Pharma, Architecture, and Energy) with domain expertise, focus areas, and iterative intelligence
- **Hybrid RAG System** - Combines ColBERT (neural) and BM25 (lexical) retrieval with HyDE query expansion and cross-encoder reranking
- **Web Search Integration** - Real-time web search using Tavily API for up-to-date information (prioritizes 2024-2025 sources)
- **Financial Data Analysis** - Integrates yfinance for financial metrics and market data (latest data from Yahoo Finance)
- **Comprehensive Report Generation** - Produces detailed reports (HTML, Markdown, PDF) with citations, sources, and financial calculations
- **Analytics Dashboard** - System metrics, query analytics, and performance monitoring

### 🎨 User Interface

- **Three-Panel Layout** - History, Main Content, and Activity/Sources panels
- **Real-Time Updates** - WebSocket-based live progress tracking
- **Interactive Plan Selection** - Choose clarification questions before research
- **Report Viewer** - Markdown-rendered reports with proper formatting
- **Source Citations** - Track all sources and URLs used in research
- **Responsive Design** - Works seamlessly on desktop and mobile devices

### 🛡️ Safety & Quality

- **Guardrails System** - Content filtering, rate limiting, and safety validation
- **Query Validation** - Ensures queries are appropriate and safe
- **Error Handling** - Robust error handling and recovery mechanisms
- **Rate Limiting** - Per-minute, per-hour, and per-day rate limits

---

## 🚀 Quick Start

### Installation Options

You can run FinScope AI in two ways:
1. **🐳 Docker (Recommended)** - Run everything with a single command
2. **💻 Manual Setup** - Install and run services individually

### Prerequisites

**For Docker:**
- Docker **20.10+** and Docker Compose **2.0+** ([Download](https://www.docker.com/get-started) - Latest 2024-2025)
- Git ([Download](https://git-scm.com/downloads) - Latest 2024-2025)

**For Manual Setup:**
- Python **3.11+** or **3.12** ([Download](https://www.python.org/downloads/) - Latest 2024-2025 versions)
- Node.js **18+** or **20+** and npm ([Download](https://nodejs.org/en/download) - Latest LTS 2024-2025)
- Git ([Download](https://git-scm.com/downloads) - Latest 2024-2025)

### Required API Keys

1. **OpenAI API Key** - Sign up at [platform.openai.com](https://platform.openai.com/) (Latest 2024-2025)
2. **Tavily API Key** - Sign up at [tavily.com](https://tavily.com/) (Latest 2024-2025)

---

## 🐳 Docker Quick Start (Recommended)

The easiest way to run FinScope AI is using Docker. All services (backend, frontend, database) run in isolated containers.

### 1. Clone Repository

```bash
git clone <repository-url>
cd finscope-ai
```

### 2. Configure Environment

Create `docker/.env` file:

```bash
cd docker
cat > .env << 'EOF'
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional API Keys
JINA_AI_API_KEY=your_jina_ai_api_key_here

# Database (SQLite by default, or use PostgreSQL)
DATABASE_URL=sqlite:///db.sqlite3

# Django Settings
DJANGO_SECRET_KEY=change-this-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# CORS
CORS_ORIGINS=http://localhost:80,http://localhost:3000,http://localhost:5173

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=80

# Frontend API URL (internal Docker network)
VITE_API_URL=http://backend:8000
EOF
```

### 3. Build and Start

```bash
# Build and start all services
docker-compose up -d --build

# Or using Makefile (if available)
make build
make up
```

### 4. Access the Application

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Or using Makefile
make logs
make logs-backend
```

### 6. Stop Services

```bash
docker-compose down

# Or remove volumes (clean slate)
docker-compose down -v

# Or using Makefile
make down
make down-volumes
```

### Using PostgreSQL (Optional)

To use PostgreSQL instead of SQLite:

1. Update `docker/.env`:
```env
DATABASE_URL=postgresql://finscope:finscope123@postgres:5432/finscope
```

2. Start with PostgreSQL:
```bash
docker-compose --profile postgres up -d
# Or: make up-postgres
```

### Common Docker Commands

```bash
# View running containers
docker-compose ps
# Or: make ps

# Restart services
docker-compose restart
# Or: make restart

# Run Django migrations
docker-compose exec backend python manage.py migrate
# Or: make migrate

# Open backend shell
docker-compose exec backend bash
# Or: make shell-backend

# Rebuild after code changes
docker-compose up -d --build
```

### Docker Documentation

For detailed Docker documentation, see:
- **[Docker README](docker/README.md)** - Complete Docker guide
- **[Quick Start Guide](docker/QUICKSTART.md)** - Quick reference

---

## 💻 Manual Setup

If you prefer to run services manually without Docker:

### 1. Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd finscope-ai

# Backend setup
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `backend/.env` file:

```env
# API Keys (Required)
OPENAI_API_KEY=sk-your-openai-api-key-here
TAVILY_API_KEY=tvly-your-tavily-api-key-here

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./data/chromadb
CHROMA_COLLECTION_IT=it_sector_docs
CHROMA_COLLECTION_PHARMA=pharma_sector_docs

# Research Configuration
MIN_RESEARCH_STEPS=5
MAX_RESEARCH_STEPS=20

# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Initialize Database & ChromaDB

```bash
# Initialize Django database
python manage.py migrate

# Initialize ChromaDB collections (will be created automatically on first use)
# Or manually:
python -c "import chromadb; client = chromadb.PersistentClient(path='./data/chromadb'); client.create_collection('it_sector_docs'); client.create_collection('pharma_sector_docs')"
```

### 4. Pre-train Documents (Optional)

```bash
# Pre-train documents from data/raw_reports directory
python scripts/pretrain_documents.py
```

### 5. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000/api" > .env
echo "VITE_WS_BASE_URL=ws://localhost:8000/api" >> .env
echo "VITE_APP_NAME=FinScope AI" >> .env
```

### 6. Run the Application

**Terminal 1 - Django (Admin Panel):**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver 0.0.0.0:8001
daphne -b 0.0.0.0 -p 8000 django_app.asgi:application
```

**Terminal 2 - FastAPI (Main API):**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Access the Application

- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Django Admin**: http://localhost:8001/admin

---

## 🏗️ Architecture

### System Flow Diagram

```text
User Query (Frontend)
    ↓
FastAPI Backend (`main.py`)
    ↓
Query Router (GPT-4o-mini) → Classify Query (IT/Pharma/Unknown)
    ↓
Research Planner (GPT-4o) → Generate Research Plan with Questions
    ↓
Research Orchestrator (LangGraph Workflow)
    ├─ Sector-Specific Agent (IT/Pharma) - GPT-4o
    ├─ Hybrid RAG Retriever (ColBERT + BM25 + HyDE + Reranker)
    ├─ Web Search (Tavily)
    ├─ Financial Data (yfinance)
    ├─ Web Scraper (Jina AI + BeautifulSoup)
    └─ Calculator (Financial Metrics)
    ↓
Report Synthesizer (GPT-4o) → Synthesize Findings
    ↓
Report Formatter → Format (HTML/Markdown/PDF)
    ↓
Report Exporter → Export Final Report
```

### Component Architecture

```text
Backend Services:
├── API Layer (FastAPI)
│   ├── Health Router
│   ├── Classification Router
│   ├── Planning Router
│   ├── Research Router (WebSocket)
│   ├── Report Router
│   ├── RAG Router (Ingest/Retrieve)
│   └── Analytics Router
├── Agent Layer
│   ├── BaseAgent (Abstract Base Class)
│   ├── QueryRouter (Classification - GPT-4o-mini)
│   ├── ResearchPlanner (Plan Generation - GPT-4o)
│   ├── ITSectorAgent (IT Expertise - GPT-4o)
│   └── PharmaSectorAgent (Pharma Expertise - GPT-4o)
├── Research Layer
│   ├── ResearchOrchestrator (LangGraph Workflow)
│   ├── ToolExecutor (Tool Execution)
│   ├── QueryGenerator (Iterative Query Generation)
│   └── ResearchState (State Management)
├── RAG Layer
│   ├── VectorStore (ChromaDB Integration)
│   ├── HybridRetriever (ColBERT + BM25)
│   ├── EmbeddingGenerator (Sentence Transformers)
│   ├── QueryExpander (HyDE - Hypothetical Document Embeddings)
│   └── Reranker (Cross-Encoder Reranking)
├── Reports Layer
│   ├── ReportSynthesizer (GPT-4o with Financial Calculations)
│   ├── ReportFormatter (HTML/Markdown/PDF)
│   └── ReportExporter (File Export)
├── Tools Layer
│   ├── WebSearch (Tavily API)
│   ├── WebScraper (Jina AI + BeautifulSoup)
│   ├── FinancialData (yfinance)
│   ├── Calculator (Financial Metrics)
│   └── MCPTools (Tool Registry)
├── Guardrails Layer
│   ├── SafetyChecker (Orchestrator)
│   ├── ContentFilter (Content Validation)
│   └── RateLimiter (Rate Limiting)
├── Analytics Layer
│   ├── AnalyticsService (Metrics Collection)
│   └── AnalyticsCalculator (Metric Calculations)
└── Core Layer (Django ORM)
    ├── Query Model
    ├── ResearchStep Model
    └── Report Model
```

---

## 📖 Core Components

### 1. `main.py` – FastAPI Entry Point

- Creates FastAPI app with CORS configuration
- Registers routers for all endpoints
- Initializes pre-training check on startup
- Exposes utility endpoints: `/health`, `/stats`

### 2. `agents/query_router.py` – Query Classification

- Classifies queries into IT, Pharma, or Unknown sectors
- Uses **GPT-4o-mini** for fast, cost-effective classification
- Includes safety validation and guardrails
- Returns confidence scores and reasoning

### 3. `agents/research_planner.py` – Research Planning

- Generates comprehensive research plans with **GPT-4o**
- Creates dynamically generated clarification questions
- Supports deep research mode with 18 steps
- Plans include step-by-step research strategy

### 4. `agents/it_sector_agent.py` & `pharma_sector_agent.py` – Sector Specialists

- Domain-specific knowledge for IT and Pharma sectors
- Focus areas and key metrics for each sector
- Enhanced query understanding and context
- Iterative intelligence for follow-up queries
- Coverage validation and gap identification

### 5. `research/orchestrator.py` – Research Workflow

- **LangGraph-based** iterative research execution
- Coordinates multiple research tools in parallel
- Manages research state and progress
- Implements iterative intelligence loop
- WebSocket-based real-time progress updates

### 6. `rag/` – Hybrid RAG Components

- **VectorStore**: ChromaDB integration for document storage
- **HybridRetriever**: Combines ColBERT (neural) and BM25 (lexical) retrieval
- **EmbeddingGenerator**: Sentence Transformers for embeddings
- **QueryExpander**: HyDE (Hypothetical Document Embeddings) for query expansion
- **Reranker**: Cross-encoder reranking for result refinement
- **DocumentProcessor**: PDF, DOCX processing and chunking

### 7. `tools/` – Research Tools

- **WebSearch**: Tavily API integration for web search
- **WebScraper**: Jina AI Reader + BeautifulSoup for web content extraction
- **FinancialData**: yfinance integration for financial metrics and market data
- **Calculator**: Financial metric calculations (ROE, P/E, Debt-to-Equity, etc.)
- **MCPTools**: Tool registry and execution framework

### 8. `reports/` – Report Generation

- **ReportSynthesizer**: GPT-4o-based report synthesis with financial calculations
- **ReportFormatter**: Formats reports into HTML, Markdown, and PDF structures
- **ReportExporter**: Exports formatted reports to files

### 9. `guardrails/` – Safety & Validation

- **SafetyChecker**: Orchestrates all safety checks
- **ContentFilter**: Filters sensitive content and validates financial scope
- **RateLimiter**: Per-minute, per-hour, per-day rate limiting

### 10. `analytics/` – Analytics & Monitoring

- **AnalyticsService**: Collects and aggregates system metrics
- **AnalyticsCalculator**: Calculates query, report, and research step metrics

---

## ⚙️ Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | _required_ | OpenAI API key for GPT models |
| `TAVILY_API_KEY` | _required_ | Tavily API key for web search |
| `DEBUG` | `True` | Django debug mode |
| `SECRET_KEY` | _required_ | Django secret key |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chromadb` | ChromaDB storage path |
| `CHROMA_COLLECTION_IT` | `it_sector_docs` | IT sector collection name |
| `CHROMA_COLLECTION_PHARMA` | `pharma_sector_docs` | Pharma sector collection name |
| `MIN_RESEARCH_STEPS` | `5` | Minimum research steps |
| `MAX_RESEARCH_STEPS` | `20` | Maximum research steps |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Backend API URL |
| `VITE_WS_BASE_URL` | `ws://localhost:8000/api` | WebSocket URL |
| `VITE_APP_NAME` | `FinScope AI` | Application name |

---

## 📡 API Usage

### Base URLs

- API base: `http://localhost:8000`
- Main API prefix: `/api`

### Key Endpoints

#### Health Check

```http
GET    /api/health              # Health check
GET    /api/stats               # System statistics
```

#### Classification

```http
POST   /api/classify              # Classify query into sector
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze Infosys financial performance"}'
```

#### Research Planning

```http
POST   /api/plan                  # Generate research plan
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare TCS and Infosys cloud services",
    "sector": "IT",
    "mode": "deep"
  }'
```

#### Research Execution

```http
POST   /api/research              # Start research workflow
GET    /api/research/{id}         # Get research status
WS     /api/research/stream       # WebSocket for real-time updates
```

#### Reports

```http
GET    /api/report/{id}           # Get generated report
POST   /api/report/{id}/export   # Export report as PDF/HTML/Markdown
```

#### RAG & Retrieval

```http
POST   /api/retrieve              # Retrieve documents from RAG
POST   /api/ingest                # Ingest documents into RAG
```

#### Analytics

```http
GET    /api/analytics/metrics     # Get system metrics
GET    /api/analytics/queries     # Get query analytics
```

### Example Research Flow

1. **Classify Query**
   ```bash
   POST /api/classify
   {"query": "Analyze Sun Pharma drug pipeline"}
   ```

2. **Generate Plan**
   ```bash
   POST /api/plan
   {"query": "...", "sector": "Pharma", "mode": "deep"}
   ```

3. **Start Research (WebSocket)**
   ```bash
   WS /api/research/stream
   {
     "query": "...",
     "sector": "Pharma",
     "plan": {...},
     "selected_questions": [...]
   }
   ```

4. **Get Report**
   ```bash
   GET /api/report/{research_id}
   ```

---

## 📁 Directory Structure

```text
finscope-ai/
├── backend/
│   ├── api/                      # FastAPI application
│   │   ├── routes/              # API endpoints
│   │   │   ├── health.py
│   │   │   ├── classify.py
│   │   │   ├── plan.py
│   │   │   ├── research.py
│   │   │   ├── report.py
│   │   │   ├── ingest.py
│   │   │   ├── retrieve.py
│   │   │   └── analytics.py
│   │   └── schemas/             # Pydantic models
│   ├── agents/                  # AI agents
│   │   ├── base_agent.py        # Abstract base class
│   │   ├── query_router.py      # Query classification
│   │   ├── research_planner.py  # Research planning
│   │   ├── it_sector_agent.py   # IT sector specialist
│   │   └── pharma_sector_agent.py # Pharma sector specialist
│   ├── research/                # Research orchestration
│   │   ├── orchestrator.py     # LangGraph workflow
│   │   ├── query_generator.py  # Iterative query generation
│   │   ├── tool_executor.py    # Tool execution
│   │   └── state.py            # Research state
│   ├── tools/                   # Research tools
│   │   ├── base_tool.py        # Abstract base class
│   │   ├── web_search.py        # Tavily search
│   │   ├── web_scraper.py       # Web scraping
│   │   ├── financial_data.py     # Financial APIs (yfinance)
│   │   ├── calculator.py        # Financial calculations
│   │   └── mcp_tools.py        # Tool registry
│   ├── rag/                     # RAG components
│   │   ├── retriever.py        # Hybrid retrieval (ColBERT + BM25)
│   │   ├── embeddings.py        # Embedding generation
│   │   ├── vector_store.py      # ChromaDB integration
│   │   ├── query_expansion.py   # HyDE query expansion
│   │   ├── reranker.py         # Cross-encoder reranking
│   │   └── document_processor.py # Document processing
│   ├── reports/                 # Report generation
│   │   ├── synthesizer.py      # Report synthesis
│   │   ├── formatter.py        # Report formatting
│   │   └── exporter.py         # Report export
│   ├── guardrails/              # Safety & validation
│   │   ├── safety_checker.py   # Safety orchestrator
│   │   ├── content_filter.py   # Content filtering
│   │   └── rate_limiter.py     # Rate limiting
│   ├── analytics/               # Analytics & monitoring
│   │   ├── service.py          # Analytics service
│   │   └── calculator.py       # Metric calculations
│   ├── core/                    # Django models
│   │   ├── models.py           # Database models
│   │   └── admin.py            # Django admin
│   ├── django_app/              # Django configuration
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── utils/                   # Helper functions
│   │   ├── logger.py           # Logging setup
│   │   ├── helpers.py          # Utility functions
│   │   ├── prompts.py          # Prompt templates
│   │   └── pretrain_init.py    # Pre-training initialization
│   ├── data/                    # Data storage
│   │   ├── chromadb/           # ChromaDB data
│   │   ├── documents/          # Processed documents
│   │   └── uploads/            # User uploads
│   ├── outputs/                 # Generated outputs
│   │   └── reports/            # Generated reports
│   ├── logs/                    # Application logs
│   ├── main.py                  # FastAPI entry point
│   ├── manage.py                # Django management
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── Layout/         # Three-panel layout
│   │   │   ├── Chat/           # Query input & reports
│   │   │   ├── Activity/       # Real-time activity feed
│   │   │   ├── Sources/        # Citations and sources
│   │   │   └── Common/         # Common components
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API clients
│   │   ├── types/               # TypeScript types
│   │   └── utils/               # Utilities
│   └── package.json             # Node dependencies
│
├── scripts/                     # Automation scripts
│   └── pretrain_documents.py   # Document pre-training
│
├── data/                        # Raw data
│   └── raw_reports/            # Raw PDF reports
│
└── README.md                    # This file
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | FastAPI 0.109.0 |
| **Server** | Uvicorn 0.27.0 |
| **ORM/Database** | Django 5.0.1 + Django ORM |
| **Frontend Framework** | React 19.2.0 |
| **Frontend Language** | TypeScript 5.9.3 |
| **Build Tool** | Vite 7.2.4 |
| **Styling** | Tailwind CSS 3.4.1 |
| **Workflow Engine** | LangGraph 0.0.20+ |
| **LLM Framework** | LangChain 0.1.x |
| **LLM Provider** | OpenAI GPT-4o, GPT-4o-mini |
| **Vector Database** | ChromaDB 0.4.22 |
| **Embeddings** | Sentence Transformers 2.3.1 |
| **RAG Techniques** | ColBERT, BM25, HyDE, Cross-Encoder Reranking |
| **Web Search** | Tavily API |
| **Financial Data** | yfinance 0.2.36 |
| **Document Processing** | PyPDF2, pdfplumber, python-docx |
| **Validation** | Pydantic 2.0+ |
| **Language** | Python 3.11+ |

---

## 📖 Usage Examples

### IT Sector Queries

- "Analyze Infosys financial performance and market position"
- "Compare TCS, Infosys, and Wipro's cloud services"
- "What are the emerging trends in Indian IT services sector?"
- "Research Wipro's AI strategy and competitive advantages"

### Pharma Sector Queries

- "Analyze Sun Pharma's drug pipeline and R&D strategy"
- "Compare R&D spending across top 3 Indian pharma companies"
- "What are the key trends in Indian pharmaceutical R&D?"
- "Research Dr. Reddy's biosimilar portfolio and market position"

### Research Workflow

1. **Enter Query** - Type your research question in the frontend
2. **Auto-Classification** - System identifies IT or Pharma sector using GPT-4o-mini
3. **Plan Generation** - Review research plan and select clarification questions
4. **Research Execution** - Watch real-time progress in Activity panel via WebSocket
5. **Iterative Intelligence** - System generates follow-up queries based on findings
6. **Report Generation** - View comprehensive report with citations and financial calculations
7. **Review Sources** - Check all sources and URLs in Sources panel

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pytest
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run lint
npm run build
```

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# macOS / Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Module Not Found Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### ChromaDB Issues

```bash
# Reinitialize ChromaDB
rm -rf backend/data/chromadb
python -c "import chromadb; client = chromadb.PersistentClient(path='./backend/data/chromadb'); client.create_collection('it_sector_docs'); client.create_collection('pharma_sector_docs')"
```

### CORS Errors

- Verify `CORS_ORIGINS` in `backend/.env` includes your frontend URL
- Check `backend/main.py` CORS middleware configuration

### API Key Issues

- Verify API keys in `.env` file
- Restart servers after changing `.env`
- Check OpenAI and Tavily API key validity

### WebSocket Connection Issues

- Ensure FastAPI server is running on port 8000
- Check WebSocket URL in frontend `.env` file
- Verify CORS settings allow WebSocket connections

---

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration (if available)
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI
- **Architecture** - See Architecture section above
- **Component Details** - See Core Components section above

---

## 🐳 Docker Deployment

Docker is the **recommended** way to run FinScope AI. See the [Docker Quick Start](#-docker-quick-start-recommended) section above for complete instructions.

### Docker Features

- ✅ **Single Command Setup** - Run everything with `docker-compose up`
- ✅ **Isolated Services** - Backend, frontend, and database in separate containers
- ✅ **Data Persistence** - All data stored in Docker volumes
- ✅ **Health Checks** - Automatic service health monitoring
- ✅ **Production Ready** - Optimized builds and security configurations
- ✅ **Easy Scaling** - Add more services or scale as needed

### Docker Services

- **Backend** (`finscope-backend`) - FastAPI + Django on port 8000
- **Frontend** (`finscope-frontend`) - React app served via Nginx on port 80
- **PostgreSQL** (`finscope-postgres`) - Optional database on port 5432

### Docker Documentation

- **[Docker README](docker/README.md)** - Complete setup and configuration guide
- **[Quick Start Guide](docker/QUICKSTART.md)** - Quick reference commands
- **[Makefile](docker/Makefile)** - Convenience commands for common operations

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📝 License

MIT License – see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author & Support

- **Author**: Noorain Fathima – AI / Backend Specialist  
- **Contact**: fnoorain0609@gmail.com

For help:

- Check **Swagger UI** at `http://localhost:8000/docs`
- Use `/api/health` and `/api/stats` endpoints to verify system status
- Review server logs in `backend/logs/finscope.log`
- Check the documentation sections above for detailed guides

---

Made with ❤️ for intelligent financial research
