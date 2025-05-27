# AI Force Migration Platform - Technical Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [AI Learning System](#ai-learning-system)
8. [Database Design](#database-design)
9. [API Design](#api-design)
10. [Development Workflow](#development-workflow)
11. [Testing Strategy](#testing-strategy)
12. [Deployment & DevOps](#deployment--devops)

## Overview

The AI Force Migration Platform is a comprehensive cloud migration orchestration system that leverages AI agents to automate and optimize the entire migration lifecycle. The platform is built with a modern microservices architecture using FastAPI for the backend and Next.js for the frontend, with CrewAI providing the AI agent framework.

### Key Features
- **AI-Powered Analysis**: CrewAI agents analyze CMDB data and provide migration recommendations
- **Dynamic Field Mapping**: AI learns field mappings from user feedback and data patterns
- **Real-time Monitoring**: WebSocket-based agent monitoring and task tracking
- **6R Strategy Analysis**: Automated recommendations for Rehost, Replatform, Refactor, etc.
- **Wave Planning**: Intelligent migration sequencing based on dependencies
- **Risk Assessment**: Comprehensive risk analysis with mitigation strategies

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           AI Force Migration Platform                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │
│  │   Frontend      │    │    Backend      │    │   Data Layer    │               │
│  │   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │               │
│  │                 │    │                 │    │                 │               │
│  │ • TypeScript    │    │ • Python 3.11+  │    │ • Data Storage  │               │
│  │ • Tailwind CSS  │    │ • CrewAI        │    │ • Persistence   │               │
│  │ • React         │    │ • WebSocket     │    │ • Migrations    │               │
│  │ • shadcn/ui     │    │ • SQLAlchemy    │    │                 │               │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘               │
│                                 │                                                │
│                                 ▼                                                │
│                    ┌────────────────────────────────────┐                        │
│                    │         AI Agent Layer             │                        │
│                    │         (CrewAI)                   │                        │
│                    │                                    │                        │
│                    │ • CMDB Analyst Agent               │                        │
│                    │ • Learning Specialist Agent        │                        │
│                    │ • Pattern Recognition Agent        │                        │
│                    │ • Migration Strategy Agent         │                        │
│                    │ • Risk Assessment Agent            │                        │
│                    │ • Wave Planning Agent              │                        │
│                    └────────────────────────────────────┘                        │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Technologies
- **Python 3.11+**: Core language with async/await support
- **FastAPI**: Modern, fast web framework for building APIs
- **CrewAI 0.121.0**: AI agent framework for multi-agent collaboration
- **SQLAlchemy**: ORM with async support for database operations
- **PostgreSQL**: Primary database for data persistence
- **Pydantic**: Data validation and serialization
- **WebSockets**: Real-time communication for agent monitoring
- **DeepInfra**: LLM provider for AI agent intelligence

### Frontend Technologies
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern component library
- **React Hooks**: State management and lifecycle
- **WebSocket Client**: Real-time updates from backend

### Development & DevOps
- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container orchestration
- **Git**: Version control with feature branch workflow
- **ESLint**: JavaScript/TypeScript linting
- **Pytest**: Python testing framework
- **Railway**: Cloud deployment platform

## Project Structure

```
migrate-ui-orchestrator/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   └── v1/
│   │   │       └── endpoints/ # Route handlers
│   │   ├── core/              # Core configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   └── tools/         # AI agent tools
│   │   └── websocket/         # WebSocket handlers
│   ├── data/                  # Data files and exports
│   ├── venv/                  # Python virtual environment
│   └── requirements.txt       # Python dependencies
├── src/                       # Next.js frontend
│   ├── components/            # React components
│   │   ├── discovery/         # Discovery phase components
│   │   └── ui/                # Shared UI components
│   ├── config/                # Configuration files
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility libraries
│   └── pages/                 # Next.js pages
│       ├── assess/            # Assessment phase
│       ├── discovery/         # Discovery phase
│       ├── execute/           # Execution phase
│       ├── finops/            # FinOps phase
│       ├── modernize/         # Modernization phase
│       └── plan/              # Planning phase
├── tests/                     # Test suites
│   ├── backend/               # Python tests
│   └── frontend/              # JavaScript tests
├── docs/                      # Documentation
├── docker-compose.yml         # Docker orchestration
├── Dockerfile                 # Container definition
└── package.json               # Node.js dependencies
``` 