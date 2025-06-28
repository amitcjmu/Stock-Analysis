# 🤖 Flow Processing Agent Design Document

## Executive Summary

The **Flow Processing Agent** is a central AI-powered orchestrator that manages all discovery flow continuations. When a user clicks "Continue Flow", this agent analyzes the flow's current state, evaluates completion checklists for each phase, and intelligently routes the flow to the appropriate next step.

## 🎯 Core Responsibilities

### 1. **Central Flow Orchestration**
- Receive all "Continue Flow" requests from the UI
- Analyze current flow state and completion status
- Determine the correct next phase or action
- Route users to the appropriate page with proper context

### 2. **Intelligent Checklist Validation**
- Maintain comprehensive checklists for each discovery phase
- Evaluate what tasks have been completed vs. pending
- Identify missing requirements and dependencies
- Provide specific guidance on what needs to be done

### 3. **Context-Aware Routing**
- Analyze flow data to determine actual completion state
- Route users to the exact step that needs attention
- Pre-populate pages with relevant flow context
- Handle error states and recovery scenarios

## 🏗️ Architecture Design

### **Flow Processing Agent Structure**

```python
class FlowProcessingAgent(BaseTool):
    """
    Central AI agent for intelligent flow continuation and routing.
    Replaces hard-coded flow logic with intelligent analysis.
    """
    
    name: str = "flow_processing_agent"
    description: str = "Intelligent flow analysis and routing for discovery flows"
    
    # Core capabilities
    checklist_analyzer: FlowChecklistAnalyzer
    phase_validator: PhaseCompletionValidator  
    route_orchestrator: RouteOrchestrator
    context_builder: FlowContextBuilder
    
    def _run(self, flow_id: str, user_action: str) -> FlowContinuationResult:
        """
        Main entry point for all flow continuation requests
        """
        return self.process_flow_continuation(flow_id, user_action)
```

### **Phase Completion Checklists**

```yaml
# Discovery Phase Checklists
data_import:
  required_tasks:
    - file_upload_completed: "Data file successfully uploaded"
    - format_validation: "File format validated by agents" 
    - data_parsing: "Data successfully parsed into records"
    - initial_analysis: "Basic data analysis completed"
    - agent_insights_generated: "Import validation agents provided insights"
  validation_criteria:
    - min_records: 1
    - agent_confidence: 0.7
    - validation_status: "passed"
  next_phase_conditions:
    - all_required_tasks: true
    - data_quality_acceptable: true

attribute_mapping:
  required_tasks:
    - field_analysis_completed: "Source fields analyzed by agents"
    - critical_attributes_identified: "Critical migration attributes identified"
    - mapping_suggestions_generated: "AI-generated field mapping suggestions"
    - user_mapping_review: "User reviewed and approved mappings"
    - confidence_scores_calculated: "Mapping confidence scores generated"
  validation_criteria:
    - min_mapped_fields: 5
    - critical_fields_mapped: 80%
    - avg_confidence_score: 0.6
  next_phase_conditions:
    - user_approval_received: true
    - critical_mappings_complete: true

data_cleansing:
  required_tasks:
    - quality_analysis_completed: "Data quality assessment performed"
    - cleansing_rules_applied: "Data cleansing rules executed"
    - validation_performed: "Cleansed data validated"
    - quality_metrics_calculated: "Quality improvement metrics generated"
    - agent_quality_review: "Quality assessment agents completed review"
  validation_criteria:
    - quality_improvement: 10%
    - completeness_score: 0.8
    - consistency_score: 0.7
  next_phase_conditions:
    - quality_thresholds_met: true
    - cleansing_approved: true

inventory:
  required_tasks:
    - asset_classification: "Assets classified by type and category"
    - criticality_assessment: "Business criticality evaluated"
    - dependency_identification: "Basic dependencies identified"
    - migration_readiness: "Migration readiness scored"
    - agent_inventory_review: "Inventory agents completed analysis"
  validation_criteria:
    - min_assets_classified: 90%
    - criticality_assigned: 80%
    - migration_scores_calculated: true
  next_phase_conditions:
    - inventory_complete: true
    - asset_validation_passed: true

dependencies:
  required_tasks:
    - app_dependencies_mapped: "Application dependencies identified"
    - infrastructure_dependencies: "Infrastructure dependencies mapped"
    - data_dependencies: "Data flow dependencies analyzed"
    - integration_complexity: "Integration complexity assessed"
    - dependency_validation: "Dependencies validated by agents"
  validation_criteria:
    - dependency_coverage: 85%
    - complexity_scores_assigned: true
    - validation_confidence: 0.7
  next_phase_conditions:
    - dependency_analysis_complete: true
    - complexity_assessment_done: true

tech_debt:
  required_tasks:
    - technical_assessment: "Technical debt assessment completed"
    - modernization_opportunities: "Modernization opportunities identified"
    - risk_analysis: "Technical risks analyzed"
    - recommendation_generation: "Modernization recommendations generated"
    - six_r_preparation: "6R strategy preparation completed"
  validation_criteria:
    - debt_scores_calculated: true
    - recommendations_generated: true
    - risk_assessment_complete: true
  next_phase_conditions:
    - technical_analysis_complete: true
    - ready_for_6r_strategy: true
```

## 🤖 Agent Implementation

### **1. Flow Continuation Processor**

```python
class FlowContinuationProcessor:
    """
    Core processor that handles flow continuation requests
    """
    
    async def process_continuation_request(
        self, 
        flow_id: str, 
        user_context: Dict[str, Any]
    ) -> FlowContinuationResult:
        """
        Main processing method for flow continuation
        """
        
        # Step 1: Analyze current flow state
        flow_analysis = await self.analyze_flow_state(flow_id)
        
        # Step 2: Evaluate phase completion checklists
        checklist_results = await self.evaluate_phase_checklists(flow_analysis)
        
        # Step 3: Determine next action
        next_action = await self.determine_next_action(checklist_results)
        
        # Step 4: Build routing context
        routing_context = await self.build_routing_context(
            flow_analysis, 
            checklist_results, 
            next_action
        )
        
        # Step 5: Generate continuation result
        return FlowContinuationResult(
            flow_id=flow_id,
            current_phase=flow_analysis.current_phase,
            next_action=next_action,
            routing_context=routing_context,
            checklist_status=checklist_results,
            user_guidance=await self.generate_user_guidance(next_action)
        )
```

### **2. Phase Checklist Analyzer**

```python
class PhaseChecklistAnalyzer:
    """
    Analyzes phase completion against comprehensive checklists
    """
    
    async def evaluate_phase_completion(
        self, 
        flow_data: FlowData, 
        phase: str
    ) -> PhaseChecklistResult:
        """
        Evaluate if a phase meets all completion criteria
        """
        
        checklist = self.get_phase_checklist(phase)
        results = PhaseChecklistResult(phase=phase)
        
        for task in checklist.required_tasks:
            task_result = await self.evaluate_task_completion(
                flow_data, 
                task
            )
            results.add_task_result(task, task_result)
        
        # Validate against criteria
        results.validation_passed = self.validate_completion_criteria(
            results, 
            checklist.validation_criteria
        )
        
        # Check next phase readiness
        results.ready_for_next_phase = self.check_next_phase_conditions(
            results,
            checklist.next_phase_conditions
        )
        
        return results
    
    async def evaluate_task_completion(
        self, 
        flow_data: FlowData, 
        task: TaskDefinition
    ) -> TaskResult:
        """
        Evaluate if a specific task has been completed
        """
        
        # Use AI to analyze if task is complete
        ai_analysis = await self.ai_task_analyzer.analyze_task_completion(
            flow_data=flow_data,
            task_definition=task,
            evidence_sources=[
                "agent_insights",
                "database_records", 
                "flow_state_data",
                "user_interactions"
            ]
        )
        
        return TaskResult(
            task_id=task.id,
            completed=ai_analysis.is_complete,
            confidence=ai_analysis.confidence,
            evidence=ai_analysis.evidence,
            missing_requirements=ai_analysis.missing_requirements,
            next_steps=ai_analysis.recommended_next_steps
        )
```

### **3. Intelligent Route Orchestrator**

```python
class RouteOrchestrator:
    """
    Determines the correct routing based on flow analysis
    """
    
    async def determine_optimal_route(
        self, 
        flow_analysis: FlowAnalysis,
        checklist_results: List[PhaseChecklistResult]
    ) -> RouteDecision:
        """
        Determine where to route the user based on intelligent analysis
        """
        
        # Find the first incomplete phase
        incomplete_phase = self.find_first_incomplete_phase(checklist_results)
        
        if not incomplete_phase:
            # All phases complete - route to next logical step
            return self.route_to_completion_action(flow_analysis)
        
        # Find the specific task that needs attention
        pending_task = self.find_next_pending_task(incomplete_phase)
        
        # Determine the exact page and context needed
        route_decision = RouteDecision(
            target_page=self.get_task_page(pending_task),
            flow_id=flow_analysis.flow_id,
            phase=incomplete_phase.phase,
            specific_task=pending_task.task_id,
            context_data=self.build_page_context(
                flow_analysis, 
                incomplete_phase, 
                pending_task
            ),
            user_guidance=self.generate_task_guidance(pending_task)
        )
        
        return route_decision
    
    def get_task_page(self, task: TaskResult) -> str:
        """
        Map specific tasks to the appropriate UI pages
        """
        task_page_mapping = {
            # Data Import tasks
            "file_upload_completed": "/discovery/import",
            "format_validation": "/discovery/import",
            "data_parsing": "/discovery/import",
            
            # Attribute Mapping tasks
            "field_analysis_completed": "/discovery/attribute-mapping",
            "mapping_suggestions_generated": "/discovery/attribute-mapping", 
            "user_mapping_review": "/discovery/attribute-mapping",
            
            # Data Cleansing tasks
            "quality_analysis_completed": "/discovery/data-cleansing",
            "cleansing_rules_applied": "/discovery/data-cleansing",
            "validation_performed": "/discovery/data-cleansing",
            
            # Inventory tasks
            "asset_classification": "/discovery/inventory",
            "criticality_assessment": "/discovery/inventory",
            "migration_readiness": "/discovery/inventory",
            
            # Dependencies tasks
            "app_dependencies_mapped": "/discovery/dependencies",
            "infrastructure_dependencies": "/discovery/dependencies",
            "integration_complexity": "/discovery/dependencies",
            
            # Tech Debt tasks
            "technical_assessment": "/discovery/tech-debt",
            "modernization_opportunities": "/discovery/tech-debt",
            "six_r_preparation": "/discovery/tech-debt"
        }
        
        return task_page_mapping.get(
            task.task_id, 
            f"/discovery/{task.phase}"
        )
```

## 🔄 Integration with UI

### **Enhanced Continue Flow Handler**

```typescript
// Enhanced flow continuation in EnhancedDiscoveryDashboard.tsx
const handleContinueFlow = async (flowId: string) => {
  try {
    setFlowLoading(true);
    
    // Call the Flow Processing Agent
    const response = await flowProcessingAgent.processContinuation({
      flow_id: flowId,
      user_context: {
        client_account_id: client?.id,
        engagement_id: engagement?.id,
        user_id: user?.id
      }
    });
    
    if (response.success) {
      // Show user what the agent determined
      toast.success(
        `🤖 Flow Analysis Complete: ${response.user_guidance.summary}`
      );
      
      // Route to the exact location determined by the agent
      navigate(response.routing_context.target_page, {
        state: {
          flow_id: flowId,
          phase: response.current_phase,
          task_context: response.routing_context.context_data,
          checklist_status: response.checklist_status,
          agent_guidance: response.user_guidance
        }
      });
      
    } else {
      toast.error(`Flow Processing Failed: ${response.error_message}`);
    }
    
  } catch (error) {
    console.error('Flow Processing Agent failed:', error);
    toast.error('Failed to process flow continuation');
  } finally {
    setFlowLoading(false);
  }
};
```

### **Context-Aware Page Loading**

```typescript
// Enhanced page components that receive agent context
const AttributeMappingPage = () => {
  const location = useLocation();
  const agentContext = location.state?.agent_guidance;
  const checklistStatus = location.state?.checklist_status;
  
  useEffect(() => {
    if (agentContext) {
      // Show user exactly what needs to be done
      showAgentGuidance(agentContext);
      
      // Pre-populate page based on checklist status
      if (checklistStatus) {
        highlightPendingTasks(checklistStatus.pending_tasks);
      }
    }
  }, [agentContext, checklistStatus]);
  
  return (
    <div>
      {agentContext && (
        <AgentGuidancePanel 
          guidance={agentContext}
          checklistStatus={checklistStatus}
        />
      )}
      {/* Rest of page content */}
    </div>
  );
};
```

## 📊 API Endpoints

### **Flow Processing Agent API**

```python
@router.post("/api/v1/flow-processing/continue/{flow_id}")
async def continue_flow_with_agent(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext = Depends(get_current_context)
) -> FlowContinuationResponse:
    """
    Process flow continuation using the Flow Processing Agent
    """
    
    try:
        # Initialize Flow Processing Agent
        flow_agent = FlowProcessingAgent(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Process the continuation request
        result = await flow_agent.process_continuation(
            flow_id=flow_id,
            user_context=request.user_context
        )
        
        return FlowContinuationResponse(
            success=True,
            flow_id=flow_id,
            current_phase=result.current_phase,
            next_action=result.next_action,
            routing_context=result.routing_context,
            checklist_status=result.checklist_status,
            user_guidance=result.user_guidance
        )
        
    except Exception as e:
        logger.error(f"Flow Processing Agent failed for {flow_id}: {e}")
        return FlowContinuationResponse(
            success=False,
            error_message=str(e),
            fallback_route="/discovery/enhanced-dashboard"
        )

@router.get("/api/v1/flow-processing/checklist/{flow_id}")
async def get_flow_checklist_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context)
) -> FlowChecklistResponse:
    """
    Get detailed checklist status for a flow
    """
    
    flow_agent = FlowProcessingAgent(
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    )
    
    checklist_status = await flow_agent.get_checklist_status(flow_id)
    
    return FlowChecklistResponse(
        flow_id=flow_id,
        phases=checklist_status.phases,
        overall_completion=checklist_status.overall_completion,
        next_required_tasks=checklist_status.next_required_tasks,
        blocking_issues=checklist_status.blocking_issues
    )
```

## 🎯 User Experience Flow

### **1. User Clicks "Continue Flow"**
```
User Action: Click "Continue Flow" on flow ff1cb4ba...
↓
Flow Processing Agent receives request
↓
Agent analyzes flow state and checklists
↓
Agent determines: "Attribute mapping needs user review"
↓
Agent routes to: /discovery/attribute-mapping/ff1cb4ba
↓
Page loads with specific guidance: "Please review and approve the 12 suggested field mappings"
```

### **2. Agent Guidance Display**
```
🤖 Flow Processing Agent Analysis:

Current Phase: Attribute Mapping
Completion Status: 75% complete

✅ Completed Tasks:
- Field analysis completed
- Critical attributes identified  
- Mapping suggestions generated

⏳ Pending Tasks:
- User mapping review (REQUIRED)
- Confidence scores calculation

Next Steps:
1. Review the 12 suggested field mappings below
2. Approve or modify mappings as needed
3. Click "Approve Mappings" to continue to Data Cleansing
```

## 🔧 Implementation Plan

### **Phase 1: Core Agent Development**
1. Create `FlowProcessingAgent` class with basic checklist evaluation
2. Implement phase completion checklist definitions
3. Build route orchestration logic
4. Create API endpoints for agent communication

### **Phase 2: UI Integration**
1. Update "Continue Flow" handlers to use Flow Processing Agent
2. Enhance page components to receive and display agent context
3. Create agent guidance UI components
4. Implement checklist status displays

### **Phase 3: Advanced Intelligence**
1. Add machine learning for checklist optimization
2. Implement predictive flow routing
3. Add user behavior learning
4. Create automated flow recovery for error states

### **Phase 4: Monitoring & Analytics**
1. Add flow processing metrics and monitoring
2. Create agent decision audit trails
3. Implement flow efficiency analytics
4. Add user satisfaction tracking

## 🌟 Success Metrics

### **Agent Intelligence**
- **100% Intelligent Routing**: All flow continuations use agent analysis
- **Accurate Task Detection**: Agent correctly identifies pending tasks
- **Context-Aware Guidance**: Users receive specific next steps
- **Zero Dead Ends**: No more pages with "no data" or unclear next steps

### **User Experience**
- **Seamless Continuation**: Users always know what to do next
- **Reduced Confusion**: Clear guidance on incomplete tasks
- **Faster Completion**: Direct routing to the exact step needed
- **Error Recovery**: Intelligent handling of flow issues

This Flow Processing Agent will transform the discovery flow experience from a confusing maze into an intelligent, guided journey where users always know exactly what needs to be done next. 