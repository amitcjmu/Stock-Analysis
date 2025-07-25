# AI Modernize Migration Platform - Local Development Guide

This guide helps developers set up and run the AI Modernize Migration Platform on their local machines.

## Prerequisites

- **Python 3.11+** - Backend development
- **Node.js 18+** - Frontend development
- **PostgreSQL 14+** OR **Docker** - Database
- **Git** - Version control

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator

# Run the automated setup script
cd backend
./scripts/local_setup.sh
```

The setup script will:
- Create a `.env` file with default settings
- Start PostgreSQL (using existing installation or Docker)
- Create a Python virtual environment
- Install all dependencies
- Run database migrations
- Initialize test data and accounts
- Start the backend server

### Option 2: Docker Compose (Full Stack)

```bash
# Clone the repository
git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator

# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- Frontend: http://localhost:8081
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5433

### Option 3: Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Or create manually with content below

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup

```bash
# In a new terminal
cd migrate-ui-orchestrator

# Install dependencies
npm install

# Start frontend development server
npm run dev
```

## Environment Configuration

### Backend (.env file)

Create a `.env` file in the `backend` directory:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/migration_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=migration_db

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
FRONTEND_URL=http://localhost:8081

# AI/LLM Configuration (optional)
DEEPINFRA_API_KEY=your-api-key-here

# Feature Flags
SKIP_DB_INIT=false  # Set to true to skip automatic database initialization
```

### Frontend Configuration

The frontend uses Vite's proxy configuration to connect to the backend. This is already configured in `vite.config.ts`.

## Test Accounts

The platform automatically creates test accounts in development mode:

| Account Type | Email | Password | Description |
|-------------|-------|----------|-------------|
| Platform Admin | chocka@gmail.com | Password123! | Full platform access |
| Demo Client Admin | demo.admin@aimodernize.com | Demo123! | Client-level access |
| Demo Engagement Manager | demo.manager@aimodernize.com | Demo123! | Engagement management |
| Demo User | demo.user@aimodernize.com | Demo123! | Basic user access |

## Common Issues & Solutions

### Issue: DATABASE_URL format error

**Error**: `invalid DSN: scheme is expected to be either "postgresql" or "postgres"`

**Solution**: The start.sh script now handles this automatically by converting SQLAlchemy URLs to asyncpg format.

### Issue: Port conflicts

**Error**: `Address already in use`

**Solutions**:
- Backend: Change port in startup command: `--port 8001`
- Frontend: Change port in `vite.config.ts`
- PostgreSQL: Use port 5433 if 5432 is taken

### Issue: Missing tables error

**Error**: `relation "crewai_flow_state_extensions" does not exist`

**Solution**: Run migrations:
```bash
cd backend
alembic upgrade head
```

### Issue: Login fails with "Account not approved"

**Solution**: The database initialization should handle this automatically. If not:
```bash
cd backend
python -m app.core.database_initialization
```

## Development Workflow

1. **Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd migrate-ui-orchestrator
   npm run dev
   ```

3. **View API Documentation**:
   - Open http://localhost:8000/docs

4. **Run Tests**:
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   npm test
   ```

## Database Management

### Reset Database
```bash
cd backend
alembic downgrade base
alembic upgrade head
python -m app.core.database_initialization
```

### Create New Migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Debugging Tips

1. **Check Backend Logs**: The backend provides detailed logs of all operations
2. **API Documentation**: Use http://localhost:8000/docs to test API endpoints
3. **Database Inspection**: Use pgAdmin or DBeaver to inspect database state
4. **Environment Variables**: Ensure all required environment variables are set

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

For more information, see the main [README.md](README.md).
