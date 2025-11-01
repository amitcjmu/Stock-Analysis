# 🎉 Welcome to the AI Modernize Migration Platform!

## 👋 A Warm Welcome, New Developer!

Welcome to our cutting-edge AI-powered migration platform! We're excited to have you join our team. This guide will get you from zero to productive in 30 minutes, and fully onboarded within your first day.

**Platform Overview**: The AI Modernize Migration Platform is an enterprise-grade cloud migration orchestration system powered by 17 CrewAI agents that automate the entire migration lifecycle from discovery to decommission.

---

## 🚀 Quick Start in 30 Minutes

### ⚡ Prerequisites (5 minutes)
- **Docker Desktop** (Required - all development happens in containers)
- **Git** for repository management  
- **8GB RAM minimum** for optimal Docker performance

### 🏁 Get Running Fast (10 minutes)
```bash
# 1. Clone and enter the project
git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator

# 2. Start all services (this will take a few minutes first time)
docker-compose up -d --build

# 3. Verify everything is working
curl http://localhost:8000/health     # Backend health check
curl http://localhost:8081           # Frontend check (NOT port 3000)

# 4. Access the platform
# Frontend: http://localhost:8081 (IMPORTANT: NOT 3000)
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 🎯 Test Your Setup (15 minutes)
1. **Open the frontend**: Navigate to http://localhost:8081 (NOT port 3000)
2. **Login credentials**: Contact your team lead or check the team onboarding documentation for current authentication setup
3. **Create a test discovery flow**: Upload a sample CSV file
4. **Watch the AI agents work**: See real-time processing and field mapping
5. **Explore the admin dashboard**: Check LLM cost tracking and agent monitoring

**🎉 Congratulations!** If everything above worked, you're ready to start developing!

---

## 📊 Observability Stack Setup (Optional - 15 minutes)

The platform includes an enterprise-grade observability stack powered by Grafana for monitoring logs, traces, and metrics. This is **optional** for development but **highly recommended** for debugging and understanding system behavior.

### 🎯 What's Included in Observability

When enabled, you get **5 additional containers**:
1. **Grafana** (port 9999): Dashboards and visualizations
2. **Loki** (port 3100): Log aggregation and storage (14-day retention)
3. **Tempo** (port 3200): Distributed tracing (7-day retention)
4. **Prometheus** (port 9090): Metrics time-series database (14-day retention)
5. **Alloy** (ports 12345, 4317, 4318): Unified telemetry collector (replaces deprecated Promtail)

**Pre-built Dashboards**:
- 📋 **Application Logs - Enhanced**: 8 specialized panels for CrewAI monitoring
- 🏥 **Agent Health Dashboard**: Agent performance and memory usage
- 💰 **LLM Costs Dashboard**: Token usage and cost tracking
- 🔄 **Master Flow Orchestrator**: Flow lifecycle and state tracking

### ✅ Option 1: Enable Observability (Recommended)

```bash
# 1. Create observability environment file
cd config/docker
cp .env.observability.template .env.observability

# 2. Edit .env.observability and set required passwords
# GRAFANA_ADMIN_PASSWORD=<your-secure-password>
# POSTGRES_GRAFANA_PASSWORD=<your-postgres-password>

# 3. Start all services INCLUDING observability (9 total containers)
docker-compose up -d
docker-compose -f docker-compose.observability.yml up -d

# 4. Verify observability stack is running
docker ps | grep migration_

# You should see: backend, frontend, postgres, redis (core) + grafana, loki, tempo, prometheus, alloy (observability)
```

**Access Grafana**:
- URL: http://localhost:9999
- Login: `admin` / `<your-GRAFANA_ADMIN_PASSWORD>`
- Navigate to: Dashboards → Observability

**Verify Log Collection**:
```bash
# Check Alloy is collecting logs
curl http://localhost:12345/-/ready
# Should return: "Alloy is ready."

# Check Loki has logs
curl -G http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={container="migration_backend"}' \
  --data-urlencode 'limit=5'
```

### ❌ Option 2: Run Without Observability (Lightweight)

If you prefer a minimal setup without monitoring (saves ~2GB RAM):

```bash
# Start ONLY the core 4 containers
docker-compose up -d

# Core containers:
# - migration_backend (FastAPI + CrewAI)
# - migration_frontend (Next.js)
# - migration_postgres (PostgreSQL 16 + pgvector)
# - migration_redis (Redis 7)
```

**When to skip observability**:
- You're on a resource-constrained machine (<8GB RAM)
- You're doing quick feature testing
- You don't need log/trace/metric analysis

**Re-enable later anytime**:
```bash
cd config/docker
docker-compose -f docker-compose.observability.yml up -d
```

### 🛑 Stop Observability Stack

To stop observability while keeping core services running:

```bash
cd config/docker
docker-compose -f docker-compose.observability.yml down
```

To stop EVERYTHING (core + observability):

```bash
docker-compose down
docker-compose -f docker-compose.observability.yml down
```

**Note**: Stopping containers preserves data in mounted volumes. To delete all data:
```bash
docker-compose down -v  # Deletes core volumes
docker-compose -f docker-compose.observability.yml down -v  # Deletes observability volumes
```

### 🔍 Using Observability for Development

**Debugging with Logs**:
1. Open Grafana: http://localhost:9999
2. Go to: Dashboards → Observability → Application Logs - Enhanced
3. Use panels:
   - **Error & Exception Logs**: See full error stack traces with context
   - **Flow Phase Transitions**: Track flow progress through phases
   - **CrewAI Agent Decisions**: Watch agent decision-making in real-time
   - **Log Levels**: Overview of INFO/WARNING/ERROR distribution

**Finding Issues**:
- Use the `$search` filter at the top to narrow results
- Click any log entry to expand and see full JSON details
- Adjust time range (default: Last 6 hours) for historical analysis
- Use "Log Rate by Container" to spot unusual activity spikes

**Monitoring LLM Costs**:
1. Navigate to: Dashboards → Observability → LLM Costs Dashboard
2. See real-time usage by model (Gemma 3, Llama 4)
3. Track token consumption and cost per engagement
4. Identify expensive CrewAI operations

**Performance Troubleshooting**:
- **Agent Health Dashboard**: Memory usage, execution times, success rates
- **Master Flow Orchestrator**: Flow bottlenecks and state transitions
- **Prometheus**: Query backend metrics at http://localhost:9090

### 📚 Observability Documentation

For detailed setup, architecture, and troubleshooting:
- **Setup Guide**: `/tmp/observability-stack-setup-guide.md` (generated during setup)
- **Migration Summary**: `.serena/memories/promtail-to-alloy-migration-oct-2025.md`
- **Alloy Docs**: https://grafana.com/docs/alloy/latest/
- **Loki Query Syntax**: https://grafana.com/docs/loki/latest/logql/

### ⚠️ Important: Secrets Management

**NEVER commit** `.env.observability` to Git:
- ✅ `.env.observability.template` is tracked (template for reference)
- ❌ `.env.observability` is gitignored (contains your passwords)
- ✅ Pattern `*.observability` ensures all variants are excluded

**Why Grafana Alloy?**
- Promtail (previous solution) reached End-of-Life: March 2, 2026
- Alloy is the strategic replacement with:
  - Unified logs + traces + metrics collection
  - Full OTLP (OpenTelemetry Protocol) support
  - Active development and long-term support
  - Better performance than separate agents

---

## 📖 Documentation Learning Path

### 🏛️ Foundation Architecture (Read First - 45 minutes)

#### **Critical Must-Reads**
📋 **[docs/analysis/Notes/000-lessons.md](./analysis/Notes/000-lessons.md)** ⭐ **START HERE**
- **Why**: Contains ALL critical learnings that prevent common pitfalls
- **Time**: 15 minutes
- **Key Takeaways**: Docker-first development, agentic-first principles, multi-tenant patterns

📐 **[docs/adr/README.md](./adr/README.md)** 
- **Why**: Understand architectural decisions and their reasoning
- **Time**: 10 minutes  
- **Key Takeaways**: Decision context, reading order for ADRs

🏗️ **[docs/TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md)**
- **Why**: Complete system overview and component relationships
- **Time**: 20 minutes
- **Key Takeaways**: CrewAI integration, multi-tenant architecture, flow-based patterns

#### **Platform Overview**
📊 **[docs/PLATFORM_COMPREHENSIVE_SUMMARY.md](./PLATFORM_COMPREHENSIVE_SUMMARY.md)**
- **Why**: Complete platform status and capabilities overview
- **Time**: 15 minutes
- **Key Takeaways**: 17 AI agents, current implementation status, recent fixes

🚀 **[README.md](../README.md)**
- **Why**: Project overview, features, and current roadmap
- **Time**: 10 minutes
- **Key Takeaways**: Feature overview, sprint plans, success metrics

### 🛠️ Development Guidelines (Essential - 30 minutes)

🔧 **[docs/DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** ⭐ **ESSENTIAL**
- **Why**: Complete development standards and workflows
- **Time**: 30 minutes
- **Key Takeaways**: Code organization, testing patterns, Docker workflows

📏 **[docs/architecture/ARCHITECTURAL_REVIEW_GUIDELINES.md](./architecture/ARCHITECTURAL_REVIEW_GUIDELINES.md)**
- **Why**: How to evaluate and improve the codebase properly
- **Time**: 15 minutes
- **Key Takeaways**: What to respect vs. what to change, common mistakes to avoid

### 👤 User Experience Understanding (20 minutes)

📖 **[docs/user_guide/discovery_flow.md](./user_guide/discovery_flow.md)**
- **Why**: Understand how users interact with the platform
- **Time**: 15 minutes
- **Key Takeaways**: Automated workflows, multi-phase processing, user interaction patterns

### 🚨 Troubleshooting & Operations (Reference - 25 minutes)

🔍 **[docs/troubleshooting/phase1-common-issues.md](./troubleshooting/phase1-common-issues.md)**
- **Why**: Quick diagnosis and solutions for common problems
- **Time**: 15 minutes
- **Use**: When something breaks or behaves unexpectedly

🚀 **[docs/DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**
- **Why**: Understanding deployment processes and rollback procedures
- **Time**: 10 minutes
- **Use**: For production deployments and emergency procedures

---

## 🎭 Role-Based Learning Paths

### 🎨 Frontend Developer Path (45 minutes total)

#### **Start Here**
1. **[docs/FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)** (10 min)
   - Component architecture and state management
2. **[docs/DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Frontend sections (15 min)
   - React patterns, TypeScript standards, component testing
3. **[src/components/README.md](../src/components/README.md)** if exists (5 min)
   - Component library patterns

#### **Deep Dive**
4. **[docs/development/modularization/](./development/modularization/)** (15 min)
   - TypeScript module boundaries, lazy loading patterns

### ⚙️ Backend Developer Path (90 minutes total)

#### **Start Here** 
1. **[docs/BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)** (10 min)
   - Service architecture and patterns
2. **[docs/DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Backend sections (20 min)
   - FastAPI patterns, async development, database patterns
3. **[docs/CREWAI.md](./CREWAI.md)** (15 min)
   - AI agent development patterns

#### **Database & Data Layer** ⭐ **ENHANCED**
4. **[docs/architecture/database-design.md](./architecture/database-design.md)** (15 min)
   - Complete database schema and multi-tenant architecture
5. **[docs/implementation/postgresql-development-guide.md](./implementation/postgresql-development-guide.md)** (20 min)
   - **Database schema visualization with Mermaid diagrams**
   - **Local PostgreSQL connection setup (Docker)**
   - **SQLAlchemy ORM patterns and best practices**
   - **Repository pattern implementation**
   - **Query optimization and performance**

#### **Redis & Caching** ⭐ **NEW**
6. **[docs/implementation/redis-development-guide.md](./implementation/redis-development-guide.md)** (15 min)
   - **Redis key naming conventions and patterns**
   - **Local Redis setup and CLI commands**
   - **Caching strategies and TTL management**
   - **Event bus and pub/sub patterns**
   - **How to inspect Redis keys during development**

#### **Deep Dive**
7. **[docs/development/master_flow_orchestrator/](./development/master_flow_orchestrator/)** (15 min)
   - Flow orchestration patterns
8. **[docs/adr/025-collection-flow-child-service-migration.md](./adr/025-collection-flow-child-service-migration.md)** (10 min) ⭐ **OCTOBER 2025**
   - Child flow service pattern (replaces crew_class)
   - Single execution path architecture
   - How to implement new flow types

### 🗄️ Database/DevOps Developer Path (45 minutes total)

#### **Start Here**
1. **[docs/db/DATABASE_ARCHITECTURE_DECISIONS.md](./db/DATABASE_ARCHITECTURE_DECISIONS.md)** (15 min)
   - Database design patterns and multi-tenancy
2. **[docs/deployment/](./deployment/)** folder (20 min)
   - Deployment strategies and Docker configuration
3. **[docs/troubleshooting/](./troubleshooting/)** folder (10 min)
   - Common operational issues

### 🤖 AI/Agent Developer Path (75 minutes total)

#### **Start Here**
1. **[docs/CREWAI.md](./CREWAI.md)** (20 min)
   - CrewAI framework integration
2. **[docs/AI_LEARNING_SYSTEM.md](./AI_LEARNING_SYSTEM.md)** (20 min)
   - Learning system architecture
3. **[docs/agents/](./agents/)** folder (20 min)
   - Agent specifications and patterns

#### **Deep Dive**
4. **[docs/development/agentic-memory-architecture/](./development/agentic-memory-architecture/)** (15 min)
   - Memory and learning patterns
5. **[docs/adr/024-tenant-memory-manager-architecture.md](./adr/024-tenant-memory-manager-architecture.md)** (15 min) ⭐ **OCTOBER 2025**
   - Why CrewAI memory is disabled (memory=False)
   - How TenantMemoryManager provides enterprise agent learning
   - Multi-tenant memory isolation patterns

### 🧪 QA/Testing Developer Path (40 minutes total)

#### **Start Here**
1. **[docs/testing/README.md](./testing/README.md)** (10 min)
   - Testing strategy overview
2. **[docs/DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Testing sections (15 min)
   - Testing patterns and frameworks
3. **[docs/testing/](./testing/)** folder (15 min)
   - Specific testing documentation

---

## 📁 Document Categories

### 📚 Reference Materials (Use When Needed)

#### **APIs & Integration**
- **[docs/api/](./api/)** - API documentation and migration guides
- **[docs/API_V3_DOCUMENTATION.md](./API_V3_DOCUMENTATION.md)** - Complete API reference

#### **Database & Schema**
- **[docs/db/](./db/)** - Database design, migrations, and architecture
- **[docs/DATABASE_SETUP_AUTOMATION.md](./DATABASE_SETUP_AUTOMATION.md)** - Database initialization

#### **Deployment & Operations**
- **[docs/deployment/](./deployment/)** - Deployment guides and configurations
- **[docs/security/](./security/)** - Security guidelines and assessments

#### **Feature-Specific Docs**
- **[docs/features/](./features/)** - Individual feature documentation
- **[docs/planning/](./planning/)** - Feature planning and requirements

### 📋 Process Documentation

#### **Development Process**
- **[docs/development/](./development/)** - Development workflows and standards
- **[docs/implementation/](./implementation/)** - Implementation guides and summaries

#### **Quality Assurance**  
- **[docs/testing/](./testing/)** - Testing strategies and reports
- **[docs/technical-debt/](./technical-debt/)** - Technical debt tracking

### 📜 Historical Context

#### **Archive (Browse When Curious)**
- **[docs/archive/](./archive/)** - Historical decisions and deprecated features
- **[docs/cleanup/](./cleanup/)** - Code cleanup and refactoring notes

---

## 🚨 Critical "Don't Break These" Rules

### ❌ Never Do These Things
1. **Never develop locally** - Always use Docker containers
2. **Never implement hard-coded logic** - Use AI agents for all intelligence
3. **Never skip multi-tenant context** - All data must be client-scoped
4. **Never mix sync/async patterns** - Use `AsyncSessionLocal` in async contexts
5. **Never bypass pre-commit checks** - Run them at least once
6. **Never enable CrewAI memory** - Always set `memory=False` (ADR-024, October 2025)
7. **Never use crew_class parameter** - Always use `child_flow_service` pattern (ADR-025, October 2025)
8. **Never make direct LLM calls** - Always use `multi_model_service.generate_response()` for tracking
9. **Never use camelCase in new code** - Always use snake_case (migration completed August 2025)

### ✅ Always Do These Things
1. **Always use Docker for everything** - `docker exec` for all debugging
2. **Always implement learning in agents** - No static business logic
3. **Always include context headers** - `X-Client-Account-ID`, `X-Engagement-ID`
4. **Always update CHANGELOG.md** - After every task completion
5. **Always test in containers** - Never trust local testing
6. **Always use TenantMemoryManager** - For all agent learning and pattern storage (ADR-024, October 2025)
7. **Always use child_flow_service pattern** - When implementing new flow types (ADR-025, October 2025)
8. **Always use multi_model_service** - For automatic LLM usage tracking and cost monitoring (October 2025)
9. **Always use snake_case** - For all new API fields and TypeScript interfaces (August 2025)

### 🔧 Development Patterns

#### **Docker-First Development**
```bash
# ✅ Correct way - everything in containers
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_frontend npm run build
docker exec -it migration_db psql -U user -d migration_db

# ❌ Wrong way - local development
python main.py
npm run dev  # NEVER use this - would run on port 3000 incorrectly
```

#### **Agentic-First Programming**
```python
# ✅ Correct - use AI agents
async def analyze_data(data):
    result = await crewai_service.analyze_with_agents(data)
    return result

# ❌ Wrong - hard-coded logic
def analyze_data(data):
    if data["type"] == "server":
        return "Rehost"
    elif data["type"] == "application":
        return "Refactor"
```

---

## 🎯 Common Pitfalls for New Developers

### 🐛 Top 5 Mistakes New Developers Make

1. **Trying to run services locally**
   - **Why it fails**: Platform is designed for Docker-only development
   - **Solution**: Use `docker exec` for everything

2. **Implementing business logic instead of using agents**
   - **Why it fails**: Platform is agentic-first - all intelligence comes from AI
   - **Solution**: Always delegate to CrewAI agents

3. **Forgetting multi-tenant context**
   - **Why it fails**: Data leakage between clients
   - **Solution**: Always include client and engagement headers

4. **Mixing sync and async database operations**
   - **Why it fails**: Database deadlocks and connection issues
   - **Solution**: Use `AsyncSessionLocal` exclusively in async contexts

5. **Not reading the lessons learned document**
   - **Why it fails**: Repeating solved problems
   - **Solution**: **[docs/analysis/Notes/000-lessons.md](./analysis/Notes/000-lessons.md)** is mandatory reading

### 🔍 Quick Debugging Guide

#### **Something Not Working?**
1. **Check container health**: `docker-compose ps`
2. **View logs**: `docker-compose logs -f backend frontend`
3. **Test connectivity**: `curl http://localhost:8000/health`
4. **Check the troubleshooting guide**: [docs/troubleshooting/phase1-common-issues.md](./troubleshooting/phase1-common-issues.md)

#### **Build Failing?**
1. **Clean rebuild**: `docker-compose down && docker-compose up --build`
2. **Check for syntax errors**: Look for TypeScript/Python syntax issues
3. **Verify imports**: Ensure all modules are properly imported
4. **Check port conflicts**: Ensure nothing is running on port 8081 locally
5. **Read recent commits**: Check what changed recently

---

## 🏆 Your First Week Goals

### 📅 Day 1: Setup & Understanding
- [ ] Complete 30-minute quick start
- [ ] Read all "Must-Read" documents (3-4 hours total)
- [ ] Successfully upload test data and see agents process it
- [ ] Join team Slack and introduce yourself

### 📅 Day 2-3: Deep Dive Your Role
- [ ] Complete your role-specific learning path
- [ ] Explore the codebase using your preferred IDE
- [ ] Make a small test change and verify it works
- [ ] Ask questions in team channels

### 📅 Day 4-5: First Contribution
- [ ] Pick up a "good first issue" from the project board
- [ ] Implement the change following development guidelines
- [ ] Submit your first pull request
- [ ] Get code review feedback and iterate

### 📅 Week 1 Wrap-up
- [ ] Attend team standup and demo meetings
- [ ] Complete onboarding feedback survey
- [ ] Plan your Week 2 learning goals
- [ ] Celebrate your first week! 🎉

---

## 🤝 Team Communication

### 📞 Getting Help
- **Github Discussions**: https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/discussions (for team members)
- **GitHub Issues**: For bugs and feature requests
- **Direct Messages**: Your assigned buddy/mentor
- **Team Meetings**: Daily standups and weekly demos

### 💬 Communication Best Practices
- **Ask questions early and often** - we're here to help!
- **Document what you learn** - contribute back to this guide
- **Share your screen** when asking for help
- **Use @here sparingly** in Slack channels

### 📋 GitHub Project Management ⭐ **REQUIRED**
**All development activities must be tracked in our GitHub Projects board.**

📊 **Main Project Board**: [https://github.com/users/CryptoYogiLLC/projects/2/views/3](https://github.com/users/CryptoYogiLLC/projects/2/views/3)

#### Essential Project Management Rules:
- **All work must be tracked** as either an issue or sub-issue
- **Assign yourself** when starting work (move to "In Progress")
- **Update status** as you progress through development
- **Link PRs to issues** using "Closes #123" in PR descriptions
- **Break down large tasks** into smaller sub-issues

#### Quick Start with GitHub Projects:
1. **Browse the board** to understand current work
2. **Pick up Ready issues** that match your skills
3. **Create issues** for new bugs or features you discover
4. **Use proper labels** (frontend, backend, bug, enhancement)
5. **Reference issues** in all commits and PRs

📚 **Complete Guide**: [docs/workflow/github-project-management.md](./workflow/github-project-management.md)

### 📝 Development Process
1. **Pick up issues** from the [GitHub Projects Board](https://github.com/users/CryptoYogiLLC/projects/2/views/3)
2. **Create feature branches** following naming conventions (`type/issue-number-description`)
3. **Test thoroughly** in Docker containers
4. **Submit pull requests** with clear descriptions and issue links
5. **Participate in code reviews** - both giving and receiving feedback

---

## 🎓 Advanced Learning Resources

### 📖 Deep Technical Topics (After Week 1)

#### **AI Agent Development**
- **[docs/development/agentic-memory-architecture/](./development/agentic-memory-architecture/)** - Memory system design
- **[docs/agents/crew_specifications.md](./agents/crew_specifications.md)** - Crew implementation patterns
- **[docs/planning/agent-tool-service-registry/](./planning/agent-tool-service-registry/)** - Service registry patterns

#### **Advanced Architecture**
- **[docs/adr/](./adr/)** - All architectural decision records
- **[docs/planning/architecture/](./planning/architecture/)** - Future architecture planning
- **[docs/development/master_flow_orchestrator/](./development/master_flow_orchestrator/)** - Flow orchestration deep dive

#### **Performance & Optimization**
- **[docs/development/CREWAI_PERFORMANCE_OPTIMIZATION_PLAN.md](./development/CREWAI_PERFORMANCE_OPTIMIZATION_PLAN.md)** - Performance optimization
- **[docs/backend/DATABASE_TIMEOUT_CONFIGURATION.md](./backend/DATABASE_TIMEOUT_CONFIGURATION.md)** - Database optimization

### 🌟 Become a Platform Expert

#### **Specialization Tracks** (Choose after Week 2)
1. **AI Agent Specialist**: Focus on CrewAI development and learning systems
2. **Multi-Tenant Expert**: Deep dive into enterprise architecture patterns  
3. **Performance Engineer**: Optimize platform performance and scalability
4. **DevOps Specialist**: Focus on deployment, monitoring, and operations
5. **Frontend Architect**: Lead UI/UX and component architecture

---

## ✨ Welcome to the Team!

You're joining a cutting-edge project that's pushing the boundaries of AI-powered enterprise software. Our platform showcases:

- **17 AI Agents** working together across all migration phases
- **95%+ accuracy** in field mapping through continuous learning
- **Enterprise-grade** multi-tenant architecture with security
- **Docker-first** development with comprehensive health monitoring
- **Real-time** collaboration between AI agents and human users

We're excited to see what you'll build with us! Remember:

🚀 **Start small, learn fast, contribute meaningfully**

📚 **When in doubt, read the docs (especially the lessons learned)**

🤖 **Think "agent-first" for all intelligence and automation**

🐳 **Everything happens in Docker - embrace the container lifestyle**

💪 **You've got this, and we've got your back!**

---

**Happy coding, and welcome to the AI Modernize Migration Platform team! 🎉**

*This guide is a living document. Please contribute improvements as you learn!*