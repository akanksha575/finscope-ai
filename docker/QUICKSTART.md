# Quick Start Guide

## 1. Setup Environment Variables

Create a `.env` file in the `docker/` directory:

```bash
cd docker
cat > .env << 'EOF'
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional API Keys
JINA_AI_API_KEY=your_jina_ai_api_key_here

# Database (use SQLite by default)
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

## 2. Build and Start

```bash
# Build and start all services
docker-compose up -d --build

# Or use Makefile
make build
make up
```

## 3. Access the Application

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 4. View Logs

```bash
# All services
docker-compose logs -f

# Or use Makefile
make logs
make logs-backend
make logs-frontend
```

## 5. Stop Services

```bash
docker-compose down

# Or use Makefile
make down
```

## Using PostgreSQL (Optional)

To use PostgreSQL instead of SQLite:

1. Update `.env`:
```bash
DATABASE_URL=postgresql://finscope:finscope123@postgres:5432/finscope
```

2. Start with PostgreSQL profile:
```bash
docker-compose --profile postgres up -d

# Or use Makefile
make up-postgres
```

## Common Commands

```bash
# View running containers
make ps

# Restart services
make restart

# Run Django migrations
make migrate

# Open backend shell
make shell-backend

# Clean everything (removes volumes)
make down-volumes
```








