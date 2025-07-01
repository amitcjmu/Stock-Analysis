# AI Coding Agent 4: Frontend UI Implementation

## Agent Overview
You are responsible for creating the React/TypeScript frontend for the Assessment Flow feature. This includes creating pages, components, hooks, and services that provide an intuitive user interface for the assessment process.

## Context

### Project Overview
The Assessment Flow UI guides users through:
1. Selecting applications from the inventory
2. Viewing architecture verification results
3. Reviewing technical debt analysis
4. Reviewing and potentially overriding 6R strategy recommendations
5. Viewing the final assessment summary

### Technical Stack
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **State Management**: React hooks (useState, useEffect, custom hooks)
- **UI Components**: Shadcn/ui components
- **API Client**: Axios with interceptors
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

### UI/UX Principles
- Clean, professional interface matching existing design
- Real-time status updates during flow execution
- Clear data visualization for analysis results
- Intuitive override interface with rationale capture
- Responsive design for various screen sizes

## Your Assigned Tasks

### ⚛️ Frontend Tasks

#### FE-001: Create useAssessmentFlow Hook
**Priority**: P0 - Critical  
**Effort**: 6 hours  
**Location**: `src/hooks/useAssessmentFlow.ts`

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentService } from '@/services/assessmentService';
import { 
  AssessmentFlowStatus,
  AssessmentFlowPhase,
  ArchitectureRequirement,
  TechDebtAnalysis,
  SixRDecision,
  AssessmentFlowState
} from '@/types/assessment';

interface UseAssessmentFlowOptions {
  flowId?: string;
  pollingInterval?: number;
}

interface UseAssessmentFlowReturn {
  // Flow state
  flowId: string | null;
  status: AssessmentFlowStatus | null;
  progress: number;
  currentPhase: AssessmentFlowPhase | null;
  error: Error | null;
  isLoading: boolean;
  
  // Flow control
  initializeFlow: (discoveryFlowId: string, selectedAppIds: string[]) => Promise<void>;
  executePhase: (phase: AssessmentFlowPhase) => Promise<void>;
  finalizeAssessment: () => Promise<void>;
  
  // Data access
  architectureRequirements: ArchitectureRequirement[];
  techDebtAnalysis: TechDebtAnalysis | null;
  sixrDecisions: SixRDecision[];
  
  // User actions
  verifyRequirement: (reqId: string, status: string, notes?: string) => Promise<void>;
  overrideSixRDecision: (appId: string, strategy: string, reason: string) => Promise<void>;
  
  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
}

export const useAssessmentFlow = (
  options: UseAssessmentFlowOptions = {}
): UseAssessmentFlowReturn => {
  const { flowId: initialFlowId, pollingInterval = 5000 } = options;
  const navigate = useNavigate();
  
  // State management
  const [flowId, setFlowId] = useState<string | null>(initialFlowId || null);
  const [status, setStatus] = useState<AssessmentFlowStatus | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentPhase, setCurrentPhase] = useState<AssessmentFlowPhase | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Data state
  const [architectureRequirements, setArchitectureRequirements] = useState<ArchitectureRequirement[]>([]);
  const [techDebtAnalysis, setTechDebtAnalysis] = useState<TechDebtAnalysis | null>(null);
  const [sixrDecisions, setSixrDecisions] = useState<SixRDecision[]>([]);
  
  // Polling ref
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize flow
  const initializeFlow = useCallback(async (
    discoveryFlowId: string, 
    selectedAppIds: string[]
  ) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await assessmentService.initializeFlow({
        discovery_flow_id: discoveryFlowId,
        selected_application_ids: selectedAppIds,
        engagement_id: 1 // Get from context
      });
      
      setFlowId(response.flow_id);
      setStatus(response.status);
      setProgress(response.progress);
      
      // Navigate to first phase
      navigate(`/assessment/architecture?flow_id=${response.flow_id}`);
      
      // Start polling for updates
      subscribeToUpdates();
      
    } catch (err) {
      setError(err as Error);
      console.error('Failed to initialize assessment flow:', err);
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);
  
  // Fetch flow status
  const fetchFlowStatus = useCallback(async () => {
    if (!flowId) return;
    
    try {
      const statusData = await assessmentService.getFlowStatus(flowId);
      
      setStatus(statusData.status);
      setProgress(statusData.progress);
      setCurrentPhase(statusData.current_phase);
      
      // Fetch phase-specific data based on current phase
      if (statusData.current_phase === 'architecture_verification') {
        const reqs = await assessmentService.getArchitectureRequirements(flowId);
        setArchitectureRequirements(reqs);
      } else if (statusData.current_phase === 'tech_debt_analysis') {
        const analysis = await assessmentService.getTechDebtAnalysis(flowId);
        setTechDebtAnalysis(analysis);
      } else if (statusData.current_phase === 'sixr_strategy' || 
                 statusData.current_phase === 'collaborative_review') {
        const decisions = await assessmentService.getSixRDecisions(flowId);
        setSixrDecisions(decisions);
      }
      
    } catch (err) {
      console.error('Failed to fetch flow status:', err);
    }
  }, [flowId]);
  
  // Execute flow phase
  const executePhase = useCallback(async (phase: AssessmentFlowPhase) => {
    if (!flowId) {
      throw new Error('No flow ID available');
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      await assessmentService.executePhase(flowId, phase);
      await fetchFlowStatus();
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [flowId, fetchFlowStatus]);
  
  // Verify architecture requirement
  const verifyRequirement = useCallback(async (
    reqId: string,
    verificationStatus: string,
    notes?: string
  ) => {
    if (!flowId) return;
    
    try {
      await assessmentService.updateArchitectureVerification(
        flowId,
        reqId,
        { verification_status: verificationStatus, notes }
      );
      
      // Update local state
      setArchitectureRequirements(prev => 
        prev.map(req => 
          req.id === reqId 
            ? { ...req, verification_status: verificationStatus }
            : req
        )
      );
    } catch (err) {
      console.error('Failed to verify requirement:', err);
      throw err;
    }
  }, [flowId]);
  
  // Override 6R decision
  const overrideSixRDecision = useCallback(async (
    appId: string,
    strategy: string,
    reason: string
  ) => {
    if (!flowId) return;
    
    try {
      await assessmentService.overrideSixRDecision(flowId, appId, {
        override_strategy: strategy,
        override_reason: reason
      });
      
      // Update local state
      setSixrDecisions(prev =>
        prev.map(decision =>
          decision.application_id === appId
            ? { 
                ...decision, 
                user_override_strategy: strategy,
                override_reason: reason 
              }
            : decision
        )
      );
    } catch (err) {
      console.error('Failed to override decision:', err);
      throw err;
    }
  }, [flowId]);
  
  // Finalize assessment
  const finalizeAssessment = useCallback(async () => {
    if (!flowId) return;
    
    setIsLoading(true);
    
    try {
      const result = await assessmentService.finalizeAssessment(flowId);
      setStatus('completed');
      setProgress(100);
      
      // Navigate to summary
      navigate(`/assessment/summary?flow_id=${flowId}`);
      
      // Stop polling
      unsubscribeFromUpdates();
      
      return result;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [flowId, navigate]);
  
  // Subscribe to updates (polling)
  const subscribeToUpdates = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    
    pollingRef.current = setInterval(() => {
      fetchFlowStatus();
    }, pollingInterval);
  }, [fetchFlowStatus, pollingInterval]);
  
  // Unsubscribe from updates
  const unsubscribeFromUpdates = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);
  
  // Load initial data if flowId provided
  useEffect(() => {
    if (flowId) {
      fetchFlowStatus();
      subscribeToUpdates();
    }
    
    return () => {
      unsubscribeFromUpdates();
    };
  }, [flowId, fetchFlowStatus, subscribeToUpdates, unsubscribeFromUpdates]);
  
  return {
    // Flow state
    flowId,
    status,
    progress,
    currentPhase,
    error,
    isLoading,
    
    // Flow control
    initializeFlow,
    executePhase,
    finalizeAssessment,
    
    // Data access
    architectureRequirements,
    techDebtAnalysis,
    sixrDecisions,
    
    // User actions
    verifyRequirement,
    overrideSixRDecision,
    
    // Real-time updates
    subscribeToUpdates,
    unsubscribeFromUpdates
  };
};
```

#### FE-002: Create Assessment Types
**Priority**: P1 - High  
**Effort**: 2 hours  
**Location**: `src/types/assessment.ts`

```typescript
export enum AssessmentFlowStatus {
  INITIALIZED = 'initialized',
  IN_PROGRESS = 'in_progress',
  AWAITING_REVIEW = 'awaiting_review',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum AssessmentFlowPhase {
  INITIALIZATION = 'initialization',
  ARCHITECTURE_VERIFICATION = 'architecture_verification',
  TECH_DEBT_ANALYSIS = 'tech_debt_analysis',
  SIXR_STRATEGY = 'sixr_strategy',
  COLLABORATIVE_REVIEW = 'collaborative_review',
  FINALIZED = 'finalized'
}

export enum SixRStrategy {
  REHOST = 'rehost',
  REPLATFORM = 'replatform',
  REFACTOR = 'refactor',
  REPURCHASE = 'repurchase',
  RETIRE = 'retire',
  RETAIN = 'retain'
}

export enum TechDebtSeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export interface AssessmentFlowState {
  flow_id: string;
  discovery_flow_id: string;
  status: AssessmentFlowStatus;
  progress: number;
  current_phase: AssessmentFlowPhase;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ArchitectureRequirement {
  id: string;
  type: string;
  description: string;
  mandatory: boolean;
  verification_status: 'pending' | 'verified' | 'failed';
  verified_at?: string;
  notes?: string;
}

export interface TechDebtItem {
  category: string;
  severity: TechDebtSeverity;
  description: string;
  remediation_effort_hours: number;
  impact_on_migration: string;
}

export interface TechDebtAnalysis {
  applications: {
    [appId: string]: {
      overall_score: number;
      items: TechDebtItem[];
    };
  };
}

export interface SixRDecision {
  application_id: string;
  application_name: string;
  recommended_strategy: SixRStrategy;
  confidence_score: number;
  rationale: string;
  risk_factors: string[];
  estimated_effort_hours: number;
  estimated_cost: number;
  user_override_strategy?: SixRStrategy;
  override_reason?: string;
  override_by?: string;
  override_at?: string;
}

export interface AssessmentSummary {
  total_applications: number;
  strategy_distribution: {
    [key in SixRStrategy]?: number;
  };
  user_overrides: number;
  completion_time: string;
}
```

#### FE-003: Create Assessment Service Layer
**Priority**: P1 - High  
**Effort**: 4 hours  
**Location**: `src/services/assessmentService.ts`

```typescript
import axios from '@/lib/axios';
import { 
  AssessmentFlowState,
  ArchitectureRequirement,
  TechDebtAnalysis,
  SixRDecision,
  AssessmentSummary
} from '@/types/assessment';

const API_BASE = '/api/v3/assessment-flow';

export const assessmentService = {
  // Initialize assessment flow
  async initializeFlow(data: {
    discovery_flow_id: string;
    selected_application_ids: string[];
    engagement_id: number;
  }) {
    const response = await axios.post(`${API_BASE}/initialize`, data);
    return response.data;
  },
  
  // Get flow status
  async getFlowStatus(flowId: string): Promise<AssessmentFlowState> {
    const response = await axios.get(`${API_BASE}/${flowId}/status`);
    return response.data;
  },
  
  // Execute flow phase
  async executePhase(flowId: string, phase: string, phaseInput?: any) {
    const response = await axios.post(
      `${API_BASE}/${flowId}/execute/${phase}`,
      phaseInput || {}
    );
    return response.data;
  },
  
  // Get architecture requirements
  async getArchitectureRequirements(flowId: string): Promise<ArchitectureRequirement[]> {
    const response = await axios.get(`${API_BASE}/${flowId}/architecture-requirements`);
    return response.data;
  },
  
  // Update architecture verification
  async updateArchitectureVerification(
    flowId: string,
    reqId: string,
    data: { verification_status: string; notes?: string }
  ) {
    const response = await axios.put(
      `${API_BASE}/${flowId}/architecture-requirements/${reqId}`,
      data
    );
    return response.data;
  },
  
  // Get tech debt analysis
  async getTechDebtAnalysis(flowId: string): Promise<TechDebtAnalysis> {
    const response = await axios.get(`${API_BASE}/${flowId}/tech-debt`);
    return response.data;
  },
  
  // Get 6R decisions
  async getSixRDecisions(flowId: string): Promise<SixRDecision[]> {
    const response = await axios.get(`${API_BASE}/${flowId}/sixr-decisions`);
    return response.data;
  },
  
  // Override 6R decision
  async overrideSixRDecision(
    flowId: string,
    appId: string,
    data: { override_strategy: string; override_reason: string }
  ) {
    const response = await axios.put(
      `${API_BASE}/${flowId}/sixr-decisions/${appId}`,
      data
    );
    return response.data;
  },
  
  // Finalize assessment
  async finalizeAssessment(flowId: string): Promise<AssessmentSummary> {
    const response = await axios.post(`${API_BASE}/${flowId}/finalize`);
    return response.data;
  },
  
  // Get assessment report
  async getAssessmentReport(flowId: string, format: string = 'json') {
    const response = await axios.get(
      `${API_BASE}/${flowId}/report?format=${format}`
    );
    return response.data;
  }
};
```

#### FE-004: Create Application Selection Page
**Priority**: P1 - High  
**Effort**: 8 hours  
**Location**: `src/pages/assessment/initialize.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowRight, Server } from 'lucide-react';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { unifiedDiscoveryService } from '@/services/unifiedDiscoveryService';
import { AssetInventory } from '@/types/discovery';

export default function AssessmentInitializePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const discoveryFlowId = searchParams.get('discovery_flow_id');
  
  const { initializeFlow, isLoading, error } = useAssessmentFlow();
  
  const [applications, setApplications] = useState<AssetInventory[]>([]);
  const [selectedAppIds, setSelectedAppIds] = useState<string[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);
  
  // Load applications from discovery flow
  useEffect(() => {
    if (!discoveryFlowId) {
      navigate('/discovery/inventory');
      return;
    }
    
    const loadApplications = async () => {
      try {
        const assets = await unifiedDiscoveryService.getFlowAssets(discoveryFlowId);
        // Filter only applications
        const apps = assets.filter(asset => asset.asset_type === 'Application');
        setApplications(apps);
      } catch (err) {
        console.error('Failed to load applications:', err);
      } finally {
        setLoadingApps(false);
      }
    };
    
    loadApplications();
  }, [discoveryFlowId, navigate]);
  
  // Handle application selection
  const handleSelectApp = (appId: string) => {
    setSelectedAppIds(prev =>
      prev.includes(appId)
        ? prev.filter(id => id !== appId)
        : [...prev, appId]
    );
  };
  
  // Handle select all
  const handleSelectAll = () => {
    if (selectedAppIds.length === applications.length) {
      setSelectedAppIds([]);
    } else {
      setSelectedAppIds(applications.map(app => app.id));
    }
  };
  
  // Start assessment
  const handleStartAssessment = async () => {
    if (!discoveryFlowId || selectedAppIds.length === 0) return;
    
    try {
      await initializeFlow(discoveryFlowId, selectedAppIds);
    } catch (err) {
      console.error('Failed to start assessment:', err);
    }
  };
  
  if (loadingApps) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading applications...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Initialize Assessment</h1>
        <p className="text-gray-600">
          Select applications to assess for migration strategy
        </p>
      </div>
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700">{error.message}</p>
          </div>
        </div>
      )}
      
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Select Applications</CardTitle>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {selectedAppIds.length} of {applications.length} selected
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
              >
                {selectedAppIds.length === applications.length ? 'Deselect All' : 'Select All'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {applications.map((app) => (
              <div
                key={app.id}
                className={`p-4 border rounded-lg transition-colors cursor-pointer hover:bg-gray-50 ${
                  selectedAppIds.includes(app.id) ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => handleSelectApp(app.id)}
              >
                <div className="flex items-start gap-4">
                  <Checkbox
                    checked={selectedAppIds.includes(app.id)}
                    onCheckedChange={() => handleSelectApp(app.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Server className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium">{app.asset_name}</h3>
                      <Badge variant="outline" className="text-xs">
                        {app.environment || 'Unknown'}
                      </Badge>
                      {app.business_criticality === 'Critical' && (
                        <Badge variant="destructive" className="text-xs">
                          Critical
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      {app.operating_system || 'Unknown OS'} • 
                      Dependencies: {app.dependencies || 'None identified'}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>Risk Score: {app.risk_score || 'N/A'}</span>
                      <span>Readiness: {Math.round((app.migration_readiness || 0) * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => navigate(`/discovery/inventory?flow_id=${discoveryFlowId}`)}
        >
          Back to Inventory
        </Button>
        <Button
          onClick={handleStartAssessment}
          disabled={selectedAppIds.length === 0 || isLoading}
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Starting Assessment...
            </>
          ) : (
            <>
              Start Assessment
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
```

#### FE-005: Create Architecture Verification Page
**Priority**: P1 - High  
**Effort**: 6 hours  
**Location**: `src/pages/assessment/architecture.tsx`

Create page for reviewing and verifying architecture requirements.

#### FE-006: Create Tech Debt Analysis Page
**Priority**: P1 - High  
**Effort**: 8 hours  
**Location**: `src/pages/assessment/tech-debt.tsx`

Create visualization for tech debt analysis results.

#### FE-007: Create 6R Review Page
**Priority**: P1 - High  
**Effort**: 10 hours  
**Location**: `src/pages/assessment/sixr-review.tsx`

Create the most complex page for reviewing and overriding 6R decisions.

#### FE-008: Create Assessment Summary Page
**Priority**: P1 - High  
**Effort**: 6 hours  
**Location**: `src/pages/assessment/summary.tsx`

Create final summary page with report generation.

#### FE-009: Update Navigation for Assessment Flow
**Priority**: P2 - Medium  
**Effort**: 2 hours  
**Location**: `src/components/navigation/MainNav.tsx`

Add assessment flow to navigation menu.

#### MIG-002: Update Inventory Page Navigation
**Priority**: P1 - High  
**Effort**: 3 hours  
**Location**: `src/pages/discovery/inventory.tsx`

Add "Continue to Assessment" button that passes selected applications.

## Development Guidelines

### Component Structure
```typescript
// Follow this pattern for all pages
import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function AssessmentPageName() {
  const [searchParams] = useSearchParams();
  const flowId = searchParams.get('flow_id');
  
  const {
    // Destructure what you need
    status,
    progress,
    currentPhase,
    // ... other hook values
  } = useAssessmentFlow({ flowId: flowId || undefined });
  
  // Component logic
  
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Page content */}
    </div>
  );
}
```

### UI Components to Use
- Cards for grouping related content
- Badges for status indicators
- Progress bars for flow progress
- Tables for data display
- Alert dialogs for confirmations
- Toasts for success/error messages

### State Management
- Use the custom hook for all assessment flow state
- Local state only for UI-specific needs
- Avoid prop drilling - use context if needed

### Error Handling
```typescript
// Display errors consistently
{error && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{error.message}</AlertDescription>
  </Alert>
)}
```

### Loading States
```typescript
// Consistent loading indicators
if (isLoading) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 animate-spin" />
    </div>
  );
}
```

### Testing Your Implementation
```bash
# Run development server
npm run dev

# Run component tests
npm test

# Run E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

### Responsive Design
- Use Tailwind responsive prefixes
- Test on mobile, tablet, and desktop
- Ensure tables are scrollable on mobile
- Use appropriate touch targets

### Performance Optimization
- Lazy load heavy components
- Memoize expensive calculations
- Use virtualization for long lists
- Optimize re-renders with React.memo

## Completion Checklist
- [ ] FE-001: useAssessmentFlow hook complete
- [ ] FE-002: TypeScript types defined
- [ ] FE-003: Assessment service layer
- [ ] FE-004: Application selection page
- [ ] FE-005: Architecture verification page
- [ ] FE-006: Tech debt analysis page
- [ ] FE-007: 6R review page
- [ ] FE-008: Assessment summary page
- [ ] FE-009: Navigation updated
- [ ] MIG-002: Inventory page updated
- [ ] All pages responsive
- [ ] Loading and error states
- [ ] Component tests written
- [ ] E2E tests for flow

## Dependencies
- Requires Agent 3's API endpoints to be working
- Uses existing UI components from the project
- Follows existing design patterns

## Coordination Notes
- Test with real API responses from Agent 3
- Ensure real-time updates work smoothly
- Handle long-running flow execution gracefully
- Consider accessibility (ARIA labels, keyboard nav)