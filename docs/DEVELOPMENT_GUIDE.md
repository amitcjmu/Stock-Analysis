# Development Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [API Development](#api-development)
8. [Frontend Development](#frontend-development)
9. [AI Agent Development](#ai-agent-development)
10. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
11. [Deployment](#deployment)
12. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **Docker & Docker Compose**: For containerized development
- **Git**: For version control
- **VS Code**: Recommended IDE with extensions

### Required VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.vscode-pylance",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers",
    "ms-python.black-formatter",
    "ms-python.isort",
    "charliermarsh.ruff"
  ]
}
```

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip and install build dependencies
python -m pip install --upgrade pip
pip install wheel setuptools

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Install pre-commit hooks
pre-commit install
```

### 3. Frontend Setup

```bash
# Navigate to project root
cd ..

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

### 4. Docker Setup (Alternative)

```bash
# Build and start all services
docker-compose up --build

# For development with hot reload
docker-compose -f docker-compose.dev.yml up
```

### 5. Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/migration_db

# AI Configuration
DEEPINFRA_API_KEY=your_deepinfra_api_key
CREWAI_ENABLED=true
CREWAI_TEMPERATURE=0.1
CREWAI_MAX_TOKENS=1000

# API Configuration
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Security
SECRET_KEY=your_secret_key_here
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Core configuration
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── websocket/            # WebSocket handlers
├── data/                     # Data files and exports
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
└── main.py                   # Application entry point
```

### Frontend Structure
```
src/
├── app/                      # Next.js App Router
├── components/               # React components
├── hooks/                    # Custom React hooks
├── lib/                      # Utility libraries
├── types/                    # TypeScript definitions
└── config/                   # Configuration files
```

## Development Workflow

### 1. Feature Development Process

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and commit frequently
git add .
git commit -m "feat: add new feature description"

# 3. Push branch and create PR
git push origin feature/your-feature-name
```

### 2. Commit Message Convention

Follow conventional commits format:

```
type(scope): description

feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: adding tests
chore: maintenance tasks
```

### 3. Branch Naming Convention

```
feature/feature-name        # New features
bugfix/bug-description      # Bug fixes
hotfix/critical-fix         # Critical fixes
docs/documentation-update   # Documentation
refactor/code-improvement   # Code refactoring
```

## Coding Standards

### Python (Backend)

#### Code Formatting
```bash
# Use Black for code formatting
black app/

# Use isort for import sorting
isort app/

# Use pylint for linting
pylint app/
```

#### Type Hints
```python
# Always use type hints
from typing import Dict, List, Optional, Any

def analyze_data(data: Dict[str, Any]) -> Optional[List[str]]:
    """Analyze data and return results."""
    if not data:
        return None
    return list(data.keys())
```

## API Development

### Creating New Endpoints

1. Add a new file in the appropriate directory under `app/api/v1/endpoints/`
2. Define your FastAPI router and endpoints using Pydantic V2 models
3. Import and include the router in `app/api/v1/api.py`

Example endpoint with Pydantic V2:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models import Item
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.core.database import get_db

router = APIRouter(prefix="/items", tags=["items"])

@router.get(
    "/",
    response_model=List[ItemResponse],
    summary="List items",
    description="Retrieve a list of items with pagination"
)
async def read_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve items with pagination.
    
    - **skip**: Number of items to skip
    - **limit**: Maximum number of items to return
    """
    result = await db.execute(select(Item).offset(skip).limit(limit))
    items = result.scalars().all()
    return items
```

### Pydantic V2 Best Practices

1. **Model Configuration**:
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional
   
   class ItemBase(BaseModel):
       name: str = Field(..., min_length=1, max_length=100)
       description: Optional[str] = Field(None, max_length=500)
   
   class ItemCreate(ItemBase):
       pass
   
   class ItemUpdate(BaseModel):
       name: Optional[str] = Field(None, min_length=1, max_length=100)
       description: Optional[str] = Field(None, max_length=500)
   
   class ItemResponse(ItemBase):
       id: int
       owner_id: int
       
       model_config = {
           "from_attributes": True,  # Replaces orm_mode
           "json_schema_extra": {
               "example": {
                   "id": 1,
                   "name": "Example Item",
                   "description": "An example item",
                   "owner_id": 1
               }
           }
       }
   ```

2. **Field Validation**:
   ```python
   from pydantic import field_validator, EmailStr
   
   class UserCreate(BaseModel):
       email: EmailStr
       password: str = Field(..., min_length=8)
       
       @field_validator('password')
       def password_complexity(cls, v):
           if not any(c.isupper() for c in v):
               raise ValueError('Password must contain at least one uppercase letter')
           if not any(c.isdigit() for c in v):
               raise ValueError('Password must contain at least one digit')
           return v
   ```

3. **Custom Types**:
   ```python
   from pydantic import GetCoreSchemaHandler
   from pydantic_core import CoreSchema, core_schema
   
   class CustomType:
       def __init__(self, value: str):
           self.value = value
   
       @classmethod
       def __get_pydantic_core_schema__(
           cls, _source_type: Any, _handler: GetCoreSchemaHandler
       ) -> CoreSchema:
           return core_schema.no_info_after_validator_function(
               cls.validate,
               core_schema.str_schema(),
               serialization=core_schema.to_string_ser_schema(),
           )
       
       @classmethod
       def validate(cls, value: str) -> 'CustomType':
           if not value.startswith('custom_'):
               raise ValueError('Must start with "custom_"')
           return cls(value)
   ```

4. **Error Handling**:
   ```python
   from fastapi import HTTPException, status
   
   @router.get("/{item_id}", response_model=ItemResponse)
   async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
       db_item = await db.get(Item, item_id)
       if db_item is None:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail="Item not found"
           )
       return db_item
   ```

5. **Dependency Injection**:
   ```python
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   
   async def get_current_user(
       token: str = Depends(oauth2_scheme),
       db: AsyncSession = Depends(get_db)
   ) -> User:
       credentials_exception = HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Could not validate credentials",
           headers={"WWW-Authenticate": "Bearer"},
       )
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           username: str = payload.get("sub")
           if username is None:
               raise credentials_exception
       except JWTError:
           raise credentials_exception
       
       user = await get_user(db, username=username)
       if user is None:
           raise credentials_exception
       return user
   ```
        
    Raises:
        ValueError: If data format is invalid
    """
    pass
```

#### Error Handling
```python
import logging

logger = logging.getLogger(__name__)

async def api_endpoint():
    try:
        result = await process_data()
        return {"success": True, "data": result}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### TypeScript (Frontend)

#### Component Structure
```tsx
// components/ComponentName.tsx
'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'

interface ComponentProps {
  title: string
  onAction: (data: string) => void
  className?: string
}

export function ComponentName({ title, onAction, className }: ComponentProps) {
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Effect logic
  }, [])

  const handleAction = async () => {
    setIsLoading(true)
    try {
      await onAction('data')
    } catch (error) {
      console.error('Action failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={className}>
      <h2>{title}</h2>
      <Button onClick={handleAction} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Action'}
      </Button>
    </div>
  )
}
```

#### Type Definitions
```typescript
// types/api.ts
export interface CMDBAnalysisRequest {
  filename: string
  content: string
  fileType: string
}

export interface CMDBAnalysisResponse {
  asset_type_detected: string
  confidence_level: number
  data_quality_score: number
  missing_fields_relevant: string[]
  recommendations: string[]
}
```

## Testing Guidelines

### Backend Testing

#### Unit Tests
```python
# tests/backend/test_field_mapper.py
import pytest
from app.services.field_mapper import field_mapper

class TestFieldMapper:
    def test_learn_field_mapping(self):
        """Test learning a new field mapping."""
        result = field_mapper.learn_field_mapping(
            "RAM_GB", "Memory (GB)", "test"
        )
        assert result["success"] is True
        assert "RAM_GB → Memory (GB)" in result["mapping"]

    def test_find_matching_fields(self):
        """Test finding matching fields."""
        columns = ["RAM_GB", "CPU_CORES", "STORAGE_GB"]
        matches = field_mapper.find_matching_fields(columns, "Memory (GB)")
        assert "RAM_GB" in matches

    @pytest.mark.asyncio
    async def test_ai_learning_integration(self):
        """Test AI learning integration."""
        # Test implementation
        pass
```

#### Integration Tests
```python
# tests/backend/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIIntegration:
    def test_analyze_cmdb_endpoint(self):
        """Test CMDB analysis endpoint."""
        test_data = {
            "filename": "test.csv",
            "content": "name,type,memory\nserver1,server,8GB",
            "fileType": "text/csv"
        }
        
        response = client.post("/api/v1/discovery/analyze", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "asset_type_detected" in data
        assert "confidence_level" in data
```

### Frontend Testing

#### Component Tests
```tsx
// components/__tests__/CMDBUpload.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { CMDBUpload } from '../CMDBUpload'

describe('CMDBUpload', () => {
  it('renders upload area', () => {
    const mockOnComplete = jest.fn()
    render(<CMDBUpload onAnalysisComplete={mockOnComplete} />)
    
    expect(screen.getByText('Upload CMDB Data')).toBeInTheDocument()
    expect(screen.getByText('Drag & drop CMDB file here')).toBeInTheDocument()
  })

  it('handles file upload', async () => {
    const mockOnComplete = jest.fn()
    render(<CMDBUpload onAnalysisComplete={mockOnComplete} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = screen.getByRole('textbox', { hidden: true })
    
    fireEvent.change(input, { target: { files: [file] } })
    
    // Assert upload behavior
  })
})
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
npm test

# Coverage reports
pytest --cov=app tests/
npm run test:coverage
```

## API Development

### Creating New Endpoints

#### 1. Define Pydantic Schemas
```python
# app/schemas/new_feature.py
from pydantic import BaseModel
from typing import List, Optional

class FeatureRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[str] = []

class FeatureResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
```

#### 2. Create Database Model
```python
# app/models/new_feature.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### 3. Implement Service Logic
```python
# app/services/feature_service.py
from typing import List
from app.models.new_feature import Feature
from app.schemas.new_feature import FeatureRequest, FeatureResponse

class FeatureService:
    async def create_feature(self, request: FeatureRequest) -> FeatureResponse:
        """Create a new feature."""
        # Implementation
        pass
    
    async def get_features(self) -> List[FeatureResponse]:
        """Get all features."""
        # Implementation
        pass
```

#### 4. Create API Endpoint
```python
# app/api/v1/endpoints/features.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.new_feature import FeatureRequest, FeatureResponse
from app.services.feature_service import FeatureService

router = APIRouter()

@router.post("/", response_model=FeatureResponse)
async def create_feature(
    request: FeatureRequest,
    service: FeatureService = Depends()
):
    """Create a new feature."""
    try:
        return await service.create_feature(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[FeatureResponse])
async def get_features(service: FeatureService = Depends()):
    """Get all features."""
    return await service.get_features()
```

## Frontend Development

### Creating New Components

#### 1. Component Structure
```tsx
// components/feature/FeatureManager.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'

interface Feature {
  id: string
  name: string
  status: string
  created_at: string
}

export function FeatureManager() {
  const [features, setFeatures] = useState<Feature[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadFeatures()
  }, [])

  const loadFeatures = async () => {
    try {
      const data = await apiClient.getFeatures()
      setFeatures(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load features",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature Manager</CardTitle>
      </CardHeader>
      <CardContent>
        {features.map((feature) => (
          <div key={feature.id} className="p-2 border rounded mb-2">
            <h3>{feature.name}</h3>
            <p>Status: {feature.status}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
```

#### 2. Custom Hooks
```tsx
// hooks/useFeatures.ts
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

export function useFeatures() {
  const [features, setFeatures] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadFeatures = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getFeatures()
      setFeatures(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadFeatures()
  }, [])

  return {
    features,
    isLoading,
    error,
    refetch: loadFeatures
  }
}
```

## AI Agent Development

### Creating New Agents

#### 1. Agent Definition
```python
# app/services/agents.py
def _create_new_agent(self):
    """Create a new specialized agent."""
    return Agent(
        role='Specialized Agent Role',
        goal='Specific goal for this agent',
        backstory="""
        Detailed backstory explaining the agent's expertise,
        experience, and capabilities. Include information about
        available tools and expected behavior.
        """,
        tools=[available_tools],
        llm=self.llm,
        memory=False,
        verbose=False,
        allow_delegation=False
    )
```

#### 2. Agent Tools
```python
# app/services/tools/new_tool.py
class NewAgentTool:
    """Tool for agents to perform specific tasks."""
    
    def perform_action(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the tool's main action."""
        try:
            # Tool implementation
            result = self._process_parameters(parameters)
            
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _process_parameters(self, parameters: Dict[str, Any]) -> Any:
        """Process tool parameters."""
        # Implementation
        pass
```

#### 3. Agent Tasks
```python
# Creating tasks for agents
async def create_agent_task(self, task_description: str, agent_name: str):
    """Create a task for a specific agent."""
    
    agent = self.agents.get(agent_name)
    if not agent:
        raise ValueError(f"Agent {agent_name} not found")
    
    task = Task(
        description=task_description,
        agent=agent,
        expected_output="Detailed description of expected output format"
    )
    
    return await self._execute_task_async(task)
```

## Debugging and Troubleshooting

### Backend Debugging

#### Logging Configuration
```python
# app/core/logging.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )

# Usage in modules
logger = logging.getLogger(__name__)
logger.info("Information message")
logger.error("Error message")
```

#### Debug Mode
```python
# Enable debug mode in development
if settings.DEBUG:
    import pdb; pdb.set_trace()  # Breakpoint
```

### Frontend Debugging

#### Console Debugging
```tsx
// Debug component state
useEffect(() => {
  console.log('Component state:', { isLoading, data, error })
}, [isLoading, data, error])

// Debug API calls
const debugApiCall = async () => {
  console.log('Making API call...')
  try {
    const result = await apiClient.getData()
    console.log('API result:', result)
    return result
  } catch (error) {
    console.error('API error:', error)
    throw error
  }
}
```

#### React Developer Tools
- Install React Developer Tools browser extension
- Use Components tab to inspect component state
- Use Profiler tab to identify performance issues

### Common Issues and Solutions

#### 1. CORS Issues
```python
# Backend: Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Database Connection Issues
```python
# Check database connection
async def check_db_connection():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### 3. AI Agent Issues
```python
# Debug agent execution
logger.info(f"Starting task: {task.description}")
logger.info(f"Agent: {task.agent.role}")
logger.info(f"Available tools: {[tool.__class__.__name__ for tool in task.agent.tools]}")
```

## Deployment

### Development Deployment

#### Using Docker Compose
```bash
# Build and start services
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Production Deployment

#### Environment Setup
```bash
# Set production environment variables
export NODE_ENV=production
export PYTHON_ENV=production
export DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db
```

#### Build Process
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m pytest tests/

# Frontend
npm run build
npm run test
```

### Health Checks

#### Backend Health Check
```python
# app/api/v1/endpoints/health.py
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION
    }
```

#### Frontend Health Check
```tsx
// lib/health.ts
export async function checkHealth() {
  try {
    const response = await fetch('/api/v1/health')
    return response.ok
  } catch {
    return false
  }
}
```

## Best Practices

### Code Quality

1. **Write Tests First**: Follow TDD when possible
2. **Use Type Hints**: Always use type hints in Python and TypeScript
3. **Handle Errors Gracefully**: Implement proper error handling
4. **Log Appropriately**: Use appropriate log levels
5. **Document Code**: Write clear docstrings and comments

### Performance

1. **Database Queries**: Use async queries and proper indexing
2. **API Responses**: Implement pagination for large datasets
3. **Frontend Optimization**: Use React.memo and useMemo for expensive operations
4. **Caching**: Implement caching where appropriate

### Security

1. **Input Validation**: Validate all user inputs
2. **Environment Variables**: Never commit secrets to version control
3. **HTTPS**: Use HTTPS in production
4. **Authentication**: Implement proper authentication and authorization

### Collaboration

1. **Code Reviews**: All code must be reviewed before merging
2. **Documentation**: Keep documentation up to date
3. **Communication**: Use clear commit messages and PR descriptions
4. **Testing**: Ensure all tests pass before merging

This development guide provides a comprehensive foundation for working on the AI Force Migration Platform. Follow these guidelines to maintain code quality, consistency, and team productivity. 