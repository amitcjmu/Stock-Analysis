# Code Style and Conventions

## TypeScript/Frontend Conventions
- **Strict TypeScript**: No explicit `any` types allowed (`@typescript-eslint/no-explicit-any`: "error")
- **Type Imports**: Use `import type` for type-only imports to prevent circular dependencies
- **Interface over Type**: Prefer interfaces over type aliases for object shapes
- **Array Types**: Use `array-simple` syntax (e.g., `string[]` instead of `Array<string>`)
- **Return Types**: Explicit return types required on exported functions
- **Naming**: PascalCase for components, camelCase for functions and variables

## Python/Backend Conventions
- **Python Version**: Python 3.11+ required for CrewAI compatibility
- **Type Hints**: Comprehensive type annotations using modern Python typing
- **Async/Await**: Full async patterns throughout the application
- **Code Formatting**: Black for code formatting with 120 character line length
- **Linting**: Flake8 with extended ignore patterns (E203, W503)
- **Security**: Bandit for security scanning with low-low severity level

## Database Conventions
- **Schema**: Uses `migration` schema instead of `public` for better organization
- **Migrations**: Alembic migrations must be idempotent and handle existing constraints
- **Async**: AsyncPG driver for all database operations
- **Multi-tenancy**: Client account scoping in all queries

## Docker and Infrastructure
- **Container-First**: All development happens within Docker containers
- **Health Checks**: Comprehensive health monitoring for all services
- **Environment Variables**: Proper environment variable management with defaults
- **Security**: Non-root users, resource limits, and security configurations

## AI Agent Conventions
- **Agentic-First**: Use AI agents for intelligence over hard-coded rules
- **Learning Capabilities**: Implement continuous learning in all agent tools
- **Performance Tracking**: Success metrics and performance monitoring
- **Memory Patterns**: Agent memory for pattern recognition and user preferences

## File Organization
- **Frontend**: Organized by feature with shared components and utilities
- **Backend**: Clean architecture with separate layers (models, services, repositories, API)
- **Types**: Comprehensive TypeScript type definitions in organized structure
- **Tests**: Co-located with source code and comprehensive coverage

## Git and Development
- **Commits**: Follow conventional commit format
- **Pre-commit**: Comprehensive security and quality checks required
- **Branches**: Feature branches with descriptive names
- **Reviews**: Code review required for all changes
