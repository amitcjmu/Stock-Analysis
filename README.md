# AI Force Migration Platform

## Overview

The **AI Force Migration Platform** is a comprehensive cloud migration management application designed to orchestrate the entire cloud migration journey from discovery to decommission. Powered by **AI-driven automation** with **CrewAI agents**, this platform streamlines complex migration processes through intelligent insights, automated workflows, and continuous learning.

Built with a modern tech stack featuring a **Next.js frontend** and **FastAPI backend**, the platform integrates with **CrewAI** for advanced agentic AI capabilities. The application runs **entirely in Docker containers** for consistent development and deployment. The platform is currently in MVP stage with **7 operational AI agents** and comprehensive LLM cost tracking, preparing for **CloudBridge integration** expected in September 2025.

## 🚀 Key Features

### 🧠 **Agentic AI Architecture (NEW)**

The platform features **7 active CrewAI agents** that provide intelligent automation across all migration phases:

#### **Active AI Agents**
1. **Asset Intelligence Agent** - Asset inventory management and classification
2. **CMDB Data Analyst** - Expert CMDB analysis and field mapping
3. **Learning Specialist** - Enhanced with asset learning and pattern recognition
4. **Pattern Recognition Agent** - Field mapping intelligence and data normalization
5. **Migration Strategy Expert** - 6R strategy analysis and recommendations
6. **Risk Assessment Specialist** - Migration risk analysis and mitigation
7. **Wave Planning Coordinator** - Migration sequencing and optimization

#### **Agent Capabilities**
- **🔄 Continuous Learning**: Agents learn from user feedback and improve over time
- **📊 Real-time Monitoring**: Live agent status tracking with performance metrics
- **🎯 Intelligent Decision Making**: AI-powered analysis rather than hard-coded rules
- **💾 Persistent Memory**: Agents remember patterns and user preferences across sessions

### 💰 **LLM Cost Management (NEW)**

Comprehensive cost tracking and optimization for all AI model usage:

#### **Complete Coverage**
- **Multi-Modal Chat Interface**: Gemma-3-4b-it model for user interactions
- **Feedback Processing**: AI-powered sentiment analysis and insight extraction
- **Agent Operations**: All 7 agents tracked with cost attribution
- **Background Tasks**: Automated analysis and learning processes

#### **Cost Optimization**
- **Intelligent Model Selection**: 75% cost reduction for routine tasks
- **Real-time Monitoring**: Live cost tracking with budget alerts
- **Provider Comparison**: OpenAI, DeepInfra, and Anthropic usage analytics
- **Feature-level Breakdown**: Cost attribution by platform feature

#### **Cost Dashboard Features**
- **7 Admin Endpoints**: Live data from `/api/v1/admin/llm-usage/*`
- **Visual Analytics**: Comprehensive charts and trend analysis
- **Export Capabilities**: PDF and CSV cost reports
- **Budget Management**: Alerts and threshold monitoring

### Migration Phases

#### 🔍 **Discovery Phase**
- **Asset Inventory**: AI-powered discovery and cataloging with agent classification
- **Dependency Mapping**: Automated identification of application and service dependencies
- **Tech Debt Analysis**: Deep analysis of technical debt and modernization opportunities
- **Smart Field Mapping**: AI learns field mappings from user feedback and corrections
- **Data Cleansing**: Automated data quality improvement with agent assistance

#### 📊 **Assess Phase**
- **6R Treatment Analysis**: AI-powered recommendations for migration strategies
- **Agent-Driven Analysis**: CrewAI agents analyze each application with contextual intelligence
- **Wave Planning**: Intelligent migration sequencing with dependency consideration
- **Risk Assessment**: Automated identification of migration risks with mitigation strategies
- **Real Application Processing**: Integration with Discovery data for authentic analysis

#### 📋 **Plan Phase**
- **Migration Timeline**: Agent-powered project scheduling with milestone tracking
- **Resource Allocation**: AI-optimized resource planning and capacity management
- **Target Architecture Design**: Agent-assisted cloud architecture recommendations
- **Wave Coordination**: Intelligent migration wave planning and execution sequencing

#### 🔄 **Execute Phase**
- **Rehost Operations**: Automated lift-and-shift migration execution
- **Replatform Services**: Platform migration with AI optimization recommendations
- **Cutover Management**: Intelligent cutover scheduling and execution tracking
- **Real-time Monitoring**: Live migration status and performance tracking

#### ✨ **Modernize Phase**
- **Refactor Recommendations**: AI-powered code modernization suggestions
- **Rearchitect Planning**: Agent-driven architecture transformation guidance
- **Rewrite Strategies**: Intelligent application rewrite planning and execution
- **Progress Tracking**: Real-time modernization progress with success metrics

#### 🗄️ **Decommission Phase**
- **Planning Automation**: AI-powered decommission planning and scheduling
- **Data Retention**: Intelligent data archival and retention policy management
- **Execution Tracking**: Automated decommission execution with validation
- **Compliance Verification**: Automated compliance checking and documentation

#### 💹 **FinOps Phase (NEW)**
- **Cloud Cost Comparison**: AI-powered cost analysis across providers
- **Savings Analysis**: Migration cost optimization recommendations
- **LLM Cost Dashboard**: Comprehensive AI usage cost tracking and analytics
- **Wave Cost Breakdown**: Financial analysis by migration wave
- **Budget Alerts**: Proactive cost monitoring and threshold alerts

### 🎯 **AI Learning System (Enhanced)**

The platform features a sophisticated AI learning system that continuously improves:

#### **Dynamic Learning Capabilities**
- **🔧 Field Mapping Intelligence**: AI learns field mappings from user corrections (e.g., "DR_TIER → Criticality")
- **📚 Persistent Knowledge**: Learned patterns stored in database and JSON files
- **🎯 Reduced False Alerts**: System learns field equivalencies and reduces noise
- **🔄 Feedback Integration**: Each user correction improves future AI performance

#### **Agent Memory System**
- **📊 Cross-Session Learning**: Agents remember patterns across platform sessions
- **🎛️ Context Awareness**: Agents maintain context of user preferences and workflows
- **📈 Performance Tracking**: AI success rates, execution times, and improvement metrics
- **🔍 Pattern Recognition**: Advanced pattern matching for better decision making

### 🏗️ **Docker-First Architecture (Enhanced)**

The entire platform runs in Docker containers for consistent deployment:

#### **Container Services**
- **Frontend**: `migration_frontend` - Next.js application
- **Backend**: `migration_backend` - FastAPI with CrewAI integration
- **Database**: `migration_db` - PostgreSQL with async support
- **All Development**: Happens within containers, never locally

#### **Development Workflow**
```bash
# Start development environment
docker-compose up -d --build

# Real-time debugging
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_db psql -U user -d migration_db

# View logs
docker-compose logs -f backend frontend
```

### 📱 **Enhanced User Experience**

#### **Real-time Features**
- **WebSocket Integration**: Live updates across all platform components
- **Agent Monitoring**: Real-time agent status and task execution tracking
- **Cost Monitoring**: Live LLM usage and cost tracking
- **Progress Tracking**: Real-time migration progress across all phases

#### **User Interface Improvements**
- **Context Breadcrumbs**: Consistent navigation with multi-tenant context
- **Feedback System**: AI-powered feedback analysis with sentiment tracking
- **Responsive Design**: Scalable layouts across all devices and screen sizes
- **Dark Mode Support**: Coming soon with user preference storage

## Architecture

### High-Level Architecture (Updated)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Data Layer    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│ • TypeScript    │    │ • Python        │    │ • Multi-tenant  │
│ • Tailwind CSS  │    │ • 7 AI Agents   │    │ • Learning Data │
│ • React         │    │ • WebSocket     │    │ • Cost Tracking │
│ • Real-time UI  │    │ • LLM Tracking  │    │ • Agent Memory  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   AI Agents     │
                    │   (CrewAI)      │
                    │                 │
                    │ • Asset Intel   │
                    │ • CMDB Analysis │
                    │ • Learning Spec │
                    │ • Pattern Recog │
                    │ • Migration Exp │
                    │ • Risk Assess   │
                    │ • Wave Planning │
                    └─────────────────┘
```

### Technical Stack (Updated)

**Frontend**: Next.js with TypeScript and Tailwind CSS
- **Structured Pages**: Phase-based architecture with specialized components
- **Component Library**: shadcn/ui components with custom extensions
- **Real-time Features**: WebSocket integration for live updates
- **Context Management**: Multi-tenant context with breadcrumb navigation
- **Responsive Design**: Mobile-first design with scalable layouts

**Backend**: FastAPI with Python and CrewAI
- **Async Architecture**: Full async/await patterns for high performance
- **Multi-tenant Database**: Client account scoping for enterprise deployment
- **AI Agent Integration**: 7 specialized CrewAI agents with learning capabilities
- **LLM Cost Tracking**: Comprehensive cost monitoring across all AI usage
- **WebSocket Support**: Real-time communication for live updates

**AI & Learning**:
- **CrewAI Framework**: Advanced multi-agent orchestration and coordination
- **Learning Systems**: Persistent memory and pattern recognition across sessions
- **Cost Optimization**: Intelligent model selection for optimal cost/performance
- **Multi-Model Support**: OpenAI, DeepInfra, and Anthropic integration

**Infrastructure**:
- **Docker Containers**: Complete containerized development and deployment
- **PostgreSQL**: Async database with comprehensive data modeling
- **WebSocket Manager**: Real-time communication and status updates
- **Health Monitoring**: Comprehensive health checks and monitoring systems

> **Note**: All development happens within Docker containers. The platform is designed for containerized deployment with no local service dependencies.

## Installation

### Prerequisites

- **Docker Desktop** (Required - all development happens in containers)
- **Git** for repository management
- **8GB RAM minimum** for optimal Docker performance

### 🐳 **Docker Setup (Recommended)**

#### **Quick Start**
```bash
# Clone repository
git clone https://github.com/CryptoYogiLLC/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator

# Start all services
docker-compose up -d --build

# Access the application
# Frontend: http://localhost:8081
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### **Development Workflow**
```bash
# View real-time logs
docker-compose logs -f backend frontend

# Execute in containers for debugging
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_backend python -m pytest tests/

# Database access
docker exec -it migration_db psql -U user -d migration_db

# Health checks
curl http://localhost:8000/health
curl http://localhost:8081
```

#### **Development Scripts**

```bash
# Rebuild with latest changes
./docker-rebuild.sh

# Verify all systems
./verify-docker-changes.sh

# Manual health checks
./scripts/health-check.sh
```

### Alternative Setup Methods

#### **Option 1: Setup Script**
```bash
chmod +x setup.sh
./setup.sh
```

#### **Option 2: Manual Setup**
```bash
# Backend (Python 3.11+ required for CrewAI)
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
npm install

# Environment configuration
cp backend/env.example backend/.env
# Edit backend/.env with your API keys

# Start services
# Terminal 1: cd backend && source venv/bin/activate && python main.py
# Terminal 2: npm run dev
```

## 🔧 Development Guidelines

### **Container-First Development**
- **All debugging happens in Docker containers**
- **Never run services locally** - use `docker exec` for interaction
- **Health monitoring** through container health checks
- **Log viewing** through `docker-compose logs -f`

### **AI Agent Development**
- **Always use agentic intelligence** over hard-coded rules
- **Implement learning capabilities** in all agent tools
- **Track agent performance** with success metrics
- **Use agent memory** for pattern recognition

### **Multi-Tenant Architecture**
- **Client account scoping** for all data access
- **Context-aware repositories** for data isolation
- **Engagement-level data management** with proper isolation
- **Admin interfaces** for tenant management

### **LLM Cost Management**
- **Track all AI model usage** through multi-model service
- **Implement cost-effective model selection**
- **Monitor usage with real-time dashboards**
- **Use cost optimization strategies**

## 🗺️ Roadmap

### **Current Status (Enhanced - Q4 2025)**

#### **✅ Completed Recent Enhancements**
- ✅ **7 Active AI Agents**: Full CrewAI agent orchestration
- ✅ **LLM Cost Tracking**: Complete cost monitoring dashboard
- ✅ **Learning Systems**: AI agents learn from user feedback
- ✅ **Docker Architecture**: Complete containerization
- ✅ **Multi-Tenant Support**: Enterprise-ready data isolation
- ✅ **Real-time Monitoring**: WebSocket-powered live updates
- ✅ **Enhanced FinOps**: Comprehensive cost analysis and optimization

#### **🔄 Active Development**
- 🔄 **Advanced Agent Capabilities**: Enhanced reasoning and decision-making
- 🔄 **Cost Optimization**: Advanced model selection algorithms
- 🔄 **User Experience**: Enhanced UI/UX with improved workflows
- 🔄 **Integration Testing**: Comprehensive end-to-end testing

#### **⏳ Planned Enhancements (Q1 2026)**
- ⏳ **CloudBridge Integration**: External system connectivity
- ⏳ **Advanced Analytics**: Enhanced reporting and insights
- ⏳ **Enterprise Features**: Advanced security and compliance
- ⏳ **Mobile Applications**: Native mobile app development

### **Development Sprint Plan (Updated)**

#### **Sprint 8** (September 1 – September 14, 2025)
- 🎯 **Agent Intelligence Enhancement**: Advanced reasoning capabilities
- 🎯 **Cost Optimization**: Predictive cost modeling and optimization
- 🎯 **User Experience**: Enhanced dashboards and workflows
- 🎯 **Integration Testing**: Comprehensive system testing

#### **Sprint 9** (September 15 – September 28, 2025)
- 🎯 **CloudBridge Preparation**: External system integration framework
- 🎯 **Security Enhancement**: Advanced security and compliance features
- 🎯 **Performance Optimization**: System performance improvements
- 🎯 **Documentation**: Comprehensive user and developer documentation

#### **Sprint 10** (September 29 – October 12, 2025)
- 🎯 **CloudBridge Integration**: Live external system connectivity
- 🎯 **Production Readiness**: Enterprise deployment preparation
- 🎯 **Advanced Features**: AI-powered advanced capabilities
- 🎯 **Quality Assurance**: Comprehensive testing and validation

## 🤝 Contributing

We welcome contributions from the development community! The platform is designed with extensibility and collaboration in mind.

### **Development Standards**

#### **Agentic-First Development**
- **Use AI agents** for all intelligence and decision-making
- **Avoid hard-coded rules** - implement learning capabilities instead
- **Test agent functionality** with comprehensive test suites
- **Document agent behavior** and learning patterns

#### **Container Development**
- **Develop within Docker containers** - never run services locally
- **Test in container environment** for consistency
- **Use container debugging** tools and workflows
- **Maintain container health** and monitoring

#### **Code Quality**
- **TypeScript** with strict typing for frontend
- **Python** with type hints and async patterns for backend
- **Comprehensive testing** for all new features
- **Documentation** for API changes and new capabilities

### **Contribution Workflow**

1. **Fork and Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop in Containers**
   ```bash
   docker-compose up -d --build
   # Make changes and test in containers
   ```

3. **Test Thoroughly**
   ```bash
   docker exec -it migration_backend python -m pytest tests/
   ./verify-docker-changes.sh
   ```

4. **Submit Pull Request**
   - Clear description of changes
   - Test coverage for new features
   - Updated documentation
   - Agent behavior documentation

## 📊 **Success Metrics**

### **Platform Performance**
- **100% LLM Cost Coverage**: All AI usage tracked and optimized
- **7 Active AI Agents**: Full agentic intelligence across all phases
- **Real-time Monitoring**: Live status and performance tracking
- **Multi-tenant Architecture**: Enterprise-ready data isolation

### **AI Intelligence**
- **Learning Accuracy**: Continuous improvement through user feedback
- **Cost Optimization**: 75% cost reduction for routine tasks
- **Agent Performance**: High success rates with fast response times
- **Pattern Recognition**: Advanced field mapping and data normalization

### **User Experience**
- **Container-First Development**: 100% containerized workflow
- **Real-time Updates**: Live status across all platform components
- **Context-Aware Interface**: Intelligent navigation and breadcrumbs
- **Comprehensive Analytics**: Advanced cost and performance insights

## 📜 License

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

## 📞 Contact

For questions, feedback, or support:

- **Project Manager**: [pm@aiforce-migration.com](mailto:pm@aiforce-migration.com)
- **GitHub Issues**: [Create an issue](https://github.com/your-org/ai-force-migration-platform/issues)
- **Documentation**: [Project Wiki](https://github.com/your-org/ai-force-migration-platform/wiki)
- **Slack Channel**: #ai-force-migration (for team members)

---

**🚀 Built with AI-Powered Intelligence by the AI Force Migration Team**

*Empowering enterprise cloud migrations through agentic AI, continuous learning, and intelligent automation.*
