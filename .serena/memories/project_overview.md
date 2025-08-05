# AI Modernize Migration Platform - Project Overview

## Purpose
The AI Modernize Migration Platform is a comprehensive cloud migration management application designed to orchestrate the entire cloud migration journey from discovery to decommission. It's powered by AI-driven automation with CrewAI agents to streamline complex migration processes through intelligent insights, automated workflows, and continuous learning.

## Key Features
- **17 AI Agents**: Comprehensive CrewAI agent ecosystem (13 active, 4 planned) across all migration phases
- **Multi-Tenant Architecture**: Complete client/engagement/session isolation with RBAC
- **AI Learning Systems**: 95%+ field mapping accuracy with organizational adaptation
- **LLM Cost Management**: Complete cost tracking dashboard with 7 admin endpoints
- **Cross-Page Intelligence**: Seamless agent coordination with real-time synchronization
- **Container-First Development**: 100% containerized workflow with health monitoring

## Migration Phases
1. **Discovery Phase** (4 active agents): Asset inventory, dependency mapping, tech debt analysis
2. **Assessment Phase** (2 active agents): 6R treatment analysis, risk assessment
3. **Planning Phase** (1 active agent): Wave planning and coordination
4. **Execution Phase** (1 planned): Migration execution coordination
5. **Modernization Phase** (1 planned): Containerization and refactoring
6. **Decommission Phase** (1 planned): Safe asset retirement
7. **FinOps Phase** (1 planned): Cost optimization

## Technical Architecture
- **Frontend**: Next.js with TypeScript, Tailwind CSS, and shadcn/ui components
- **Backend**: FastAPI with Python 3.11+, CrewAI framework for AI agents
- **Database**: PostgreSQL with pgvector for vector operations
- **Infrastructure**: Docker containers with Redis for caching and task queuing

## Development Environment
- All development happens within Docker containers
- Port mappings: Frontend (8081), Backend (8000), Database (5433), Redis (6379)
- Health monitoring and real-time updates via WebSocket integration
