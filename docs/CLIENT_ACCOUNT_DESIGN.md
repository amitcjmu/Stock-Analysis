 # Client Account & Engagement Segregation Design

## Executive Summary

This document outlines the design for implementing a comprehensive Client Account and Engagement segregation system across the AI Modernize Migration Platform. This feature ensures complete data isolation between different clients and supports multiple engagements per client, enabling the platform to serve multiple organizations simultaneously while maintaining strict data privacy and security.

## Table of Contents

1. [Business Requirements](#business-requirements)
2. [Architecture Overview](#architecture-overview)
3. [Database Design](#database-design)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [Security & Access Control](#security--access-control)
7. [API Design](#api-design)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Timeline](#implementation-timeline)

## Business Requirements

### Primary Objectives

1. **Complete Data Isolation**: Ensure no data mixing between different client accounts
2. **Multi-Engagement Support**: Allow multiple migration projects per client
3. **Seamless Context Switching**: Enable users to switch between accounts/engagements
4. **Scalable Architecture**: Support hundreds of clients with thousands of engagements
5. **Audit Trail**: Track all activities by client and engagement
6. **Role-Based Access**: Different access levels within client accounts

### User Stories

#### As a Platform Administrator
- I want to create and manage client accounts
- I want to assign users to specific client accounts
- I want to monitor usage across all clients
- I want to ensure complete data isolation

#### As a Client Administrator
- I want to create and manage engagements within my organization
- I want to assign team members to specific engagements
- I want to view all engagements for my organization
- I want to control access to sensitive engagement data

#### As a Migration Consultant
- I want to switch between different client accounts I have access to
- I want to work on multiple engagements simultaneously
- I want to see only the data relevant to my current context
- I want to maintain separate analysis histories per engagement

#### As an End User
- I want to see only the engagements I'm authorized to access
- I want clear indication of which client/engagement I'm currently working in
- I want to switch between engagements without losing my work

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Context Provider (Client/Engagement)                      │
│  ├── Account Selector Component                            │
│  ├── Engagement Selector Component                         │
│  └── Context-Aware Components                              │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway                              │
│  ├── Authentication Middleware                             │
│  ├── Context Validation Middleware                         │
│  └── Data Isolation Middleware                             │
├─────────────────────────────────────────────────────────────┤
│                    Backend Services                         │
│  ├── Account Management Service                            │
│  ├── Engagement Management Service                         │
│  ├── Context-Aware Business Logic                          │
│  └── Multi-Tenant Data Access Layer                        │
├─────────────────────────────────────────────────────────────┤
│                    Database Layer                           │
│  ├── Client Accounts Table                                 │
│  ├── Engagements Table                                     │
│  ├── User Account Associations                             │
│  └── Context-Scoped Data Tables                            │
└─────────────────────────────────────────────────────────────┘
```

### Core Concepts

#### Client Account
- **Definition**: A top-level organizational entity representing a customer
- **Scope**: Contains multiple engagements, users, and organizational settings
- **Examples**: "Acme Corporation", "Global Bank Inc", "TechStart LLC"

#### Engagement
- **Definition**: A specific migration project within a client account
- **Scope**: Contains all migration-related data (CMDB, analyses, plans, etc.)
- **Examples**: "Data Center Migration 2024", "Cloud Modernization Phase 1", "Legacy System Retirement"

#### Context
- **Definition**: The current client account + engagement combination
- **Scope**: Determines data visibility and access permissions
- **Format**: `{client_account_id}:{engagement_id}`

## Database Design

### Core Tables

#### 1. Client Accounts Table

```sql
CREATE TABLE client_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- URL-friendly identifier
    description TEXT,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    
    -- Subscription & Billing
    subscription_tier VARCHAR(50) DEFAULT 'standard',
    billing_contact_email VARCHAR(255),
    
    -- Settings
    settings JSONB DEFAULT '{}',
    branding JSONB DEFAULT '{}', -- Custom colors, logos, etc.
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints
    CONSTRAINT valid_slug CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Indexes
CREATE INDEX idx_client_accounts_slug ON client_accounts(slug);
CREATE INDEX idx_client_accounts_active ON client_accounts(is_active);
```

#### 2. Engagements Table

```sql
CREATE TABLE engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL, -- Unique within client account
    description TEXT,
    
    -- Engagement Details
    engagement_type VARCHAR(50) DEFAULT 'migration', -- migration, assessment, modernization
    status VARCHAR(50) DEFAULT 'active', -- active, completed, paused, cancelled
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    
    -- Timeline
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    
    -- Team & Contacts
    engagement_lead_id UUID REFERENCES users(id),
    client_contact_name VARCHAR(255),
    client_contact_email VARCHAR(255),
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints
    UNIQUE(client_account_id, slug),
    CONSTRAINT valid_engagement_slug CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Indexes
CREATE INDEX idx_engagements_client_account ON engagements(client_account_id);
CREATE INDEX idx_engagements_status ON engagements(status);
CREATE INDEX idx_engagements_active ON engagements(is_active);
```

#### 3. User Account Associations Table

```sql
CREATE TABLE user_account_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    
    -- Role within the client account
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- admin, manager, analyst, member, viewer
    
    -- Permissions
    permissions JSONB DEFAULT '[]', -- Array of specific permissions
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, pending
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Constraints
    UNIQUE(user_id, client_account_id)
);

-- Indexes
CREATE INDEX idx_user_account_associations_user ON user_account_associations(user_id);
CREATE INDEX idx_user_account_associations_account ON user_account_associations(client_account_id);
```

#### 4. User Engagement Associations Table

```sql
CREATE TABLE user_engagement_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    
    -- Role within the engagement
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- lead, analyst, member, viewer
    
    -- Permissions
    permissions JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Constraints
    UNIQUE(user_id, engagement_id)
);

-- Indexes
CREATE INDEX idx_user_engagement_associations_user ON user_engagement_associations(user_id);
CREATE INDEX idx_user_engagement_associations_engagement ON user_engagement_associations(engagement_id);
```

### Data Scoping Strategy

#### Approach 1: Context Columns (Recommended)

Add context columns to all data tables:

```sql
-- Example: Update existing tables
ALTER TABLE cmdb_assets ADD COLUMN client_account_id UUID REFERENCES client_accounts(id);
ALTER TABLE cmdb_assets ADD COLUMN engagement_id UUID REFERENCES engagements(id);

ALTER TABLE sixr_analyses ADD COLUMN client_account_id UUID REFERENCES client_accounts(id);
ALTER TABLE sixr_analyses ADD COLUMN engagement_id UUID REFERENCES engagements(id);

ALTER TABLE migration_waves ADD COLUMN client_account_id UUID REFERENCES client_accounts(id);
ALTER TABLE migration_waves ADD COLUMN engagement_id UUID REFERENCES engagements(id);

-- Add indexes for performance
CREATE INDEX idx_cmdb_assets_context ON cmdb_assets(client_account_id, engagement_id);
CREATE INDEX idx_sixr_analyses_context ON sixr_analyses(client_account_id, engagement_id);
CREATE INDEX idx_migration_waves_context ON migration_waves(client_account_id, engagement_id);
```

#### Approach 2: Schema-per-Client (Alternative)

Create separate schemas for each client:

```sql
-- Create schema for each client
CREATE SCHEMA client_acme_corp;
CREATE SCHEMA client_global_bank;

-- Tables within each schema
CREATE TABLE client_acme_corp.cmdb_assets (...);
CREATE TABLE client_acme_corp.sixr_analyses (...);
```

**Recommendation**: Use Approach 1 (Context Columns) for better maintainability and simpler queries.

## Backend Implementation

### 1. Context Management Service

```python
# app/services/context_service.py
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

class ContextService:
    """Manages client account and engagement context."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def validate_context(
        self, 
        user_id: str, 
        client_account_id: str, 
        engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate user has access to the specified context."""
        
        # Check client account access
        account_access = self.db.query(UserAccountAssociation).filter(
            UserAccountAssociation.user_id == user_id,
            UserAccountAssociation.client_account_id == client_account_id,
            UserAccountAssociation.status == 'active'
        ).first()
        
        if not account_access:
            raise HTTPException(
                status_code=403, 
                detail="Access denied to client account"
            )
        
        context = {
            "client_account_id": client_account_id,
            "client_account_role": account_access.role,
            "client_account_permissions": account_access.permissions
        }
        
        # Check engagement access if specified
        if engagement_id:
            engagement_access = self.db.query(UserEngagementAssociation).filter(
                UserEngagementAssociation.user_id == user_id,
                UserEngagementAssociation.engagement_id == engagement_id,
                UserEngagementAssociation.status == 'active'
            ).first()
            
            if not engagement_access:
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied to engagement"
                )
            
            context.update({
                "engagement_id": engagement_id,
                "engagement_role": engagement_access.role,
                "engagement_permissions": engagement_access.permissions
            })
        
        return context
    
    async def get_user_contexts(self, user_id: str) -> Dict[str, Any]:
        """Get all contexts (accounts/engagements) user has access to."""
        
        # Get client accounts
        accounts = self.db.query(
            ClientAccount, UserAccountAssociation
        ).join(
            UserAccountAssociation,
            ClientAccount.id == UserAccountAssociation.client_account_id
        ).filter(
            UserAccountAssociation.user_id == user_id,
            UserAccountAssociation.status == 'active',
            ClientAccount.is_active == True
        ).all()
        
        result = []
        for account, association in accounts:
            # Get engagements for this account
            engagements = self.db.query(
                Engagement, UserEngagementAssociation
            ).join(
                UserEngagementAssociation,
                Engagement.id == UserEngagementAssociation.engagement_id
            ).filter(
                UserEngagementAssociation.user_id == user_id,
                Engagement.client_account_id == account.id,
                UserEngagementAssociation.status == 'active',
                Engagement.is_active == True
            ).all()
            
            result.append({
                "client_account": {
                    "id": account.id,
                    "name": account.name,
                    "slug": account.slug,
                    "role": association.role
                },
                "engagements": [
                    {
                        "id": eng.id,
                        "name": eng.name,
                        "slug": eng.slug,
                        "status": eng.status,
                        "role": eng_assoc.role
                    }
                    for eng, eng_assoc in engagements
                ]
            })
        
        return {"contexts": result}
```

### 2. Context Middleware

```python
# app/middleware/context_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.context_service import ContextService

class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and inject context into requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip context validation for auth and health endpoints
        if request.url.path.startswith(('/auth', '/health', '/docs')):
            return await call_next(request)
        
        # Extract context from headers
        client_account_id = request.headers.get('X-Client-Account-ID')
        engagement_id = request.headers.get('X-Engagement-ID')
        
        if not client_account_id:
            raise HTTPException(
                status_code=400, 
                detail="Client account context required"
            )
        
        # Get user from JWT token
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            raise HTTPException(
                status_code=401, 
                detail="Authentication required"
            )
        
        # Validate context
        context_service = ContextService(request.state.db)
        context = await context_service.validate_context(
            user_id, client_account_id, engagement_id
        )
        
        # Inject context into request state
        request.state.context = context
        
        return await call_next(request)
```

### 3. Context-Aware Data Access Layer

```python
# app/repositories/base_repository.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_

class ContextAwareRepository:
    """Base repository with automatic context filtering."""
    
    def __init__(self, db: Session, context: Dict[str, Any]):
        self.db = db
        self.context = context
    
    def apply_context_filter(self, query: Query, model) -> Query:
        """Apply context filtering to a query."""
        
        # Always filter by client account
        if hasattr(model, 'client_account_id'):
            query = query.filter(
                model.client_account_id == self.context['client_account_id']
            )
        
        # Filter by engagement if specified and model supports it
        if (self.context.get('engagement_id') and 
            hasattr(model, 'engagement_id')):
            query = query.filter(
                model.engagement_id == self.context['engagement_id']
            )
        
        return query
    
    def create_with_context(self, model_class, **kwargs):
        """Create a new record with context automatically applied."""
        
        # Inject context
        kwargs['client_account_id'] = self.context['client_account_id']
        if (self.context.get('engagement_id') and 
            hasattr(model_class, 'engagement_id')):
            kwargs['engagement_id'] = self.context['engagement_id']
        
        instance = model_class(**kwargs)
        self.db.add(instance)
        return instance

# Example usage in specific repositories
class CMDBAssetRepository(ContextAwareRepository):
    """Repository for CMDB assets with context awareness."""
    
    def get_all_assets(self) -> List[CMDBAsset]:
        query = self.db.query(CMDBAsset)
        query = self.apply_context_filter(query, CMDBAsset)
        return query.all()
    
    def create_asset(self, **asset_data) -> CMDBAsset:
        return self.create_with_context(CMDBAsset, **asset_data)
```

### 4. Updated API Endpoints

```python
# app/api/v1/endpoints/context.py
from fastapi import APIRouter, Depends, Request
from app.services.context_service import ContextService

router = APIRouter()

@router.get("/contexts")
async def get_user_contexts(request: Request):
    """Get all contexts user has access to."""
    user_id = request.state.user_id
    context_service = ContextService(request.state.db)
    return await context_service.get_user_contexts(user_id)

@router.post("/contexts/validate")
async def validate_context(
    client_account_id: str,
    engagement_id: Optional[str] = None,
    request: Request = None
):
    """Validate user access to specific context."""
    user_id = request.state.user_id
    context_service = ContextService(request.state.db)
    return await context_service.validate_context(
        user_id, client_account_id, engagement_id
    )

# Updated CMDB endpoints with context
@router.post("/cmdb/analyze")
async def analyze_cmdb_data(
    request: CMDBAnalysisRequest,
    context_request: Request
):
    """Analyze CMDB data within current context."""
    context = context_request.state.context
    
    # Create context-aware repository
    cmdb_repo = CMDBAssetRepository(context_request.state.db, context)
    
    # Process analysis with context
    # ... existing logic with context-aware data access
```

## Frontend Implementation

### 1. Context Provider

```typescript
// src/contexts/ClientContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface ClientAccount {
  id: string;
  name: string;
  slug: string;
  role: string;
}

interface Engagement {
  id: string;
  name: string;
  slug: string;
  status: string;
  role: string;
}

interface ClientContextType {
  currentAccount: ClientAccount | null;
  currentEngagement: Engagement | null;
  availableContexts: Array<{
    client_account: ClientAccount;
    engagements: Engagement[];
  }>;
  setCurrentContext: (accountId: string, engagementId?: string) => void;
  isLoading: boolean;
  error: string | null;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

export const ClientContextProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [currentAccount, setCurrentAccount] = useState<ClientAccount | null>(null);
  const [currentEngagement, setCurrentEngagement] = useState<Engagement | null>(null);
  const [availableContexts, setAvailableContexts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load available contexts on mount
  useEffect(() => {
    loadAvailableContexts();
  }, []);

  const loadAvailableContexts = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/contexts');
      const data = await response.json();
      setAvailableContexts(data.contexts);
      
      // Set default context if none selected
      if (!currentAccount && data.contexts.length > 0) {
        const firstAccount = data.contexts[0].client_account;
        const firstEngagement = data.contexts[0].engagements[0];
        setCurrentContext(firstAccount.id, firstEngagement?.id);
      }
    } catch (err) {
      setError('Failed to load available contexts');
    } finally {
      setIsLoading(false);
    }
  };

  const setCurrentContext = async (accountId: string, engagementId?: string) => {
    try {
      // Validate context with backend
      const response = await fetch('/api/v1/contexts/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_account_id: accountId,
          engagement_id: engagementId
        })
      });

      if (!response.ok) {
        throw new Error('Invalid context');
      }

      // Find and set the account
      const accountContext = availableContexts.find(
        ctx => ctx.client_account.id === accountId
      );
      
      if (accountContext) {
        setCurrentAccount(accountContext.client_account);
        
        // Set engagement if specified
        if (engagementId) {
          const engagement = accountContext.engagements.find(
            eng => eng.id === engagementId
          );
          setCurrentEngagement(engagement || null);
        } else {
          setCurrentEngagement(null);
        }

        // Store in localStorage for persistence
        localStorage.setItem('currentContext', JSON.stringify({
          accountId,
          engagementId
        }));
      }
    } catch (err) {
      setError('Failed to set context');
    }
  };

  return (
    <ClientContext.Provider value={{
      currentAccount,
      currentEngagement,
      availableContexts,
      setCurrentContext,
      isLoading,
      error
    }}>
      {children}
    </ClientContext.Provider>
  );
};

export const useClientContext = () => {
  const context = useContext(ClientContext);
  if (!context) {
    throw new Error('useClientContext must be used within ClientContextProvider');
  }
  return context;
};
```

### 2. Context Selector Component

```typescript
// src/components/context/ContextSelector.tsx
import React, { useState } from 'react';
import { useClientContext } from '../../contexts/ClientContext';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../ui/select';
import { Badge } from '../ui/badge';
import { Building2, FolderOpen, ChevronDown } from 'lucide-react';

const ContextSelector: React.FC = () => {
  const { 
    currentAccount, 
    currentEngagement, 
    availableContexts, 
    setCurrentContext 
  } = useClientContext();
  
  const [isOpen, setIsOpen] = useState(false);

  const handleAccountChange = (accountId: string) => {
    const accountContext = availableContexts.find(
      ctx => ctx.client_account.id === accountId
    );
    
    // If account has engagements, select the first one
    const firstEngagement = accountContext?.engagements[0];
    setCurrentContext(accountId, firstEngagement?.id);
  };

  const handleEngagementChange = (engagementId: string) => {
    if (currentAccount) {
      setCurrentContext(currentAccount.id, engagementId);
    }
  };

  return (
    <div className="flex items-center space-x-4 p-4 bg-white border-b">
      {/* Account Selector */}
      <div className="flex items-center space-x-2">
        <Building2 className="h-4 w-4 text-gray-500" />
        <Select value={currentAccount?.id || ''} onValueChange={handleAccountChange}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select client account">
              {currentAccount && (
                <div className="flex items-center space-x-2">
                  <span>{currentAccount.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {currentAccount.role}
                  </Badge>
                </div>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availableContexts.map(({ client_account }) => (
              <SelectItem key={client_account.id} value={client_account.id}>
                <div className="flex items-center space-x-2">
                  <span>{client_account.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {client_account.role}
                  </Badge>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Engagement Selector */}
      {currentAccount && (
        <div className="flex items-center space-x-2">
          <FolderOpen className="h-4 w-4 text-gray-500" />
          <Select 
            value={currentEngagement?.id || ''} 
            onValueChange={handleEngagementChange}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select engagement">
                {currentEngagement && (
                  <div className="flex items-center space-x-2">
                    <span>{currentEngagement.name}</span>
                    <Badge 
                      variant={currentEngagement.status === 'active' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {currentEngagement.status}
                    </Badge>
                  </div>
                )}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {availableContexts
                .find(ctx => ctx.client_account.id === currentAccount.id)
                ?.engagements.map(engagement => (
                  <SelectItem key={engagement.id} value={engagement.id}>
                    <div className="flex items-center space-x-2">
                      <span>{engagement.name}</span>
                      <Badge 
                        variant={engagement.status === 'active' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {engagement.status}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Context Indicator */}
      <div className="flex-1 text-right">
        <div className="text-sm text-gray-600">
          {currentAccount && currentEngagement && (
            <span>
              Working in: <strong>{currentAccount.name}</strong> → <strong>{currentEngagement.name}</strong>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContextSelector;
```

### 3. Context-Aware API Client

```typescript
// src/lib/api/contextAwareClient.ts
import { useClientContext } from '../../contexts/ClientContext';

class ContextAwareAPIClient {
  private baseURL: string;

  constructor(baseURL: string = '/api/v1') {
    this.baseURL = baseURL;
  }

  private getContextHeaders(currentAccount: any, currentEngagement: any) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (currentAccount) {
      headers['X-Client-Account-ID'] = currentAccount.id;
    }

    if (currentEngagement) {
      headers['X-Engagement-ID'] = currentEngagement.id;
    }

    return headers;
  }

  async request(
    endpoint: string, 
    options: RequestInit = {},
    currentAccount: any,
    currentEngagement: any
  ) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      ...this.getContextHeaders(currentAccount, currentEngagement),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Hook for context-aware API calls
export const useContextAwareAPI = () => {
  const { currentAccount, currentEngagement } = useClientContext();
  const client = new ContextAwareAPIClient();

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    return client.request(endpoint, options, currentAccount, currentEngagement);
  };

  return { apiCall };
};
```

### 4. Updated Components

```typescript
// src/pages/discovery/CMDBImport.tsx (Updated)
import React from 'react';
import { useContextAwareAPI } from '../../lib/api/contextAwareClient';
import { useClientContext } from '../../contexts/ClientContext';
import ContextSelector from '../../components/context/ContextSelector';

const CMDBImport: React.FC = () => {
  const { apiCall } = useContextAwareAPI();
  const { currentAccount, currentEngagement } = useClientContext();

  const handleAnalyzeFile = async (fileData: any) => {
    try {
      // API call automatically includes context headers
      const result = await apiCall('/discovery/analyze-cmdb', {
        method: 'POST',
        body: JSON.stringify(fileData)
      });
      
      // Handle result...
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <ContextSelector />
      
      <div className="p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">CMDB Import & Analysis</h1>
          {currentAccount && currentEngagement && (
            <p className="text-gray-600 mt-2">
              Importing data for <strong>{currentEngagement.name}</strong> 
              in <strong>{currentAccount.name}</strong>
            </p>
          )}
        </div>
        
        {/* Rest of component... */}
      </div>
    </div>
  );
};
```

## Security & Access Control

### 1. Role-Based Access Control (RBAC)

#### Client Account Roles

```typescript
enum ClientAccountRole {
  ADMIN = 'admin',        // Full account management
  MANAGER = 'manager',    // Engagement management
  ANALYST = 'analyst',    // Data analysis and reporting
  MEMBER = 'member',      // Basic access
  VIEWER = 'viewer'       // Read-only access
}

const CLIENT_ACCOUNT_PERMISSIONS = {
  [ClientAccountRole.ADMIN]: [
    'account.manage',
    'users.manage',
    'engagements.create',
    'engagements.manage',
    'data.full_access'
  ],
  [ClientAccountRole.MANAGER]: [
    'engagements.create',
    'engagements.manage',
    'users.invite',
    'data.full_access'
  ],
  [ClientAccountRole.ANALYST]: [
    'data.analyze',
    'data.export',
    'reports.create'
  ],
  [ClientAccountRole.MEMBER]: [
    'data.view',
    'data.edit'
  ],
  [ClientAccountRole.VIEWER]: [
    'data.view'
  ]
};
```

#### Engagement Roles

```typescript
enum EngagementRole {
  LEAD = 'lead',          // Engagement leadership
  ANALYST = 'analyst',    // Analysis and planning
  MEMBER = 'member',      // Collaboration
  VIEWER = 'viewer'       // Read-only
}

const ENGAGEMENT_PERMISSIONS = {
  [EngagementRole.LEAD]: [
    'engagement.manage',
    'data.full_access',
    'team.manage',
    'reports.approve'
  ],
  [EngagementRole.ANALYST]: [
    'data.analyze',
    'data.edit',
    'reports.create'
  ],
  [EngagementRole.MEMBER]: [
    'data.view',
    'data.edit'
  ],
  [EngagementRole.VIEWER]: [
    'data.view'
  ]
};
```

### 2. Data Isolation Strategies

#### Database Level
- Row-level security (RLS) policies
- Context-based filtering in all queries
- Audit logging for all data access

#### Application Level
- Middleware validation of context
- Repository pattern with automatic filtering
- API endpoint protection

#### Frontend Level
- Context provider validation
- Component-level access control
- Route protection based on permissions

### 3. Audit Trail

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Context
    client_account_id UUID REFERENCES client_accounts(id),
    engagement_id UUID REFERENCES engagements(id),
    user_id UUID REFERENCES users(id),
    
    -- Action Details
    action VARCHAR(100) NOT NULL, -- create, read, update, delete, export
    resource_type VARCHAR(100) NOT NULL, -- cmdb_asset, sixr_analysis, etc.
    resource_id UUID,
    
    -- Request Details
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Changes (for update/delete actions)
    old_values JSONB,
    new_values JSONB,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_context ON audit_logs(client_account_id, engagement_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## API Design

### 1. Context Headers

All API requests must include context headers:

```
X-Client-Account-ID: uuid
X-Engagement-ID: uuid (optional)
```

### 2. Response Format

All responses include context information:

```json
{
  "data": { /* actual response data */ },
  "context": {
    "client_account_id": "uuid",
    "engagement_id": "uuid",
    "user_permissions": ["data.view", "data.edit"]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### 3. Error Handling

Context-specific error responses:

```json
{
  "error": {
    "code": "CONTEXT_ACCESS_DENIED",
    "message": "Access denied to engagement 'Data Center Migration 2024'",
    "details": {
      "required_permission": "engagement.access",
      "user_role": "viewer",
      "client_account": "Acme Corporation"
    }
  }
}
```

## Migration Strategy

### Phase 1: Database Schema (Week 1)
1. Create new context tables
2. Add context columns to existing tables
3. Create indexes and constraints
4. Set up audit logging

### Phase 2: Backend Implementation (Week 2-3)
1. Implement context service and middleware
2. Update repositories with context awareness
3. Modify API endpoints
4. Add RBAC and permissions

### Phase 3: Frontend Implementation (Week 4-5)
1. Create context provider and components
2. Update API client with context headers
3. Modify existing components
4. Add context selector UI

### Phase 4: Data Migration (Week 6)
1. Migrate existing data to default client account
2. Create initial engagements
3. Assign users to accounts and engagements
4. Validate data integrity

### Phase 5: Testing & Deployment (Week 7-8)
1. Comprehensive testing
2. Performance optimization
3. Security audit
4. Production deployment

## Testing Strategy

### 1. Unit Tests
- Context service validation
- Repository filtering logic
- Permission checking
- Data isolation

### 2. Integration Tests
- End-to-end API workflows
- Context switching scenarios
- Multi-tenant data access
- Security boundary validation

### 3. Performance Tests
- Query performance with context filtering
- Concurrent user scenarios
- Large dataset handling
- Memory usage optimization

### 4. Security Tests
- Data isolation verification
- Permission boundary testing
- SQL injection prevention
- Cross-tenant data leakage

## Implementation Timeline

### Week 1: Foundation
- [ ] Database schema design and implementation
- [ ] Core context models and migrations
- [ ] Basic audit logging setup

### Week 2: Backend Core
- [ ] Context service implementation
- [ ] Middleware development
- [ ] Repository pattern updates
- [ ] RBAC system

### Week 3: Backend APIs
- [ ] API endpoint modifications
- [ ] Context validation
- [ ] Error handling
- [ ] Documentation

### Week 4: Frontend Foundation
- [ ] Context provider implementation
- [ ] Context selector component
- [ ] API client updates
- [ ] Route protection

### Week 5: Frontend Integration
- [ ] Component updates
- [ ] Context-aware data loading
- [ ] User experience improvements
- [ ] Testing integration

### Week 6: Data Migration
- [ ] Migration scripts
- [ ] Data validation
- [ ] Default account setup
- [ ] User assignment

### Week 7: Testing
- [ ] Unit test completion
- [ ] Integration testing
- [ ] Performance testing
- [ ] Security testing

### Week 8: Deployment
- [ ] Production preparation
- [ ] Deployment scripts
- [ ] Monitoring setup
- [ ] Documentation finalization

## Success Metrics

### Technical Metrics
- **Data Isolation**: 100% - No cross-tenant data access
- **Performance**: <200ms API response time with context filtering
- **Security**: Zero security vulnerabilities in audit
- **Reliability**: 99.9% uptime during context operations

### User Experience Metrics
- **Context Switch Time**: <2 seconds
- **User Onboarding**: <5 minutes to first engagement access
- **Error Rate**: <1% context-related errors
- **User Satisfaction**: >90% positive feedback

### Business Metrics
- **Multi-Tenancy Support**: 100+ concurrent client accounts
- **Engagement Scalability**: 1000+ engagements per client
- **User Adoption**: 95% of users successfully using context switching
- **Data Security Compliance**: 100% audit compliance

---

This design provides a comprehensive foundation for implementing client account and engagement segregation across the AI Modernize Migration Platform, ensuring complete data isolation while maintaining a seamless user experience.