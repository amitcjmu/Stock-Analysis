# Codebase Structure and Organization

## Root Directory Structure
```
migrate-ui-orchestrator/
├── backend/                 # FastAPI backend with AI agents
├── src/                    # Next.js frontend source
├── scripts/                # Development and maintenance scripts
├── tests/                  # Test files (E2E, integration)
├── docs/                   # Documentation
├── infrastructure/         # Deployment configurations
├── monitoring/             # Observability and monitoring
├── data/                   # Data files and fixtures
├── docker-compose.yml      # Main Docker configuration
├── package.json           # Frontend dependencies
└── CLAUDE.md              # Development guidelines
```

## Frontend Structure (src/)
```
src/
├── components/            # React components organized by feature
│   ├── discovery/        # Discovery phase components
│   ├── assess/           # Assessment phase components
│   ├── admin/           # Admin interface components
│   ├── collection/      # Data collection components
│   └── shared/          # Shared/common components
├── contexts/             # React contexts for state management
├── hooks/               # Custom React hooks
├── lib/                 # Utility libraries and API clients
├── pages/               # Page components (route handlers)
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
├── config/              # Configuration files
└── constants/           # Application constants
```

## Backend Structure (backend/)
```
backend/
├── app/                 # Main application code
│   ├── api/            # FastAPI route definitions
│   │   └── v1/        # API version 1 endpoints
│   ├── models/        # SQLAlchemy database models
│   ├── services/      # Business logic and AI agents
│   │   └── crewai_flows/  # CrewAI agent implementations
│   ├── repositories/ # Data access layer
│   ├── core/         # Core configurations and utilities
│   └── workers/      # Background task workers
├── alembic/           # Database migration files
├── tests/             # Backend test files
├── scripts/           # Backend-specific scripts
├── requirements.txt   # Python dependencies
└── main.py           # FastAPI application entry point
```

## AI Agent Organization
```
backend/app/services/crewai_flows/
├── crews/                    # CrewAI crew definitions
├── handlers/                # Phase-specific handlers
├── unified_discovery_flow/  # Discovery flow orchestration
├── assessment_flow/         # Assessment flow (planned)
└── agents/                  # Individual agent implementations
```

## Type System Organization
```
src/types/
├── api/                     # API response/request types
├── components/             # Component prop types
├── hooks/                  # Hook parameter/return types
├── modules/               # Module-specific types
└── shared/                # Shared type definitions
```

## Key Configuration Files
- `docker-compose.yml` - Main development environment
- `package.json` - Frontend dependencies and scripts
- `backend/requirements.txt` - Python dependencies
- `tsconfig.json` - TypeScript configuration
- `eslint.config.js` - ESLint rules and configuration
- `.pre-commit-config.yaml` - Code quality and security checks
- `alembic.ini` - Database migration configuration

## Database Schema Organization
- Uses `migration` schema instead of `public`
- Multi-tenant architecture with client account scoping
- Vector support through pgvector extension
- Comprehensive foreign key relationships

## Development Workflow Directories
- `scripts/` - Automation and maintenance scripts
- `tests/` - E2E and integration test files
- `docs/` - Project documentation
- `monitoring/` - Observability configurations
- `infrastructure/` - Deployment and infrastructure code

## Container Organization
- `migration_frontend` - Next.js development server
- `migration_backend` - FastAPI with AI agents
- `migration_db` - PostgreSQL with pgvector
- `migration_redis` - Redis for caching and queuing
- `migration_assessment_worker` - Background task processing
