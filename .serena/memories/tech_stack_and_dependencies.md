# Tech Stack and Dependencies

## Frontend Technology Stack
- **Framework**: Next.js with TypeScript
- **Styling**: Tailwind CSS with shadcn/ui component library
- **State Management**: React Query (@tanstack/react-query) for server state
- **Routing**: React Router DOM
- **UI Components**: Radix UI primitives with custom extensions
- **Build Tool**: Vite
- **Testing**: Vitest for unit tests, Playwright for E2E tests

## Backend Technology Stack
- **Framework**: FastAPI (Python 3.11+)
- **AI Framework**: CrewAI for multi-agent orchestration
- **Database**: PostgreSQL 16 with pgvector extension
- **ORM**: SQLAlchemy 2.0 with async support
- **Migration Tool**: Alembic
- **Authentication**: JWT with passlib and bcrypt
- **Caching**: Redis 7 with Upstash support
- **API Documentation**: Automatic OpenAPI/Swagger docs

## AI and Machine Learning
- **CrewAI**: 17 specialized agents across migration phases
- **LLM Providers**: OpenAI, DeepInfra, Anthropic
- **Vector Database**: pgvector for semantic search
- **Cost Tracking**: Comprehensive LLM usage monitoring

## Infrastructure and DevOps
- **Containerization**: Docker and Docker Compose
- **Development**: Container-first approach with volume mounting
- **Database**: PostgreSQL with health checks and data persistence
- **Caching**: Redis with security configuration and monitoring
- **Monitoring**: Health checks, logging, and performance metrics

## Key Dependencies (Frontend)
- React 18.3.1 with TypeScript
- Tailwind CSS with animations
- Radix UI component primitives
- React Hook Form with Zod validation
- Recharts for data visualization
- React Flow for dependency graphs

## Key Dependencies (Backend)
- FastAPI 0.116.1 with async support
- CrewAI 0.141.0 for AI agents
- SQLAlchemy 2.0.41 with asyncpg driver
- Alembic 1.16.3 for migrations
- Redis 5.0.1 for caching
- OpenAI 1.93.3 and Anthropic 0.57.1 for LLM integration
