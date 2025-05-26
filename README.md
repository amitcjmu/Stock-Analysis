# AI Force Migration Platform

## Overview

The **AI Force Migration Platform** is a comprehensive cloud migration management application designed to orchestrate the entire cloud migration journey from discovery to decommission. Powered by AI-driven automation, this platform streamlines complex migration processes through intelligent insights and automated workflows.

Built with a modern tech stack featuring a **Next.js frontend** and **FastAPI backend**, the platform integrates with **CrewAI** for advanced agentic AI capabilities. The application is currently in MVP stage with placeholder logic, preparing for **CloudBridge integration** expected in September 2025.

## Features

### Migration Phases

#### 🔍 **Discovery Phase**
- **Asset Inventory**: Comprehensive discovery and cataloging of existing infrastructure
- **Dependency Mapping**: Automated identification of application and service dependencies
- **Environment Scanning**: Deep analysis of current system configurations and requirements

#### 📊 **Assess Phase**
- **6R Treatment Analysis**: AI-powered recommendations for Rehost, Replatform, Refactor, Rearchitect, Retire, or Retain strategies
- **Wave Planning**: Intelligent migration sequencing and batch planning
- **Risk Assessment**: Automated identification of migration risks and mitigation strategies

#### 📋 **Plan Phase**
- **Migration Timeline**: Detailed project scheduling with milestone tracking
- **Resource Allocation**: Optimal resource planning and capacity management
- **Target Architecture Design**: AI-assisted cloud architecture recommendations

### AI-Powered Features

- **🤖 Migration Goals Assistant**: Intelligent guidance for setting and achieving migration objectives
- **🎯 6R Assistant**: Automated analysis and recommendations for migration strategies
- **⚡ Real-time Updates**: WebSocket-powered live status updates and notifications
- **💬 Feedback Widget**: Integrated user feedback collection for continuous improvement
- **🧭 Sidebar Navigation**: Intuitive phase-based navigation system

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Data Layer    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ • TypeScript    │    │ • Python        │    │ • Data Storage  │
│ • Tailwind CSS  │    │ • CrewAI        │    │ • Persistence   │
│ • React         │    │ • WebSocket     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   AI Agents     │
                    │   (CrewAI)      │
                    │                 │
                    │ • Migration AI  │
                    │ • 6R Analysis   │
                    │ • Planning AI   │
                    └─────────────────┘
```

### Technical Stack

**Frontend**: Next.js with TypeScript and Tailwind CSS
- Structured in `pages/` directory with dedicated subfolders for Discovery, Assess, and Plan phases
- Component-based architecture with shadcn/ui components
- Real-time updates via WebSocket integration

**Backend**: FastAPI with Python
- RESTful API design with async/await patterns
- PostgreSQL integration for data persistence
- CrewAI framework for AI agent orchestration
- WebSocket support for real-time communication

**Integration**: 
- WebSocket for real-time updates and notifications
- Middleware architecture prepared for CloudBridge integration
- RESTful API communication between frontend and backend

> **Note**: The backend development is the current focus (May 2025 – August 2025) with the UI already in MVP stage.

## Installation

### Prerequisites

- **Node.js** (v18.0.0 or higher)
- **Python** (3.9+ required)
- **PostgreSQL** (v13 or higher)
- **Git**

### Setup Instructions

#### **Option 1: Quick Setup (Recommended)**

1. **Clone the repository**
   ```bash
   git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
   cd migrate-ui-orchestrator
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

#### **Option 2: Manual Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
   cd migrate-ui-orchestrator
   ```

2. **Backend Setup (Python 3.11+ required for CrewAI)**
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   npm install
   ```

4. **Environment Configuration**
   
   Copy and configure environment file:
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   ```

5. **Start the Application**
   
   **Backend** (Terminal 1):
   ```bash
   cd backend && source venv/bin/activate
   python main.py
   ```
   
   **Frontend** (Terminal 2):
   ```bash
   npm run dev
   ```

#### **Option 3: Docker Setup**

1. **Prerequisites**
   - Docker Desktop installed and running
   - Docker Hub account (free) for image pulls

2. **Run Docker setup**
   ```bash
   chmod +x docker-setup.sh
   ./docker-setup.sh
   ```

3. **Access the Application**
   - Frontend: http://localhost:8081 (Fixed Port)
   - Backend API: http://localhost:8000 (Fixed Port)
   - API Documentation: http://localhost:8000/docs
   - PostgreSQL: localhost:5433 (Docker)

## Roadmap

### Development Sprint Plan (May 27, 2025 – August 31, 2025)

#### **Sprint 1** (May 27 – June 9, 2025) - ✅ **COMPLETED**
- ✅ Initialize FastAPI project structure
- ✅ Set up CrewAI integration framework
- ✅ Establish database schema and models
- ✅ Create basic API endpoints
- ✅ Configure PostgreSQL with SQLAlchemy async
- ✅ Implement WebSocket manager for real-time updates
- ✅ Set up Railway.app deployment configuration

#### **Sprint 2** (June 10 – June 23, 2025)
- 🔄 Implement Discovery phase backend logic
- 🔄 Asset inventory API endpoints
- 🔄 Dependency mapping algorithms
- 🔄 Environment scanning capabilities

#### **Sprint 3** (June 24 – July 7, 2025)
- ⏳ Enable Assess phase backend functionality
- ⏳ 6R analysis engine implementation
- ⏳ Wave planning algorithms
- ⏳ Risk assessment automation

#### **Sprint 4** (July 8 – July 21, 2025)
- ⏳ Develop Plan phase backend services
- ⏳ Migration timeline generation
- ⏳ Resource allocation optimization
- ⏳ Target architecture recommendations

#### **Sprint 5** (July 22 – August 4, 2025)
- ⏳ Enhance CrewAI agent capabilities
- ⏳ Optimize API performance and caching
- ⏳ Implement advanced AI features
- ⏳ WebSocket real-time updates

#### **Sprint 6** (August 5 – August 18, 2025)
- ⏳ Frontend-backend integration testing
- ⏳ CloudBridge middleware preparation
- ⏳ End-to-end workflow testing
- ⏳ Performance optimization

#### **Sprint 7** (August 19 – August 31, 2025)
- ⏳ Comprehensive testing and QA
- ⏳ Documentation finalization
- ⏳ Deployment preparation
- ⏳ Security audit and compliance

### Future Phases

- **September 2025**: CloudBridge integration and external system connectivity
- **Q4 2025**: Production deployment and enterprise features
- **Q1 2026**: Advanced analytics and reporting capabilities

> **Note**: This roadmap will be updated with each sprint completion to reflect actual progress and any scope adjustments.

## Contributing

We welcome contributions from the development community! Please follow these guidelines:

### Getting Started

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards:
   - **Frontend**: TypeScript with ESLint configuration
   - **Backend**: Python with PEP 8 style guidelines
   - **Documentation**: Clear comments and README updates

3. **Submit a pull request** with:
   - Clear description of changes
   - Test coverage for new features
   - Updated documentation if applicable

### Code Review Process

All contributions are reviewed by our development team:
- **3 Python Developers** (Backend review)
- **1 AI/ML Developer** (AI features review)
- **1 Next.js Developer** (Frontend review)
- **1 Business Analyst** (Requirements validation)
- **1 Project Manager** (Overall coordination)

### Development Standards

- Write comprehensive tests for new features
- Follow existing code patterns and architecture
- Update documentation for API changes
- Ensure backward compatibility when possible

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 AI Force Migration Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Contact

For questions, feedback, or support:

- **Project Manager**: [pm@aiforce-migration.com](mailto:pm@aiforce-migration.com)
- **GitHub Issues**: [Create an issue](https://github.com/your-org/ai-force-migration-platform/issues)
- **Documentation**: [Project Wiki](https://github.com/your-org/ai-force-migration-platform/wiki)
- **Slack Channel**: #ai-force-migration (for team members)

---

**Built with ❤️ by the AI Force Migration Team**
