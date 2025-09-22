# Frontend Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Vite React Application Structure](#vite-react-application-structure)
3. [Component Architecture](#component-architecture)
4. [State Management](#state-management)
5. [Routing and Navigation](#routing-and-navigation)
6. [UI Components](#ui-components)
7. [HTTP Polling Features](#http-polling-features)
8. [Data Fetching](#data-fetching)
9. [Styling and Theming](#styling-and-theming)
10. [Performance Optimization](#performance-optimization)

## Overview

The frontend is built with Vite + React 18, TypeScript for type safety, and Tailwind CSS for styling. The architecture emphasizes component reusability, type safety, modern React patterns, and advanced lazy loading for optimal performance.

### Key Technologies
- **Vite**: Fast build tool and development server
- **React 18**: Modern React with concurrent features
- **TypeScript**: Type-safe JavaScript development
- **React Router DOM**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **shadcn/ui**: Modern component library built on Radix
- **TanStack Query**: Server state management
- **Zod**: Runtime type validation
- **React Hook Form**: Form state management

Last Updated: 2025-01-22

**IMPORTANT**: This platform uses HTTP polling with TanStack Query instead of WebSockets for Railway deployment compatibility. All API fields use snake_case naming convention.

## Vite React Application Structure

### Project Structure

```
src/
├── components/            # Reusable components
│   ├── ui/               # Base UI components (shadcn/ui)
│   ├── admin/            # Admin-specific components
│   ├── discovery/        # Discovery workflow components
│   ├── collection/       # Collection workflow components
│   ├── assessment/       # Assessment workflow components
│   ├── plan/             # Planning workflow components
│   ├── execute/          # Execution workflow components
│   ├── modernize/        # Modernization workflow components
│   ├── finops/           # FinOps workflow components
│   ├── lazy/             # Lazy loading components and utilities
│   └── shared/           # Shared/common components
├── pages/                # Route components
│   ├── collection/       # Collection workflow pages
│   ├── assessment/       # Assessment workflow pages
│   └── [other-routes]/   # Other route-specific pages
├── contexts/             # React Context providers
│   ├── AuthContext.tsx  # Authentication context
│   ├── ClientContext.tsx # Client/tenant context
│   ├── DialogContext.tsx # Dialog management
│   └── [others].tsx     # Other context providers
├── hooks/                # Custom React hooks
├── services/             # API clients and services
├── utils/                # Utility functions
├── lib/                  # External library configurations
├── types/                # TypeScript type definitions
├── constants/            # Application constants
├── config/               # Configuration files
└── __tests__/            # Test files
```

### Root Application (`src/App.tsx`)

```tsx
import { useState, useEffect } from 'react';
import { Toaster } from '@/components/ui/toaster';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ClientProvider } from './contexts/ClientContext';
import { FieldOptionsProvider } from './contexts/FieldOptionsContext';
import { DialogProvider } from './contexts/DialogContext';
import { ChatFeedbackProvider } from './contexts/ChatFeedbackContext';
import { ErrorBoundary } from './components/ErrorBoundary';

// Lazy Loading Infrastructure
import { LazyLoadingProvider, LoadingPriority } from './components/lazy';
import { routePreloader } from './utils/lazy/routePreloader';

const App = (): JSX.Element => (
  <ErrorBoundary>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <LazyLoadingProvider
        globalOptions={{
          priority: LoadingPriority.NORMAL,
          timeout: 30000,
          retryAttempts: 3,
          cacheStrategy: 'memory',
        }}
      >
        <AuthProvider>
          <ClientProvider>
            <FieldOptionsProvider>
              <DialogProvider>
                <ChatFeedbackProvider>
                  <AuthenticatedApp />
                  <GlobalChatFeedback />
                </ChatFeedbackProvider>
              </DialogProvider>
            </FieldOptionsProvider>
          </ClientProvider>
        </AuthProvider>
      </LazyLoadingProvider>
    </TooltipProvider>
  </ErrorBoundary>
);
```

## Component Architecture

### Component Hierarchy

```
App
├── Layout Components
│   ├── Header
│   ├── Sidebar
│   └── Footer
├── Page Components
│   ├── DiscoveryPage
│   ├── AssessmentPage
│   ├── PlanningPage
│   ├── ExecutionPage
│   ├── ModernizationPage
│   └── FinOpsPage
└── Feature Components
    ├── CMDBUpload
    ├── DataAnalysis
    ├── AgentMonitor
    ├── FeedbackForm
    └── MigrationWaves
```

### Component Structure Example

```tsx
// components/discovery/CMDBUpload.tsx
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { uploadCMDBFile, analyzeCMDBData } from '@/lib/api'

interface CMDBUploadProps {
  onAnalysisComplete: (result: AnalysisResult) => void
  className?: string
}

export function CMDBUpload({ onAnalysisComplete, className }: CMDBUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const { toast } = useToast()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Upload file
      const uploadResult = await uploadCMDBFile(file, (progress) => {
        setUploadProgress(progress)
      })

      // Analyze data
      const analysisResult = await analyzeCMDBData({
        filename: file.name,
        content: uploadResult.content,
        fileType: file.type
      })

      onAnalysisComplete(analysisResult)
      
      toast({
        title: "Analysis Complete",
        description: `Successfully analyzed ${file.name}`,
      })
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }, [onAnalysisComplete, toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1,
    disabled: isUploading
  })

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Upload CMDB Data</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
          } ${isUploading ? 'pointer-events-none opacity-50' : ''}`}
        >
          <input {...getInputProps()} />
          {isUploading ? (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                Uploading and analyzing...
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-lg font-medium">
                {isDragActive ? 'Drop the file here' : 'Drag & drop CMDB file here'}
              </div>
              <div className="text-sm text-muted-foreground">
                Supports CSV, XLS, XLSX files
              </div>
              <Button variant="outline" className="mt-4">
                Browse Files
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Component Best Practices

1. **TypeScript Props**: Always define prop interfaces
2. **Error Boundaries**: Wrap components in error boundaries
3. **Loading States**: Show loading indicators for async operations
4. **Accessibility**: Use semantic HTML and ARIA attributes
5. **Responsive Design**: Mobile-first responsive components

## State Management

### Local State with useState

```tsx
// Simple local state for component-specific data
const [isLoading, setIsLoading] = useState(false)
const [data, setData] = useState<DataType | null>(null)
const [error, setError] = useState<string | null>(null)
```

### HTTP Polling Hooks

```tsx
// hooks/useFlowPolling.ts
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { FlowStatus } from '@/types/flow'

export function useFlowPolling(flow_id: string) {
  const [pollingInterval, setPollingInterval] = useState(5000)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['flow-status', flow_id],
    queryFn: async (): Promise<FlowStatus> => {
      const response = await fetch(`/api/v1/polling/flow-status/${flow_id}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      // Dynamically adjust polling interval based on flow status
      if (result.data?.polling_interval) {
        setPollingInterval(result.data.polling_interval)
      }

      return result.data?.flow_status
    },
    refetchInterval: (data) => {
      // Stop polling if flow is completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false
      }
      return pollingInterval
    },
    enabled: !!flow_id && flow_id !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX',
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return {
    flow_status: data,
    isLoading,
    error,
    refetch,
    pollingInterval,
    isPolling: !isLoading && !error
  }
}

// hooks/useAgentMonitor.ts
import { useQuery } from '@tanstack/react-query'
import { AgentStatus } from '@/types/agent'

export function useAgentMonitor(flow_id: string) {
  return useQuery({
    queryKey: ['agent-monitor', flow_id],
    queryFn: async (): Promise<AgentStatus> => {
      const response = await fetch(`/api/v1/polling/agent-monitor/${flow_id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch agent status')
      }
      return response.json()
    },
    refetchInterval: (data) => {
      // More frequent polling when agents are active
      return data?.agent_status?.active_tasks &&
             Object.keys(data.agent_status.active_tasks).length > 0 ? 3000 : 10000
    },
    enabled: !!flow_id && flow_id !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX'
  })
}
```

### Context for Global State

```tsx
// contexts/MigrationContext.tsx
'use client'

import { createContext, useContext, useReducer, ReactNode } from 'react'

interface MigrationState {
  currentPhase: MigrationPhase
  projects: MigrationProject[]
  selectedProject: MigrationProject | null
}

type MigrationAction = 
  | { type: 'SET_PHASE'; payload: MigrationPhase }
  | { type: 'ADD_PROJECT'; payload: MigrationProject }
  | { type: 'SELECT_PROJECT'; payload: MigrationProject }

const MigrationContext = createContext<{
  state: MigrationState
  dispatch: React.Dispatch<MigrationAction>
} | null>(null)

function migrationReducer(state: MigrationState, action: MigrationAction): MigrationState {
  switch (action.type) {
    case 'SET_PHASE':
      return { ...state, currentPhase: action.payload }
    case 'ADD_PROJECT':
      return { ...state, projects: [...state.projects, action.payload] }
    case 'SELECT_PROJECT':
      return { ...state, selectedProject: action.payload }
    default:
      return state
  }
}

export function MigrationProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(migrationReducer, {
    currentPhase: 'discovery',
    projects: [],
    selectedProject: null
  })

  return (
    <MigrationContext.Provider value={{ state, dispatch }}>
      {children}
    </MigrationContext.Provider>
  )
}

export function useMigration() {
  const context = useContext(MigrationContext)
  if (!context) {
    throw new Error('useMigration must be used within MigrationProvider')
  }
  return context
}
```

## Routing and Navigation

### React Router Implementation

The application uses React Router DOM for client-side routing with intelligent lazy loading:

```tsx
// Key features of the routing system:
// 1. Route-based code splitting with lazy loading
// 2. Priority-based preloading (Critical, High, Normal, Low)
// 3. Hover and viewport-based preloading
// 4. Authentication-aware routing
// 5. Admin route protection

const AuthenticatedApp = (): JSX.Element => {
  const { isLoading, isAuthenticated } = useAuth();
  
  // Setup intelligent route preloading
  useEffect(() => {
    if (isAuthenticated) {
      routePreloader.registerRoute({
        path: '/',
        importFn: () => import('./pages/Index'),
        priority: LoadingPriority.CRITICAL,
      });
      
      routePreloader.setupHoverPreloading();
      routePreloader.setupViewportPreloading();
    }
  }, [isAuthenticated]);
  
  return (
    <Routes>
      {/* CRITICAL PRIORITY ROUTES */}
      <Route path="/" element={<LazyIndex />} />
      <Route path="/discovery" element={<LazyDiscovery />} />
      
      {/* Workflow routes with nested routing */}
      <Route path="/collection/*" element={<CollectionRoutes />} />
      <Route path="/assessment/*" element={<AssessmentRoutes />} />
      
      {/* Admin routes with protection */}
      <Route path="/admin/*" element={
        <AdminRoute>
          <AdminLayout>
            <AdminRoutes />
          </AdminLayout>
        </AdminRoute>
      } />
    </Routes>
  );
};
```

### Navigation Component

```tsx
// components/shared/Sidebar.tsx
import { useLocation, Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const navigationItems = [
  { name: 'Discovery', href: '/discovery', icon: SearchIcon },
  { name: 'Collection', href: '/collection', icon: DatabaseIcon },
  { name: 'Assessment', href: '/assess', icon: ClipboardIcon },
  { name: 'Planning', href: '/plan', icon: CalendarIcon },
  { name: 'Execution', href: '/execute', icon: PlayIcon },
  { name: 'Modernization', href: '/modernize', icon: CogIcon },
  { name: 'FinOps', href: '/finops', icon: DollarSignIcon },
]

export function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-card border-r">
      <div className="p-6">
        <h1 className="text-xl font-bold">AI Modernize Migration</h1>
      </div>
      <nav className="px-4 space-y-2">
        {navigationItems.map((item) => {
          const isActive = location.pathname.startsWith(item.href)
          return (
            <Link key={item.name} to={item.href}>
              <Button
                variant={isActive ? 'default' : 'ghost'}
                className={cn(
                  'w-full justify-start',
                  isActive && 'bg-primary text-primary-foreground'
                )}
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.name}
              </Button>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
```

## UI Components

### shadcn/ui Integration

The project uses shadcn/ui for consistent, accessible components:

```tsx
// components/ui/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

### Custom Components

```tsx
// components/discovery/DataAnalysisResults.tsx
interface DataAnalysisResultsProps {
  analysis: AnalysisResult
  onFeedback: (feedback: FeedbackData) => void
}

export function DataAnalysisResults({ analysis, onFeedback }: DataAnalysisResultsProps) {
  const [feedbackOpen, setFeedbackOpen] = useState(false)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Analysis Results
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFeedbackOpen(true)}
          >
            Provide Feedback
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Asset Type Detection */}
        <div>
          <h3 className="font-medium mb-2">Asset Type Detected</h3>
          <Badge variant="secondary">{analysis.asset_type_detected}</Badge>
          <div className="text-sm text-muted-foreground mt-1">
            Confidence: {(analysis.confidence_level * 100).toFixed(1)}%
          </div>
        </div>

        {/* Data Quality Score */}
        <div>
          <h3 className="font-medium mb-2">Data Quality Score</h3>
          <div className="flex items-center space-x-2">
            <Progress value={analysis.data_quality_score} className="flex-1" />
            <span className="text-sm font-medium">
              {analysis.data_quality_score}/100
            </span>
          </div>
        </div>

        {/* Missing Fields */}
        {analysis.missing_fields_relevant?.length > 0 && (
          <div>
            <h3 className="font-medium mb-2">Missing Fields</h3>
            <div className="flex flex-wrap gap-2">
              {analysis.missing_fields_relevant.map((field) => (
                <Badge key={field} variant="destructive">
                  {field}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        <div>
          <h3 className="font-medium mb-2">Recommendations</h3>
          <ul className="space-y-1">
            {analysis.recommendations?.map((rec, index) => (
              <li key={index} className="text-sm text-muted-foreground">
                • {rec}
              </li>
            ))}
          </ul>
        </div>
      </CardContent>

      {/* Feedback Dialog */}
      <FeedbackDialog
        open={feedbackOpen}
        onOpenChange={setFeedbackOpen}
        analysis={analysis}
        onSubmit={onFeedback}
      />
    </Card>
  )
}
```

## HTTP Polling Features

### TanStack Query Polling Integration

**IMPORTANT**: The platform uses HTTP polling instead of WebSockets for Railway deployment compatibility.

```tsx
// components/monitoring/AgentMonitor.tsx
import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export function AgentMonitor({ flow_id }: { flow_id: string }) {
  const [pollingInterval, setPollingInterval] = useState(5000) // Default 5 seconds

  // HTTP Polling with TanStack Query
  const { data: status, isLoading, error, refetch } = useQuery({
    queryKey: ['agent-status', flow_id],
    queryFn: async () => {
      const response = await fetch(`/api/v1/polling/agent-monitor/${flow_id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch agent status')
      }
      const result = await response.json()

      // Update polling interval based on response
      setPollingInterval(result.polling_interval || 5000)

      return result
    },
    refetchInterval: pollingInterval,
    enabled: !!flow_id && flow_id !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX'
  })

  const handleManualRefresh = async () => {
    await refetch()
  }

  const agent_status = status?.agent_status
  const isPolling = !isLoading && !error

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Agent Monitor</CardTitle>
        <div className="flex items-center space-x-2">
          <Badge variant={isPolling ? 'default' : 'destructive'}>
            {isPolling ? `Polling (${pollingInterval / 1000}s)` : 'Disconnected'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={handleManualRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="text-center text-destructive mb-4">
            Error: {error.message}
          </div>
        )}
        {agent_status ? (
          <div className="space-y-4">
            {/* Active Tasks */}
            <div>
              <h3 className="font-medium mb-2">Active Tasks</h3>
              {Object.entries(agent_status.active_tasks || {}).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(agent_status.active_tasks).map(([taskId, task]) => (
                    <div key={taskId} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <div className="font-medium">{task.agent_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {task.description.substring(0, 50)}...
                        </div>
                      </div>
                      <Badge variant="secondary">{task.status}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">No active tasks</div>
              )}
            </div>

            {/* Recent Tasks */}
            <div>
              <h3 className="font-medium mb-2">Recent Tasks</h3>
              {agent_status.task_history?.slice(0, 5).map((task) => (
                <div key={task.task_id} className="flex items-center justify-between p-2 border rounded mb-2">
                  <div>
                    <div className="font-medium">{task.agent_name}</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(task.start_time).toLocaleTimeString()}
                    </div>
                  </div>
                  <Badge variant={task.status === 'completed' ? 'default' : 'destructive'}>
                    {task.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground">
            {isLoading ? 'Loading agent status...' : 'No agent status available'}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

## Data Fetching

### API Client

```tsx
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // CMDB Analysis
  async analyzeCMDBData(data: CMDBAnalysisRequest): Promise<CMDBAnalysisResponse> {
    return this.request<CMDBAnalysisResponse>('/discovery/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Feedback Processing
  async processFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
    return this.request<FeedbackResponse>('/feedback/process', {
      method: 'POST',
      body: JSON.stringify(feedback),
    })
  }

  // Migration Management
  async createMigration(migration: MigrationCreateRequest): Promise<Migration> {
    return this.request<Migration>('/migrations', {
      method: 'POST',
      body: JSON.stringify(migration),
    })
  }

  async getMigrations(): Promise<Migration[]> {
    return this.request<Migration[]>('/migrations')
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
```

### Advanced Lazy Loading System

The application implements a sophisticated lazy loading system with intelligent preloading:

```tsx
// utils/lazy/routePreloader.ts
export enum LoadingPriority {
  CRITICAL = 0,  // Load immediately
  HIGH = 1,      // Preload on app init
  NORMAL = 2,    // Load on hover/viewport
  LOW = 3        // Load on demand only
}

class RoutePreloader {
  private routes = new Map<string, RouteConfig>();
  private loadedModules = new Map<string, any>();
  
  registerRoute(config: RouteConfig) {
    this.routes.set(config.path, config);
    
    // Immediately preload critical routes
    if (config.priority === LoadingPriority.CRITICAL) {
      this.preloadRoute(config.path);
    }
  }
  
  setupHoverPreloading() {
    // Preload routes when user hovers over navigation links
    document.addEventListener('mouseover', (e) => {
      const link = e.target.closest('a[href]');
      if (link) {
        const path = link.getAttribute('href');
        this.preloadRoute(path);
      }
    });
  }
  
  setupViewportPreloading() {
    // Preload routes for visible navigation items
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const link = entry.target.querySelector('a[href]');
          if (link) {
            const path = link.getAttribute('href');
            this.preloadRoute(path);
          }
        }
      });
    });
    
    // Observe navigation items
    document.querySelectorAll('nav').forEach(nav => {
      observer.observe(nav);
    });
  }
}
```

### Data Fetching Hooks

```tsx
// hooks/useAnalysis.ts
import { useState, useCallback } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export function useAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const analyzeData = useCallback(async (data: CMDBAnalysisRequest) => {
    setIsAnalyzing(true)
    setError(null)

    try {
      const result = await apiClient.analyzeCMDBData(data)
      setAnalysis(result)
      
      toast({
        title: "Analysis Complete",
        description: `Successfully analyzed ${data.filename}`,
      })
      
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed'
      setError(errorMessage)
      
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        variant: "destructive",
      })
      
      throw err
    } finally {
      setIsAnalyzing(false)
    }
  }, [toast])

  const clearAnalysis = useCallback(() => {
    setAnalysis(null)
    setError(null)
  }, [])

  return {
    isAnalyzing,
    analysis,
    error,
    analyzeData,
    clearAnalysis
  }
}
```

## Styling and Theming

### Vite Configuration

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          utils: ['clsx', 'tailwind-merge', 'class-variance-authority'],
        },
      },
    },
  },
  server: {
    port: 8081, // Docker development port (NOT 3000)
    host: true,
  },
})
```

### Tailwind Configuration

```js
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

### CSS Variables

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 84% 4.9%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 94.1%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

## Performance Optimization

### Advanced Code Splitting with Lazy Loading

The application uses a sophisticated lazy loading system with priority-based preloading:

```tsx
// components/lazy/index.ts
import { lazy } from 'react';
import { withLazyLoading } from './LazyLoadingProvider';

// Critical priority - loaded immediately
export const LazyIndex = withLazyLoading(
  lazy(() => import('@/pages/Index')),
  { priority: LoadingPriority.CRITICAL }
);

// High priority - preloaded on app init
export const LazyDiscovery = withLazyLoading(
  lazy(() => import('@/pages/Discovery')),
  { priority: LoadingPriority.HIGH }
);

// Normal priority - loaded on hover/viewport
export const LazyAssess = withLazyLoading(
  lazy(() => import('@/pages/Assess')),
  { priority: LoadingPriority.NORMAL }
);

// Low priority - loaded on demand only
export const LazyFinOps = withLazyLoading(
  lazy(() => import('@/pages/FinOps')),
  { priority: LoadingPriority.LOW }
);
```

### Intelligent Route Preloading

```tsx
// Features:
// 1. Hover-based preloading
// 2. Viewport-based preloading
// 3. Priority-based loading
// 4. Route dependency tracking
// 5. Memory-based caching

const routePreloader = {
  setupHoverPreloading() {
    // Preload routes when hovering over navigation
  },
  
  setupViewportPreloading() {
    // Preload visible route components
  },
  
  preloadFromCurrentLocation(pathname: string) {
    // Intelligently preload likely next routes
  }
};
```

### Memoization

```tsx
// Memoize expensive calculations
const MigrationWaveChart = memo(({ data }: { data: WaveData[] }) => {
  const chartData = useMemo(() => {
    return data.map(wave => ({
      ...wave,
      totalAssets: wave.assets.length,
      estimatedDuration: calculateDuration(wave.assets)
    }))
  }, [data])

  return <Chart data={chartData} />
})
```

### Image Optimization

```tsx
import Image from 'next/image'

// Optimized images with Next.js Image component
<Image
  src="/migration-diagram.png"
  alt="Migration Architecture"
  width={800}
  height={600}
  priority
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
```

This frontend architecture provides a modern, scalable, and maintainable foundation for the AI Modernize Migration Platform with excellent developer experience and user interface. 