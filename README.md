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

### 🧠 AI Learning System (Latest Enhancement)

The platform now features a sophisticated AI learning system that continuously improves through user feedback and data analysis:

#### **Dynamic Field Mapping**
- **🔧 External Tool Interface**: AI agents can query, learn, and update field mappings through dedicated tools
- **📚 Persistent Learning**: Field mappings are learned from user feedback and stored across sessions
- **🎯 Reduced False Alerts**: System learns field equivalencies (e.g., RAM_GB → Memory (GB), APPLICATION_OWNER → Business Owner)
- **🔄 Continuous Improvement**: Each interaction teaches the system new patterns

#### **Agent Monitoring & Management**
- **📊 Real-time Agent Status**: Monitor AI agent activities and task execution
- **🔄 Manual Refresh Controls**: On-demand monitoring updates instead of excessive polling
- **📈 Performance Tracking**: Track agent success rates, execution times, and learning progress
- **🎛️ Task Management**: View active tasks, completed work, and hanging processes

#### **Field Mapping Intelligence**
- **🗺️ Smart Field Recognition**: Automatically maps data columns to canonical field names
- **📝 User Feedback Learning**: Learns from corrections like "DR_TIER should map to Criticality"
- **💾 Persistent Knowledge Base**: Stores learned mappings in `field_mappings.json` for future use
- **🔍 Pattern Recognition**: Identifies field mapping patterns across different CMDB export formats

#### **Testing & Verification**
- **🧪 Comprehensive Test Suite**: Automated tests verify AI learning functionality
- **🐳 Docker Integration**: All AI features work seamlessly in containerized environments
- **✅ Verification Scripts**: Built-in scripts to test field mapping and agent functionality

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

#### **Docker Management Scripts**

For development and troubleshooting, use these additional Docker scripts:

**Rebuild containers with latest code changes:**
```bash
./docker-rebuild.sh
```
This script:
- Stops all containers
- Removes existing containers and images
- Rebuilds with latest code changes
- Starts fresh containers

**Verify all systems are working:**
```bash
./verify-docker-changes.sh
```
This script tests:
- Container health status
- Backend API functionality
- Field mapping tool availability
- Agent monitoring endpoints
- Frontend accessibility

**View logs for debugging:**
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All services
docker-compose logs -f
```

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

## 🚀 Recent Improvements

### Health Check Optimization
- **Removed Constant Health Checks**: Docker health checks are no longer running constantly
- **On-Demand Health Checking**: New script `./scripts/health-check.sh` for manual health verification
- **Resource Efficiency**: Reduces system resource usage while maintaining monitoring capabilities

### Data Persistence Enhancement
- **Discovery to Assessment Flow**: Asset inventory from Discovery phase now properly persists to Assessment/6R Treatment
- **New Applications API**: Added `/api/v1/discovery/applications` endpoint to transform assets for 6R analysis
- **Smart Asset Filtering**: Only Applications, Servers, and Databases are available for 6R treatment
- **Demo Data Fallback**: Provides sample applications when no discovery data exists

### Usage

#### Health Checking
```bash
# Check all services
./scripts/health-check.sh

# Check specific service
./scripts/health-check.sh backend
./scripts/health-check.sh frontend
./scripts/health-check.sh postgres
./scripts/health-check.sh containers
```

#### Data Flow
1. **Discovery Phase**: Upload and process CMDB data
2. **Assessment Phase**: Discovered applications automatically appear in 6R Treatment
3. **Fallback**: If no discovery data exists, demo applications are provided

## 🏗️ Architecture Overview

## 🔧 Data Persistence & Analysis Workflow

### Discovery → Assessment Data Flow
- **Real Application Names**: Analysis history now displays actual application names from Discovery phase
- **Application Context**: Selected applications carry forward their department, technology stack, and criticality data
- **Workflow Clarity**: Analysis Workflow clearly shows which application is being analyzed in the title
- **Parameter Separation**: Distinguished between organizational parameters (set once) vs application-specific parameters

### Analysis History Authenticity
- **Real Backend Data**: History displays actual analysis records from backend database
- **CrewAI Attribution**: Analyses are properly attributed to "CrewAI Agents" instead of generic "System"
- **Dynamic Application Loading**: Application names are fetched from `/api/v1/discovery/applications` endpoint
- **Fallback Handling**: Graceful fallback to display format when discovery data is unavailable

### Analysis Workflow Improvements
```
1. Select Application → Shows real applications from Discovery phase
2. Set Organizational Parameters → Company-wide settings (compliance, cost sensitivity, etc.)
3. Configure App-Specific Parameters → Business value, technical complexity for the selected app
4. Start Analysis → CrewAI agents process the application with real context
5. View Results → Recommendations based on actual agentic analysis, not templates
```

### Bulk Analysis Clarification
- **Purpose**: Monitoring existing bulk operations initiated from Discovery phase
- **+New Job**: Disabled with clear messaging - bulk analysis should start from Discovery workflow
- **Real vs Mock**: Only shows actual running/completed jobs, no mock data

### Data Quality Indicators
- **Analysis Source**: All analyses show "CrewAI Agents" as analyst to indicate agentic processing
- **Processing Status**: Clear distinction between template responses and actual agent recommendations
- **Application Context**: Technology stack, department, and criticality visible during analysis

## 🧠 CrewAI Analysis Validation

### Ensuring Authentic Agent Processing
To verify if an analysis used real CrewAI agents vs templates:

1. **Check Analysis History**: Look for "CrewAI Agents" in the Analyst column
2. **Review Recommendations**: Authentic agent analysis includes:
   - Specific technical factors relevant to the technology stack
   - Context-aware next steps mentioning actual application details
   - Confidence scores that vary based on real parameter combinations
3. **Backend Logs**: Agent processing appears in backend logs with detailed reasoning

### Mock vs Real Data Detection
- **Mock Data Indicators**: Generic application names like "Application 44", "IT" department fallback
- **Real Data Indicators**: Specific application names from Discovery, actual departments and tech stacks
- **Processing History**: Real analyses show iterative agent reasoning in backend logs
