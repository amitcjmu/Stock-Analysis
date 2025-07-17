# Frontend Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Next.js Application Structure](#nextjs-application-structure)
3. [Component Architecture](#component-architecture)
4. [State Management](#state-management)
5. [Routing and Navigation](#routing-and-navigation)
6. [UI Components](#ui-components)
7. [Real-time Features](#real-time-features)
8. [Data Fetching](#data-fetching)
9. [Styling and Theming](#styling-and-theming)
10. [Performance Optimization](#performance-optimization)

## Overview

The frontend is built with Next.js 14 using the App Router, TypeScript for type safety, and Tailwind CSS for styling. The architecture emphasizes component reusability, type safety, and modern React patterns.

### Key Technologies
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern component library
- **React Hooks**: State management and lifecycle
- **WebSocket**: Real-time communication

## Next.js Application Structure

### App Router Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── globals.css        # Global styles
│   └── (routes)/          # Route groups
│       ├── discovery/     # Discovery phase routes
│       ├── assess/        # Assessment phase routes
│       ├── plan/          # Planning phase routes
│       ├── execute/       # Execution phase routes
│       ├── modernize/     # Modernization phase routes
│       └── finops/        # FinOps phase routes
├── components/            # Reusable components
│   ├── ui/               # Base UI components
│   ├── discovery/        # Discovery-specific components
│   ├── layout/           # Layout components
│   └── common/           # Common components
├── hooks/                # Custom React hooks
├── lib/                  # Utility libraries
├── config/               # Configuration files
└── types/                # TypeScript type definitions
```

### Root Layout (`app/layout.tsx`)

```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Modernize Migration Platform',
  description: 'Intelligent cloud migration orchestration platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
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
'use client'

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

### Custom Hooks for Shared State

```tsx
// hooks/useAgentMonitor.ts
import { useState, useEffect, useRef } from 'react'
import { AgentStatus, TaskStatus } from '@/types/agent'

export function useAgentMonitor() {
  const [status, setStatus] = useState<AgentStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/agent-monitor`)
    
    ws.onopen = () => {
      setIsConnected(true)
      console.log('Agent monitor connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setStatus(data)
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('Agent monitor disconnected')
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    wsRef.current = ws
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    status,
    isConnected,
    connect,
    disconnect
  }
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

### App Router Structure

```tsx
// app/(dashboard)/layout.tsx
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

### Navigation Component

```tsx
// components/layout/Sidebar.tsx
'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const navigationItems = [
  { name: 'Discovery', href: '/discovery', icon: SearchIcon },
  { name: 'Assessment', href: '/assess', icon: ClipboardIcon },
  { name: 'Planning', href: '/plan', icon: CalendarIcon },
  { name: 'Execution', href: '/execute', icon: PlayIcon },
  { name: 'Modernization', href: '/modernize', icon: CogIcon },
  { name: 'FinOps', href: '/finops', icon: DollarSignIcon },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-card border-r">
      <div className="p-6">
        <h1 className="text-xl font-bold">AI Modernize Migration</h1>
      </div>
      <nav className="px-4 space-y-2">
        {navigationItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link key={item.name} href={item.href}>
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

## Real-time Features

### WebSocket Integration

```tsx
// components/monitoring/AgentMonitor.tsx
'use client'

import { useAgentMonitor } from '@/hooks/useAgentMonitor'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export function AgentMonitor() {
  const { status, isConnected, connect, disconnect } = useAgentMonitor()
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // Fetch latest status
      const response = await fetch('/api/v1/monitoring/agent-status')
      const latestStatus = await response.json()
      // Update status would be handled by the hook
    } catch (error) {
      console.error('Failed to refresh agent status:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Agent Monitor</CardTitle>
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? 'default' : 'destructive'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {status ? (
          <div className="space-y-4">
            {/* Active Tasks */}
            <div>
              <h3 className="font-medium mb-2">Active Tasks</h3>
              {Object.entries(status.active_tasks).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(status.active_tasks).map(([taskId, task]) => (
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
              {status.task_history?.slice(0, 5).map((task) => (
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
            No agent status available
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

### Data Fetching Hooks

```tsx
// hooks/useAnalysis.ts
import { useState, useCallback } from 'react'
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

### Tailwind Configuration

```js
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
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

### Code Splitting

```tsx
// Dynamic imports for large components
import dynamic from 'next/dynamic'

const DataVisualization = dynamic(
  () => import('@/components/discovery/DataVisualization'),
  {
    loading: () => <div>Loading visualization...</div>,
    ssr: false
  }
)

const AgentMonitor = dynamic(
  () => import('@/components/monitoring/AgentMonitor'),
  {
    loading: () => <div>Loading agent monitor...</div>
  }
)
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