# Development Commands

## Docker Commands (Primary Development)
```bash
# Start all services (preferred development method)
docker-compose up -d --build

# View real-time logs
docker-compose logs -f backend frontend

# Execute commands in containers for debugging
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_backend python -m pytest tests/
docker exec -it migration_db psql -U user -d migration_db

# Health checks
curl http://localhost:8000/health
curl http://localhost:8081

# Rebuild with latest changes
./docker-rebuild.sh
```

## Project Commands
```bash
# Frontend development
npm run dev
npm run build
npm run test
npm run test:e2e

# Linting and type checking
npm run lint
npm run typecheck

# Backend testing
npm run test:backend:agents
npm run test:backend:integration
```

## System Information
- Platform: darwin (macOS)
- Python: Use `/opt/homebrew/bin/python3.11@` for all Python executions
- Git CLI: Use `/opt/homebrew/bin/gh` for all Git CLI tools
- Development Environment: Docker containers (never run services locally)
- Frontend: http://localhost:8081
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
