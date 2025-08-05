# Development Guidelines and Best Practices

## Core Development Principles

### Container-First Development
- **All development happens in Docker containers** - never run services locally
- Use `docker exec` for debugging and interaction with services
- Test changes within the container environment before committing
- Health monitoring through container health checks

### Agentic-First Approach
- **Use AI agents for intelligence** over hard-coded rules
- Implement learning capabilities in all agent tools
- Track agent performance with success metrics
- Use agent memory for pattern recognition and user preferences

### Multi-Tenant Architecture
- **Client account scoping** for all data access
- Context-aware repositories for data isolation
- Engagement-level data management with proper isolation
- Admin interfaces for tenant management

## Code Modification Guidelines (from CLAUDE.md)

### Git History and Code Review
- Always thoroughly review project Git history before making changes
- Understand existing codebase support for areas you're modifying
- Validate approach consistency with past implementation patterns
- **Prioritize modifying existing code over adding new code** to prevent sprawl
- Assess if existing code can be refactored/extended before creating new implementations

### Pre-commit Compliance
- **Never bypass pre-commit checks with --no-verify** unless you've run them at least once
- Fix all issues mentioned by pre-commit checks
- Security checks, linting, and formatting must pass

### Platform-Specific Tools
- Use `/opt/homebrew/bin/gh` for all Git CLI tools
- Use `/opt/homebrew/bin/python3.11` for all Python executions

## AI Agent Development Standards

### Learning and Intelligence
- **Always use agentic intelligence** over hard-coded rules
- Implement continuous learning in all agent tools
- Track agent performance with comprehensive success metrics
- Use agent memory for pattern recognition across sessions

### Cross-Page Communication
- Implement agent state persistence across workflow pages
- Real-time synchronization between agents with health monitoring
- Pattern sharing and experience coordination across all agents
- Modular handler-based design with <200 lines per handler

### Multi-Tenant Agent Design
- Client context isolation with secure learning separation
- Session-aware intelligence with smart deduplication
- RBAC integration with role-based access control
- Context-aware analytics scoped to client and engagement

## LLM Cost Management

### Cost Optimization
- Track all AI model usage through multi-model service
- Implement cost-effective model selection (75% reduction achieved)
- Monitor usage with real-time dashboards and analytics
- Use intelligent model routing for routine vs. complex tasks

### Provider Management
- Support multiple providers: OpenAI, DeepInfra, Anthropic
- Provider comparison and performance metrics
- Feature-level cost breakdown and attribution
- Budget management with alerts and threshold monitoring

## Security and Quality Standards

### Security Requirements
- Comprehensive security scanning with Bandit and ESLint security plugins
- No hardcoded credentials or sensitive data in code
- Regular dependency audits and vulnerability scanning
- Cache security validation and Redis configuration auditing

### Code Quality Standards
- Zero tolerance for explicit `any` types in TypeScript
- Comprehensive type annotations in Python
- Consistent formatting with Black (Python) and Prettier (TypeScript)
- Pre-commit hooks for automated quality assurance

## Testing Standards

### Test Categories
- **Unit Tests**: Vitest for frontend, pytest for backend
- **Integration Tests**: Cross-service functionality testing
- **E2E Tests**: Playwright for complete user journey testing
- **Agent Tests**: Specific testing for AI agent functionality

### Testing Requirements
- All new features must include comprehensive tests
- Agent functionality requires specific agent testing
- Integration changes require full integration test suite
- UI changes require E2E test validation

## Performance Guidelines

### Agent Performance
- Optimize all 17 agents for better response times
- Real-time monitoring of agent health and performance
- Context sharing with 98% sync rate and <50ms response time
- Performance analytics with accuracy metrics and trends

### System Performance
- Async/await patterns throughout the application
- Efficient database queries with proper indexing
- WebSocket integration for real-time updates
- Resource limits and monitoring for container services

## Documentation Standards

### Required Documentation
- API changes require OpenAPI/Swagger documentation updates
- New agent implementations require behavior documentation
- Database schema changes require migration documentation
- Security changes require security impact documentation

### Code Documentation
- TypeScript interfaces and types must be well-documented
- Python functions require comprehensive docstrings
- Agent behavior and learning patterns must be documented
- Complex business logic requires inline comments
