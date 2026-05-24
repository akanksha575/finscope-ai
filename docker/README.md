# FinScope AI Docker Setup

This directory contains Docker configuration files to run the entire FinScope AI application stack.

## Quick Start

1. **Copy environment file:**
   ```bash
   cp docker/.env.example docker/.env
   ```

2. **Edit `.env` file** and add your API keys:
   - `OPENAI_API_KEY` (required)
   - `TAVILY_API_KEY` (required)
   - `JINA_AI_API_KEY` (optional)

3. **Build and start all services:**
   ```bash
   cd docker
   docker-compose up -d --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:80
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Services

### Backend (`finscope-backend`)
- FastAPI application
- Django ORM for data persistence
- ChromaDB for vector storage
- Runs on port 8000

### Frontend (`finscope-frontend`)
- React + TypeScript + Vite
- Served via Nginx
- Runs on port 80

### PostgreSQL (`finscope-postgres`) - Optional
- Only starts if using `--profile postgres`
- Alternative to SQLite for production
- Runs on port 5432

## Commands

### Start all services:
```bash
docker-compose up -d
```

### Start with PostgreSQL:
```bash
docker-compose --profile postgres up -d
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop all services:
```bash
docker-compose down
```

### Stop and remove volumes (clean slate):
```bash
docker-compose down -v
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

### Execute commands in containers:
```bash
# Backend shell
docker-compose exec backend bash

# Run Django migrations
docker-compose exec backend python manage.py migrate

# Run Django shell
docker-compose exec backend python manage.py shell
```

## Development Mode

For development with hot-reload, you can mount the source code:

1. Uncomment the volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ../backend:/app
   ```

2. Use a development server command in `Dockerfile.backend`:
   ```dockerfile
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
   ```

## Production Considerations

1. **Change default secrets** in `.env`:
   - `DJANGO_SECRET_KEY` - Generate a strong secret
   - `POSTGRES_PASSWORD` - Use a strong password

2. **Use PostgreSQL** instead of SQLite:
   ```bash
   docker-compose --profile postgres up -d
   ```

3. **Set `DEBUG=False`** in production

4. **Configure proper CORS origins** in `.env`

5. **Use environment-specific `.env` files**

6. **Set up SSL/TLS** (use a reverse proxy like Traefik or Nginx)

## Troubleshooting

### Backend won't start:
- Check API keys are set in `.env`
- Check logs: `docker-compose logs backend`
- Verify database connection if using PostgreSQL

### Frontend can't connect to backend:
- Check `CORS_ORIGINS` in `.env` includes frontend URL
- Verify backend is running: `docker-compose ps`
- Check backend logs for errors

### Database issues:
- If using SQLite, ensure volume permissions are correct
- If using PostgreSQL, check connection string in `DATABASE_URL`
- Run migrations: `docker-compose exec backend python manage.py migrate`

### ChromaDB persistence:
- Data is stored in `backend_data` volume
- To reset: `docker-compose down -v` (removes all data)

## Volumes

- `postgres_data`: PostgreSQL database files
- `backend_data`: ChromaDB and document storage
- `backend_logs`: Application logs
- `backend_outputs`: Generated reports

## Network

All services are on the `finscope-network` bridge network and can communicate using service names:
- Frontend → Backend: `http://backend:8000`
- Backend → PostgreSQL: `postgres:5432`








