# Suggested Development Commands

## Essential Docker Commands
```bash
# Start development environment (primary workflow)
docker-compose up -d --build

# View real-time logs
docker-compose logs -f backend frontend

# Execute commands in containers
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_backend python -m pytest tests/
docker exec -it migration_db psql -U postgres -d migration_db

# Health checks
curl http://localhost:8000/health
curl http://localhost:8081

# Rebuild containers
docker-compose down && docker-compose up -d --build
```

## Frontend Development Commands
```bash
# Development server (inside container)
npm run dev

# Build for production
npm run build

# Type checking
npm run typecheck
tsc --noEmit

# Linting (various strictness levels)
npm run lint                    # Strict (0 warnings)
npm run lint:tolerant          # 200 warnings max
npm run lint:agent-ready       # 50 warnings max

# Testing
npm run test                   # Unit tests with Vitest
npm run test:e2e              # Playwright E2E tests
npm run test:e2e:journey      # Complete user journey test
```

## Backend Development Commands
```bash
# Run inside backend container
python main.py                          # Start FastAPI server
python -m pytest tests/ -v             # Run all tests
python -m pytest tests/backend/integration/ -v  # Integration tests
python -m alembic upgrade head         # Run database migrations
python -m alembic revision --autogenerate -m "description"  # Create migration

# Linting and formatting
black backend/                          # Code formatting
flake8 backend/                        # Linting
mypy backend/ --ignore-missing-imports # Type checking
bandit -r backend/ -ll                 # Security scanning
```

## Database Commands
```bash
# Access database
docker exec -it migration_db psql -U postgres -d migration_db

# Database operations
python -m alembic upgrade head         # Apply migrations
python -m alembic downgrade -1        # Rollback one migration
python -m alembic current             # Show current migration
python -m alembic history             # Show migration history
```

## Development Workflow Commands
```bash
# Complete development setup
git clone <repo>
cd migrate-ui-orchestrator
docker-compose up -d --build

# Daily development workflow
docker-compose logs -f backend frontend  # Monitor logs
docker exec -it migration_backend bash   # Backend shell
docker exec -it migration_frontend sh    # Frontend shell

# Health and monitoring
curl http://localhost:8000/api/v1/monitoring/agents  # Agent status
curl http://localhost:8000/docs                      # API documentation
```

## Testing Commands
```bash
# Backend testing
npm run test:backend:agents           # Test AI agents
npm run test:backend:integration      # Integration tests
npm run test:complete                 # Full test suite

# Frontend testing
npm run test:e2e:import              # Data import E2E test
npm run test:e2e:ui                  # UI tests with Playwright UI
npm run test:admin                   # Admin interface tests
```

## Git and Pre-commit
```bash
# Pre-commit setup
pip install pre-commit
pre-commit install

# Run pre-commit checks
pre-commit run --all-files           # All files
git commit -m "message"              # Triggers pre-commit automatically

# Git workflow with pre-commit compliance
git add .
git commit -m "feat: description"   # Pre-commit runs automatically
```

## Utility Commands
```bash
# System commands (macOS/Darwin)
/opt/homebrew/bin/gh                 # GitHub CLI
/opt/homebrew/bin/python3.11         # Python 3.11

# Docker maintenance
docker system prune                  # Clean up unused containers/images
docker volume prune                  # Clean up unused volumes
docker-compose down --volumes        # Remove containers and volumes
```
