# AI Modernize Migration Platform Overview

## Project Purpose
The AI Modernize Migration Platform is a comprehensive cloud migration management application designed to orchestrate the entire cloud migration journey from discovery to decommission. It's powered by AI-driven automation with CrewAI agents and features 17 operational AI agents across all migration phases.

## Tech Stack
- **Frontend**: Next.js with TypeScript, Tailwind CSS, React Router DOM
- **Backend**: FastAPI with Python, CrewAI agents
- **Database**: PostgreSQL with async support, multi-tenancy
- **Infrastructure**: Docker-first architecture - all development happens in containers
- **UI Components**: Radix UI components with shadcn/ui, Lucide icons
- **State Management**: React Context API with custom hooks
- **API Layer**: Axios with custom API service layer

## Architecture
- **Container Services**:
  - Frontend: `migration_frontend` - Next.js application
  - Backend: `migration_backend` - FastAPI with 17 CrewAI agents
  - Database: `migration_postgres` - PostgreSQL with async support
  - Cache: `migration_redis` - Redis cache
- **Development Workflow**: All development happens within Docker containers
- **Multi-tenant Architecture**: Client/engagement/session isolation with RBAC

## Key Features
- **17 AI Agents**: Across Discovery (4), Assessment (2), Planning (1), Learning (3), Observability (3), and more planned
- **AI Learning System**: Continuous learning with 95%+ field mapping accuracy
- **LLM Cost Management**: Real-time tracking across all AI usage
- **Multi-tenant Intelligence**: Client context isolation and learning
- **Real-time Features**: WebSocket integration, live agent monitoring
