# Incomplete Discovery Flow Management Implementation Plan

## 🎯 **Executive Summary**

This document outlines the comprehensive implementation plan for proper incomplete discovery flow management in the AI Force Migration Platform using CrewAI Flow state management best practices. The goal is to ensure users can only initiate new discovery flows when no incomplete flows exist for their client/engagement context, and provide proper management tools for completing or discarding existing incomplete flows.

**Architecture Foundation**: Based on CrewAI Flow state management patterns from https://docs.crewai.com/guides/flows/mastering-flow-state and our UnifiedDiscoveryFlow implementation that uses structured state with Pydantic models and proper flow lifecycle management.

## 📊 **Current Implementation Analysis**

### ✅ **What's Already Implemented**

#### **Backend Validation Logic**
- **File**: `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`
- **Function**: `_validate_no_incomplete_discovery_flow()`
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Validates no incomplete discovery flows exist before allowing new data imports
  - Returns 409 conflict error with detailed information about existing flows
  - Provides recommendations for user action
  - Includes session_id, current_phase, progress_percentage, and next_steps

#### **Frontend Conflict Handling**
- **File**: `src/pages/discovery/CMDBImport.tsx`
- **Status**: ✅ **PARTIALLY IMPLEMENTED**
- **Functionality**:
  - Catches 409 conflict errors during data import
  - Shows toast notifications about incomplete flows
  - Offers navigation to existing flow via window.confirm dialog
  - Basic error handling and user guidance

#### **Workflow State Management**
- **File**: `backend/app/models/workflow_state.py`
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Complete WorkflowState model with multi-tenant isolation
  - UnifiedFlowStateRepository with CRUD operations
  - `delete_flow_state()` method for flow deletion
  - Multi-tenant filtering for all operations

#### **Flow Status Tracking**
- **Files**: Multiple discovery flow status endpoints
- **Status**: ✅ **IMPLEMENTED**
- **Functionality**:
  - Flow status polling and monitoring
  - Real-time progress tracking
  - Phase completion tracking
  - Agent insights and error logging

### ❌ **What's Missing**

#### **1. Frontend: Incomplete Flow Detection & UI Blocking**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**: 
  - Pre-upload validation to check for incomplete flows
  - Disable upload buttons when incomplete flows exist
  - Show incomplete flow warning banner
  - Redirect users to flow management interface

#### **2. Frontend: Incomplete Flow Management Interface**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**:
  - List of incomplete flows for current context
  - Flow details view (phase, progress, last activity)
  - Continue flow functionality
  - Discard/Delete flow functionality
  - Bulk flow management

#### **3. Backend: Flow Deletion with Data Cleanup**
- **Status**: ❌ **PARTIALLY IMPLEMENTED**
- **Required**:
  - Complete flow deletion API endpoint
  - Cascade deletion of associated data (assets, mappings, etc.)
  - Data integrity validation before deletion
  - Audit logging for deletion operations

#### **4. Backend: Enhanced Flow Management APIs**
- **Status**: ❌ **NOT IMPLEMENTED**
- **Required**:
  - List incomplete flows for context
  - Get detailed flow information
  - Resume/continue flow functionality
  - Batch flow operations

#### **5. Frontend: Enhanced Discovery Dashboard Integration**
- **Status**: ❌ **PARTIALLY IMPLEMENTED**
- **Required**:
  - Show incomplete flows prominently
  - Quick actions for flow management
  - Flow status indicators
  - Navigation to appropriate flow phases

## 🏗️ **CrewAI Flow-Based Implementation Plan**

### **Phase 1: Backend CrewAI Flow State Management Enhancements**

#### **Task 1.1: CrewAI Flow State Persistence Enhancement**
**File**: `backend/app/services/crewai_flows/discovery_flow_state_manager.py` (ENHANCE)

```python
class DiscoveryFlowStateManager:
    """Enhanced state manager leveraging CrewAI Flow state persistence patterns"""
    
    async def get_incomplete_flows_for_context(self, context: RequestContext) -> List[Dict[str, Any]]:
        """Get incomplete flows using CrewAI Flow state filtering"""
        # Query workflow_states for flows with status in ['running', 'paused']
        # Return structured flow information with CrewAI state data
        
    async def validate_flow_resumption(self, session_id: str, context: RequestContext) -> Dict[str, Any]:
        """Validate if a flow can be resumed using CrewAI Flow state validation"""
        # Check flow state integrity, phase dependencies, agent memory consistency
        
    async def prepare_flow_resumption(self, session_id: str) -> UnifiedDiscoveryFlow:
        """Prepare CrewAI Flow instance for resumption with proper state restoration"""
        # Restore UnifiedDiscoveryFlowState from database
        # Reinitialize CrewAI Flow with persisted state
        # Restore shared memory and knowledge base references
```

#### **Task 1.2: Enhanced UnifiedDiscoveryFlow with Flow Management**
**File**: `backend/app/services/crewai_flows/unified_discovery_flow.py` (ENHANCE)

```python
# Add new flow management methods to UnifiedDiscoveryFlow class

@listen()  # Can be called at any point in flow
def pause_flow(self, reason: str = "user_requested"):
    """Pause the discovery flow with proper state preservation"""
    self.state.status = "paused"
    self.state.log_entry(f"Flow paused: {reason}")
    # Persist current state to database
    return f"Flow paused at phase: {self.state.current_phase}"

@listen()
def resume_flow_from_state(self, resume_context: Dict[str, Any]):
    """Resume flow from persisted state with CrewAI Flow continuity"""
    # Validate state integrity
    # Restore agent memory and knowledge base
    # Continue from current phase
    self.state.status = "running"
    self.state.log_entry("Flow resumed from persisted state")
    return f"Flow resumed at phase: {self.state.current_phase}"

def get_flow_management_info(self) -> Dict[str, Any]:
    """Get comprehensive flow information for management UI"""
    return {
        "session_id": self.state.session_id,
        "current_phase": self.state.current_phase,
        "status": self.state.status,
        "progress_percentage": self.state.progress_percentage,
        "phase_completion": self.state.phase_completion,
        "can_resume": self._can_resume(),
        "deletion_impact": self._get_deletion_impact(),
        "agent_insights": self.state.agent_insights[-5:],  # Last 5 insights
        "created_at": self.state.created_at,
        "updated_at": self.state.updated_at
    }
```

#### **Task 1.3: Enhanced Flow Management API Endpoints**
**File**: `backend/app/api/v1/endpoints/discovery_flow_management.py` (NEW)

```python
@router.get("/flows/incomplete")
async def get_incomplete_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get all incomplete CrewAI discovery flows for current client/engagement context"""
    state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
    incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
    
    return {
        "flows": incomplete_flows,
        "total_count": len(incomplete_flows),
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id
        }
    }

@router.post("/flows/{session_id}/resume")
async def resume_discovery_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
    crewai_service = Depends(get_crewai_service)
) -> Dict[str, Any]:
    """Resume an incomplete CrewAI discovery flow with proper state restoration"""
    state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
    
    # Validate resumption capability
    validation = await state_manager.validate_flow_resumption(session_id, context)
    if not validation["can_resume"]:
        raise HTTPException(400, f"Cannot resume flow: {validation['reason']}")
    
    # Prepare and resume flow
    flow = await state_manager.prepare_flow_resumption(session_id)
    result = flow.resume_flow_from_state({"context": context.dict()})
    
    return {
        "resumed": True,
        "session_id": session_id,
        "current_phase": flow.state.current_phase,
        "next_steps": result
    }

@router.delete("/flows/{session_id}")
async def delete_discovery_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an incomplete CrewAI discovery flow with cascade cleanup"""
    cleanup_service = FlowCleanupService(db, context)
    result = await cleanup_service.delete_flow_with_cleanup(session_id)
    
    return result

@router.post("/flows/batch-delete")
async def batch_delete_flows(
    request: BatchDeleteRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete multiple CrewAI flows in batch operation with proper cleanup"""
    cleanup_service = FlowCleanupService(db, context)
    results = []
    
    for session_id in request.session_ids:
        try:
            result = await cleanup_service.delete_flow_with_cleanup(session_id)
            results.append({"session_id": session_id, "success": True, "result": result})
        except Exception as e:
            results.append({"session_id": session_id, "success": False, "error": str(e)})
    
    return {
        "batch_results": results,
        "total_processed": len(results),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]])
    }
```

#### **Task 1.4: CrewAI Flow Cleanup Service**
**File**: `backend/app/services/flow_cleanup_service.py` (NEW)

```python
class FlowCleanupService:
    """Service for safely deleting CrewAI discovery flows and associated data"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
    
    async def delete_flow_with_cleanup(self, session_id: str) -> Dict[str, Any]:
        """Delete CrewAI flow and cascade to all associated data"""
        try:
            # 1. Get flow state and validate deletion safety
            flow_state = await self._get_flow_state(session_id)
            if not flow_state:
                raise Exception(f"Flow not found: {session_id}")
            
            deletion_impact = await self.get_deletion_impact(session_id)
            
            # 2. Begin transaction for atomic deletion
            async with self.db.begin():
                # Delete WorkflowState (main CrewAI flow state)
                await self._delete_workflow_state(session_id)
                
                # Delete DataImportSession 
                await self._delete_data_import_session(session_id)
                
                # Delete ImportFieldMapping records
                await self._delete_field_mappings(session_id)
                
                # Delete created Asset records (if any)
                await self._delete_created_assets(flow_state.database_assets_created)
                
                # Delete AssetDependency records
                await self._delete_asset_dependencies(session_id)
                
                # Clean up file storage
                await self._cleanup_file_storage(session_id)
                
                # Clean up CrewAI shared memory
                await self._cleanup_shared_memory(flow_state.shared_memory_id)
                
                # Audit log the deletion
                await self._audit_log_deletion(session_id, deletion_impact)
            
            return {
                "deleted": True,
                "session_id": session_id,
                "deletion_impact": deletion_impact,
                "cleanup_summary": {
                    "workflow_state": True,
                    "data_import_session": True,
                    "field_mappings": True,
                    "assets_deleted": len(flow_state.database_assets_created),
                    "dependencies_deleted": True,
                    "files_cleaned": True,
                    "memory_cleaned": True
                }
            }
            
        except Exception as e:
            logger.error(f"Flow deletion failed for {session_id}: {e}")
            raise HTTPException(500, f"Flow deletion failed: {str(e)}")
    
    async def get_deletion_impact(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive information about what will be deleted"""
        flow_state = await self._get_flow_state(session_id)
        if not flow_state:
            return {"error": "Flow not found"}
        
        # Count associated data
        import_session_count = await self._count_import_sessions(session_id)
        field_mapping_count = await self._count_field_mappings(session_id)
        asset_count = len(flow_state.database_assets_created) if flow_state.database_assets_created else 0
        dependency_count = await self._count_dependencies(session_id)
        
        return {
            "session_id": session_id,
            "flow_phase": flow_state.current_phase,
            "flow_status": flow_state.status,
            "progress_percentage": flow_state.progress_percentage,
            "data_to_delete": {
                "workflow_state": 1,
                "import_sessions": import_session_count,
                "field_mappings": field_mapping_count,
                "assets": asset_count,
                "dependencies": dependency_count,
                "shared_memory_refs": 1 if flow_state.shared_memory_id else 0
            },
            "estimated_cleanup_time": self._estimate_cleanup_time(
                import_session_count, field_mapping_count, asset_count, dependency_count
            ),
            "data_recovery_possible": False,  # Deletion is permanent
            "created_at": flow_state.created_at,
            "last_activity": flow_state.updated_at
        }
```

### **Phase 2: Frontend CrewAI Flow Management Components**

#### **Task 2.1: CrewAI Flow Detection Hook**
**File**: `src/hooks/discovery/useIncompleteFlowDetection.ts` (NEW)

```typescript
export interface IncompleteFlow {
  session_id: string;
  current_phase: string;
  status: 'running' | 'paused' | 'failed';
  progress_percentage: number;
  phase_completion: Record<string, boolean>;
  agent_insights: Array<{
    phase: string;
    insight: string;
    confidence: number;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
  can_resume: boolean;
  deletion_impact: {
    flow_phase: string;
    data_to_delete: Record<string, number>;
    estimated_cleanup_time: string;
  };
}

export const useIncompleteFlowDetection = () => {
  const { client, engagement } = useAuth();
  
  return useQuery({
    queryKey: ['incomplete-flows', client?.id, engagement?.id],
    queryFn: async (): Promise<{flows: IncompleteFlow[], total_count: number}> => {
      const response = await apiCall('/api/v1/discovery-flow-management/flows/incomplete');
      return response;
    },
    enabled: !!client?.id && !!engagement?.id,
    refetchInterval: 30000, // Check every 30 seconds for real-time updates
    staleTime: 10000, // Consider data stale after 10 seconds
  });
};

export const useFlowResumption = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return await apiCall(`/api/v1/discovery-flow-management/flows/${sessionId}/resume`, {
        method: 'POST'
      });
    },
    onSuccess: () => {
      // Invalidate incomplete flows query to refresh UI
      queryClient.invalidateQueries(['incomplete-flows']);
    }
  });
};

export const useFlowDeletion = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return await apiCall(`/api/v1/discovery-flow-management/flows/${sessionId}`, {
        method: 'DELETE'
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['incomplete-flows']);
    }
  });
};
```

#### **Task 2.2: CrewAI Flow Management Interface Component**
**File**: `src/components/discovery/IncompleteFlowManager.tsx` (NEW)

```typescript
interface IncompleteFlowManagerProps {
  flows: IncompleteFlow[];
  onContinueFlow: (sessionId: string) => void;
  onDeleteFlow: (sessionId: string) => void;
  onBatchDelete: (sessionIds: string[]) => void;
}

export const IncompleteFlowManager: React.FC<IncompleteFlowManagerProps> = ({
  flows,
  onContinueFlow,
  onDeleteFlow,
  onBatchDelete
}) => {
  const [selectedFlows, setSelectedFlows] = useState<string[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showBatchDeleteConfirm, setShowBatchDeleteConfirm] = useState(false);

  const getPhaseIcon = (phase: string) => {
    const icons = {
      'field_mapping': MapPin,
      'data_cleansing': Zap,
      'asset_inventory': Server,
      'dependency_analysis': Network,
      'tech_debt_analysis': AlertTriangle
    };
    return icons[phase] || Activity;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with bulk actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Incomplete Discovery Flows</h2>
          <p className="text-gray-600 mt-1">
            {flows.length} incomplete flow{flows.length !== 1 ? 's' : ''} found. 
            Complete existing flows before starting new ones.
          </p>
        </div>
        
        {selectedFlows.length > 0 && (
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">
              {selectedFlows.length} selected
            </span>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowBatchDeleteConfirm(true)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Selected
            </Button>
          </div>
        )}
      </div>

      {/* Flow list */}
      <div className="space-y-4">
        {flows.map((flow) => {
          const PhaseIcon = getPhaseIcon(flow.current_phase);
          
          return (
            <Card key={flow.session_id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      checked={selectedFlows.includes(flow.session_id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedFlows([...selectedFlows, flow.session_id]);
                        } else {
                          setSelectedFlows(selectedFlows.filter(id => id !== flow.session_id));
                        }
                      }}
                    />
                    <div className="flex items-center space-x-2">
                      <PhaseIcon className="h-5 w-5 text-blue-600" />
                      <div>
                        <h3 className="font-semibold">
                          {flow.current_phase.replace('_', ' ').toUpperCase()} Phase
                        </h3>
                        <p className="text-sm text-gray-600">
                          Session: {flow.session_id.substring(0, 8)}...
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(flow.status)}>
                      {flow.status.toUpperCase()}
                    </Badge>
                    <Badge variant="outline">
                      {Math.round(flow.progress_percentage)}% Complete
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                {/* Progress bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span>Overall Progress</span>
                    <span>{Math.round(flow.progress_percentage)}%</span>
                  </div>
                  <Progress value={flow.progress_percentage} className="h-2" />
                </div>

                {/* Phase completion status */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
                  {Object.entries(flow.phase_completion).map(([phase, completed]) => (
                    <div key={phase} className="flex items-center space-x-1">
                      {completed ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <Circle className="h-4 w-4 text-gray-300" />
                      )}
                      <span className="text-xs text-gray-600 capitalize">
                        {phase.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Recent agent insights */}
                {flow.agent_insights.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Insights</h4>
                    <div className="space-y-1">
                      {flow.agent_insights.slice(0, 2).map((insight, idx) => (
                        <div key={idx} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                          <span className="font-medium">{insight.phase}:</span> {insight.insight}
                          <span className="text-gray-400 ml-2">
                            ({Math.round(insight.confidence * 100)}% confidence)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timestamps */}
                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span>Created: {new Date(flow.created_at).toLocaleString()}</span>
                  <span>Last Activity: {new Date(flow.updated_at).toLocaleString()}</span>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {flow.can_resume && (
                      <Button
                        size="sm"
                        onClick={() => onContinueFlow(flow.session_id)}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Continue Flow
                      </Button>
                    )}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Navigate to flow details or phase-specific page
                        const phaseRoutes = {
                          'field_mapping': `/discovery/attribute-mapping/${flow.session_id}`,
                          'data_cleansing': `/discovery/data-cleansing/${flow.session_id}`,
                          'asset_inventory': `/discovery/asset-inventory/${flow.session_id}`,
                          'dependency_analysis': `/discovery/dependencies/${flow.session_id}`,
                          'tech_debt_analysis': `/discovery/technical-debt/${flow.session_id}`
                        };
                        const route = phaseRoutes[flow.current_phase] || `/discovery/enhanced-dashboard`;
                        window.location.href = route;
                      }}
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                  
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setShowDeleteConfirm(flow.session_id)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Delete confirmation dialogs */}
      {showDeleteConfirm && (
        <FlowDeletionConfirmDialog
          flow={flows.find(f => f.session_id === showDeleteConfirm)!}
          onConfirm={() => {
            onDeleteFlow(showDeleteConfirm);
            setShowDeleteConfirm(null);
          }}
          onCancel={() => setShowDeleteConfirm(null)}
        />
      )}

      {showBatchDeleteConfirm && (
        <BatchDeletionConfirmDialog
          flowCount={selectedFlows.length}
          onConfirm={() => {
            onBatchDelete(selectedFlows);
            setSelectedFlows([]);
            setShowBatchDeleteConfirm(false);
          }}
          onCancel={() => setShowBatchDeleteConfirm(false)}
        />
      )}
    </div>
  );
};
```

#### **Task 2.3: Upload Blocking Component**
**File**: `src/components/discovery/UploadBlocker.tsx` (NEW)

```typescript
interface UploadBlockerProps {
  incompleteFlows: IncompleteFlow[];
  onManageFlows: () => void;
}

export const UploadBlocker: React.FC<UploadBlockerProps> = ({
  incompleteFlows,
  onManageFlows
}) => {
  const resumeFlow = useFlowResumption();
  
  const getMostRecentFlow = () => {
    return incompleteFlows.sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )[0];
  };

  const mostRecentFlow = getMostRecentFlow();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Main blocking alert */}
      <Alert className="border-yellow-200 bg-yellow-50 mb-6">
        <AlertTriangle className="h-5 w-5 text-yellow-600" />
        <AlertTitle className="text-yellow-800">
          Cannot Upload New Data - Incomplete Discovery Flow Found
        </AlertTitle>
        <AlertDescription className="text-yellow-700 mt-2">
          You have {incompleteFlows.length} incomplete discovery flow{incompleteFlows.length > 1 ? 's' : ''} 
          that must be completed or removed before uploading new data. This ensures data integrity 
          and prevents conflicts in your CrewAI discovery process.
        </AlertDescription>
      </Alert>

      {/* Most recent flow quick actions */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <span>Most Recent Flow</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">
                {mostRecentFlow.current_phase.replace('_', ' ').toUpperCase()} Phase
              </p>
              <p className="text-sm text-gray-600">
                {Math.round(mostRecentFlow.progress_percentage)}% complete • 
                Last activity: {new Date(mostRecentFlow.updated_at).toLocaleString()}
              </p>
              <div className="mt-2">
                <Progress value={mostRecentFlow.progress_percentage} className="h-2 w-48" />
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {mostRecentFlow.can_resume && (
                <Button
                  onClick={() => resumeFlow.mutate(mostRecentFlow.session_id)}
                  disabled={resumeFlow.isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {resumeFlow.isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Continue This Flow
                </Button>
              )}
              
              <Button
                variant="outline"
                onClick={onManageFlows}
              >
                <Settings className="h-4 w-4 mr-2" />
                Manage All Flows
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Flow summary */}
      <Card>
        <CardHeader>
          <CardTitle>Incomplete Flows Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {incompleteFlows.map((flow) => (
              <div key={flow.session_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">
                    {flow.current_phase.replace('_', ' ').toUpperCase()}
                  </p>
                  <p className="text-sm text-gray-600">
                    {Math.round(flow.progress_percentage)}% • {flow.status}
                  </p>
                </div>
                <Badge variant="outline">
                  {flow.session_id.substring(0, 8)}...
                </Badge>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t">
            <Button
              onClick={onManageFlows}
              className="w-full"
              variant="outline"
            >
              <List className="h-4 w-4 mr-2" />
              Manage All Incomplete Flows
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

### **Phase 3: Database Schema Enhancements for CrewAI Flow Management**

#### **Task 3.1: Enhanced Workflow States Table**
**File**: `backend/alembic/versions/add_flow_management_columns.py` (NEW)

```sql
-- Migration: Add CrewAI Flow management columns
ALTER TABLE workflow_states 
ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS auto_cleanup_eligible BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS deletion_scheduled_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_user_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS flow_resumption_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS agent_memory_refs JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS knowledge_base_refs JSONB DEFAULT '[]';

-- Add indexes for flow management queries
CREATE INDEX IF NOT EXISTS idx_workflow_states_expiration 
ON workflow_states(expiration_date) 
WHERE status IN ('running', 'paused');

CREATE INDEX IF NOT EXISTS idx_workflow_states_cleanup 
ON workflow_states(auto_cleanup_eligible, expiration_date);

CREATE INDEX IF NOT EXISTS idx_workflow_states_activity 
ON workflow_states(last_user_activity, client_account_id, engagement_id);

-- Add index for incomplete flow detection (primary query)
CREATE INDEX IF NOT EXISTS idx_workflow_states_incomplete 
ON workflow_states(client_account_id, engagement_id, status) 
WHERE status IN ('running', 'paused', 'failed');
```

#### **Task 3.2: Flow Deletion Audit Table**
**File**: `backend/alembic/versions/create_flow_deletion_audit.py` (NEW)

```sql
-- Create comprehensive audit table for flow deletions
CREATE TABLE IF NOT EXISTS flow_deletion_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    flow_id UUID NOT NULL,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    user_id VARCHAR NOT NULL,
    deletion_type VARCHAR NOT NULL, -- 'user_requested', 'auto_cleanup', 'admin_action', 'batch_operation'
    deletion_reason TEXT,
    deletion_method VARCHAR NOT NULL, -- 'manual', 'api', 'batch', 'scheduled'
    
    -- Comprehensive data deletion summary
    data_deleted JSONB NOT NULL DEFAULT '{}', -- Summary of what was deleted
    deletion_impact JSONB NOT NULL DEFAULT '{}', -- Impact analysis
    cleanup_summary JSONB NOT NULL DEFAULT '{}', -- Cleanup operation results
    
    -- CrewAI specific cleanup
    shared_memory_cleaned BOOLEAN DEFAULT FALSE,
    knowledge_base_refs_cleaned JSONB DEFAULT '[]',
    agent_memory_cleaned BOOLEAN DEFAULT FALSE,
    
    -- Audit trail
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_by VARCHAR NOT NULL,
    deletion_duration_ms INTEGER, -- How long the deletion took
    
    -- Recovery information (if applicable)
    recovery_possible BOOLEAN DEFAULT FALSE,
    recovery_data JSONB DEFAULT '{}'
);

-- Indexes for audit queries
CREATE INDEX idx_flow_deletion_audit_client 
ON flow_deletion_audit(client_account_id, engagement_id);

CREATE INDEX idx_flow_deletion_audit_date 
ON flow_deletion_audit(deleted_at);

CREATE INDEX idx_flow_deletion_audit_type 
ON flow_deletion_audit(deletion_type, deleted_at);

CREATE INDEX idx_flow_deletion_audit_session 
ON flow_deletion_audit(session_id);
```

#### **Task 3.3: CrewAI Flow State Extensions Table**
**File**: `backend/alembic/versions/create_crewai_flow_extensions.py` (NEW)

```sql
-- Extended table for CrewAI-specific flow state data
CREATE TABLE IF NOT EXISTS crewai_flow_state_extensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workflow_states(session_id) ON DELETE CASCADE,
    flow_id UUID NOT NULL,
    
    -- CrewAI Flow persistence data
    flow_persistence_data JSONB NOT NULL DEFAULT '{}',
    agent_collaboration_log JSONB DEFAULT '[]',
    memory_usage_metrics JSONB DEFAULT '{}',
    knowledge_base_analytics JSONB DEFAULT '{}',
    
    -- Flow performance metrics
    phase_execution_times JSONB DEFAULT '{}',
    agent_performance_metrics JSONB DEFAULT '{}',
    crew_coordination_analytics JSONB DEFAULT '{}',
    
    -- Learning and adaptation data
    learning_patterns JSONB DEFAULT '[]',
    user_feedback_history JSONB DEFAULT '[]',
    adaptation_metrics JSONB DEFAULT '{}',
    
    -- Flow resumption support
    resumption_checkpoints JSONB DEFAULT '[]',
    state_snapshots JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for CrewAI flow queries
CREATE INDEX idx_crewai_flow_extensions_session 
ON crewai_flow_state_extensions(session_id);

CREATE INDEX idx_crewai_flow_extensions_flow 
ON crewai_flow_state_extensions(flow_id);
```

### **Phase 4: Frontend Integration with CrewAI Flow Management**

#### **Task 4.1: Enhanced CMDBImport with CrewAI Flow Detection**
**File**: `src/pages/discovery/CMDBImport.tsx` (ENHANCE)

```typescript
// Add at the beginning of the CMDBImport component
const { data: incompleteFlows, isLoading: checkingFlows } = useIncompleteFlowDetection();
const hasIncompleteFlows = incompleteFlows?.flows?.length > 0;
const [showFlowManager, setShowFlowManager] = useState(false);

// Replace the upload sections with conditional rendering
{checkingFlows ? (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    <span className="ml-3 text-gray-600">Checking for incomplete flows...</span>
  </div>
) : hasIncompleteFlows ? (
  <UploadBlocker 
    incompleteFlows={incompleteFlows.flows}
    onManageFlows={() => setShowFlowManager(true)}
  />
) : (
  // Existing upload interface
  <div className="mb-8">
    <h2 className="text-xl font-semibold text-gray-900 mb-6">Choose Data Category</h2>
    {/* Existing upload categories grid */}
  </div>
)}

// Add flow management modal
{showFlowManager && (
  <FlowManagerModal
    flows={incompleteFlows?.flows || []}
    onClose={() => setShowFlowManager(false)}
    onFlowAction={(action, sessionId) => {
      if (action === 'continue') {
        // Handle flow continuation
        resumeFlow.mutate(sessionId);
      } else if (action === 'delete') {
        // Handle flow deletion
        deleteFlow.mutate(sessionId);
      }
      setShowFlowManager(false);
    }}
  />
)}
```

#### **Task 4.2: Enhanced Discovery Dashboard Integration**
**File**: `src/pages/discovery/EnhancedDiscoveryDashboard.tsx` (ENHANCE)

```typescript
// Add incomplete flows section to dashboard
const { data: incompleteFlows } = useIncompleteFlowDetection();
const hasIncompleteFlows = incompleteFlows?.flows?.length > 0;

// Add to dashboard tabs
<TabsContent value="incomplete" className="space-y-6">
  {hasIncompleteFlows ? (
    <IncompleteFlowManager
      flows={incompleteFlows.flows}
      onContinueFlow={(sessionId) => {
        resumeFlow.mutate(sessionId);
      }}
      onDeleteFlow={(sessionId) => {
        deleteFlow.mutate(sessionId);
      }}
      onBatchDelete={(sessionIds) => {
        batchDeleteFlows.mutate(sessionIds);
      }}
    />
  ) : (
    <div className="text-center py-12">
      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No Incomplete Flows
      </h3>
      <p className="text-gray-600">
        All discovery flows are completed. You can start a new flow anytime.
      </p>
    </div>
  )}
</TabsContent>

// Add alert banner for incomplete flows
{hasIncompleteFlows && (
  <Alert className="mb-6 border-yellow-200 bg-yellow-50">
    <AlertTriangle className="h-5 w-5 text-yellow-600" />
    <AlertTitle className="text-yellow-800">
      {incompleteFlows.flows.length} Incomplete Flow{incompleteFlows.flows.length > 1 ? 's' : ''} Found
    </AlertTitle>
    <AlertDescription className="text-yellow-700">
      Complete or remove existing flows before starting new discovery processes.
      <Button
        variant="link"
        className="p-0 ml-2 text-yellow-700 underline"
        onClick={() => setActiveTab("incomplete")}
      >
        Manage Flows
      </Button>
    </AlertDescription>
  </Alert>
)}
```

## 🧪 **Comprehensive Testing Strategy**

### **Backend Testing**

#### **Unit Tests**
- `test_discovery_flow_state_manager.py` - CrewAI Flow state management
- `test_flow_cleanup_service.py` - Flow deletion and cleanup logic
- `test_flow_management_endpoints.py` - API endpoint functionality
- `test_incomplete_flow_detection.py` - Flow detection logic with CrewAI state
- `test_crewai_flow_resumption.py` - Flow resumption with state restoration

#### **Integration Tests**
- `test_crewai_flow_lifecycle.py` - Complete flow lifecycle with interruption/resume
- `test_flow_state_persistence.py` - CrewAI Flow state persistence and restoration
- `test_multi_tenant_flow_isolation.py` - Multi-tenant flow management
- `test_agent_memory_cleanup.py` - CrewAI shared memory cleanup during deletion

### **Frontend Testing**

#### **Component Tests**
- `IncompleteFlowManager.test.tsx` - Flow management UI with CrewAI data
- `useIncompleteFlowDetection.test.ts` - Hook functionality with real-time updates
- `UploadBlocker.test.tsx` - Upload blocking behavior
- `FlowResumption.test.tsx` - CrewAI Flow resumption logic

#### **End-to-End Tests**
- Complete CrewAI discovery flow lifecycle with interruption and resume
- Multiple incomplete flows management across different phases
- Bulk flow deletion operations with cleanup verification
- Cross-page navigation with incomplete flows and state preservation

### **Performance Testing**
- Flow detection query performance with large datasets
- Bulk deletion operations with comprehensive cleanup
- Real-time flow status updates and UI responsiveness
- CrewAI Flow state restoration performance

## 📋 **Implementation Timeline**

### **Sprint 1 (Week 1-2): Backend CrewAI Flow Foundation**
- Task 1.1: CrewAI Flow State Persistence Enhancement
- Task 1.2: Enhanced UnifiedDiscoveryFlow with Flow Management
- Task 1.3: Enhanced Flow Management API Endpoints
- Task 1.4: CrewAI Flow Cleanup Service
- Database schema updates

### **Sprint 2 (Week 3-4): Frontend CrewAI Flow Components**
- Task 2.1: CrewAI Flow Detection Hook
- Task 2.2: CrewAI Flow Management Interface Component
- Task 2.3: Upload Blocking Component
- Unit tests for new components

### **Sprint 3 (Week 5-6): Database & Frontend Integration**
- Task 3.1-3.3: Database schema enhancements
- Task 4.1: Enhanced CMDBImport with CrewAI Flow Detection
- Task 4.2: Enhanced Discovery Dashboard Integration
- Integration testing with CrewAI Flow state

### **Sprint 4 (Week 7-8): Advanced Features & Production Readiness**
- Advanced flow recovery and resumption with CrewAI state
- Bulk flow management with CrewAI memory cleanup
- Flow expiration and auto-cleanup
- Performance optimization and production deployment
- End-to-end testing and UAT

## 🚀 **Success Criteria**

### **Functional Requirements**
- ✅ Users cannot start new discovery flows when incomplete CrewAI flows exist
- ✅ Users can easily identify and manage incomplete flows with full CrewAI state visibility
- ✅ Users can resume incomplete flows from exact CrewAI Flow state where they left off
- ✅ Users can safely delete incomplete flows with complete CrewAI memory cleanup
- ✅ System maintains CrewAI Flow state integrity during all operations

### **Performance Requirements**
- ✅ Incomplete flow detection completes in <500ms with CrewAI state queries
- ✅ Flow deletion operations with CrewAI cleanup complete in <5 seconds
- ✅ CrewAI Flow resumption completes in <10 seconds with full state restoration
- ✅ UI remains responsive during all CrewAI flow management operations

### **CrewAI Integration Requirements**
- ✅ Proper CrewAI Flow state persistence and restoration
- ✅ Complete agent memory and knowledge base cleanup
- ✅ Seamless flow resumption with agent context preservation
- ✅ Multi-tenant isolation of CrewAI Flow states and memory

## 🎯 **Next Steps**

1. **Review and approve this comprehensive CrewAI Flow-based implementation plan**
2. **Set up development environment with CrewAI Flow state management**
3. **Begin Sprint 1 implementation with backend CrewAI Flow foundation**
4. **Establish testing protocols for CrewAI Flow management scenarios**
5. **Create monitoring and alerting for CrewAI Flow operations**

This comprehensive plan ensures that the incomplete discovery flow management feature will be robust, user-friendly, and maintainable while leveraging CrewAI Flow state management best practices and preserving data integrity throughout the entire flow lifecycle.
