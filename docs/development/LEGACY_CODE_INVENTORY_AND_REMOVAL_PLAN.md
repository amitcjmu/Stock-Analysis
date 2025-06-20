# Legacy Code Inventory and Removal Plan

## 🎯 **Executive Summary**

This document provides a comprehensive inventory of all legacy code that does not follow the current **CrewAI Flow-based architecture** and presents a detailed implementation plan for removing these deprecated patterns. The inventory is organized by the three architectural pivots to ensure complete coverage.

### **Critical Context**
- **Current Architecture**: CrewAI Flow with specialized crews, manager agents, and hierarchical coordination
- **Legacy Patterns**: Heuristic-based logic, individual agents, and non-flow service patterns
- **Goal**: Complete removal of deprecated code to prevent regression and confusion

---

## 📋 **LEGACY CODE INVENTORY**

### **Category 1: Heuristic-Based Logic (Pivot 1 - DEPRECATED)**

#### **🚨 HIGH PRIORITY - Hard-Coded Rules and Static Logic**

##### **1.1 Strategy Analysis with Hard-Coded Weights**
- **File**: `backend/app/services/sixr_handlers/strategy_analyzer.py`
- **Size**: 20KB, 474 lines
- **Issues**: 
  - Hard-coded strategy weights and scoring rules
  - Static parameter weights instead of AI learning
  - Fixed optimal ranges and penalties
- **Code Examples**:
  ```python
  # Lines 60-95: Hard-coded strategy weights
  def _initialize_strategy_weights(self) -> Dict[SixRStrategy, Dict[str, float]]:
      return {
          SixRStrategy.REHOST: {
              "technical_complexity": 0.15,
              "business_criticality": 0.20,
              # ... more hard-coded weights
          }
      }
  ```
- **Replacement**: CrewAI Technical Debt Crew with AI-driven strategy analysis

##### **1.2 Field Mapping with Pattern Matching Heuristics**
- **File**: `backend/app/api/v1/endpoints/data_import/field_mapping.py`
- **Size**: Partial file with heuristic patterns
- **Issues**:
  - Pattern matching with hard-coded rules
  - Static confidence calculations
  - No learning from user feedback
- **Code Examples**:
  ```python
  # Lines 532-556: Hard-coded pattern matching
  def calculate_pattern_match(source_field: str, sample_value: str, all_values: list, pattern: dict) -> float:
      confidence = 0.0
      if pattern["source_pattern"].lower() in source_field.lower():
          confidence += 0.4  # Hard-coded confidence boost
  ```
- **Replacement**: CrewAI Field Mapping Crew with AI-driven semantic analysis

##### **1.3 Content Analysis with Static Heuristics**
- **File**: `backend/app/services/field_mapper_handlers/mapping_engine.py`
- **Size**: Partial file with heuristic content analysis
- **Issues**:
  - Hard-coded content analysis rules
  - Static memory/CPU range checks
  - No adaptive learning
- **Code Examples**:
  ```python
  # Lines 312-350: Hard-coded content heuristics
  def _analyze_content_match(self, canonical_field: str, sample_data: List[List[str]], column_index: int) -> float:
      if 'memory' in canonical_field.lower():
          if any(1 <= n <= 1024 for n in nums):  # Hard-coded memory range
              content_boost = 0.2  # Static confidence boost
  ```
- **Replacement**: CrewAI Field Mapping Crew with intelligent content analysis

##### **1.4 Validation Tools with Hard-Coded Alignment Checks**
- **File**: `backend/app/services/tools/sixr_handlers/validation_tools.py`
- **Size**: Partial file with static validation
- **Issues**:
  - Hard-coded cost alignment checks
  - Static strategy preferences
  - No learning from validation results
- **Code Examples**:
  ```python
  # Lines 94-124: Hard-coded cost alignment
  def _check_cost_alignment(self, recommendation: Dict[str, Any], validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
      if cost_sensitivity >= 4:
          if strategy in ["refactor", "rebuild"]:  # Hard-coded strategy rules
              check_result["score"] = 0.4
  ```
- **Replacement**: CrewAI Technical Debt Crew with AI-driven validation

##### **1.5 Analysis Tools with Static Parameter Scoring**
- **File**: `backend/app/services/tools/sixr_handlers/analysis_tools.py`
- **Size**: Partial file with static scoring
- **Issues**:
  - Hard-coded strategy preferences
  - Static parameter scoring rules
  - No adaptive intelligence
- **Code Examples**:
  ```python
  # Lines 253-294: Hard-coded parameter scoring
  def _score_parameter_for_strategy(self, param: str, value: float, strategy: str) -> float:
      strategy_preferences = {
          "rehost": {
              "technical_complexity": {"preferred": [1, 2, 3], "weight": 0.8},  # Static preferences
          }
      }
  ```
- **Replacement**: CrewAI Technical Debt Crew with intelligent parameter analysis

##### **1.6 Knowledge Base Patterns with Static Rules**
- **File**: `backend/app/knowledge_bases/field_mapping_patterns.json`
- **Size**: JSON file with static patterns
- **Issues**:
  - Static confidence patterns
  - Hard-coded validation rules
  - No learning integration
- **Code Examples**:
  ```json
  "confidence_patterns": {
    "high_confidence": {
      "exact_match": 1.0,
      "case_insensitive_match": 0.95  // Static confidence values
    }
  }
  ```
- **Replacement**: Dynamic knowledge bases updated by CrewAI agents

---

### **Category 2: Individual Agent Architecture (Pivot 2 - SUPERSEDED)**

#### **🚨 HIGH PRIORITY - Standalone Agents Without Crews**

##### **2.1 Discovery Agents (Individual Pattern)**
- **Directory**: `backend/app/services/discovery_agents/`
- **Total Size**: ~153KB across 5 files
- **Files**:
  - `data_source_intelligence_agent.py` (22KB, 497 lines)
  - `application_intelligence_agent.py` (32KB, 674 lines)
  - `dependency_intelligence_agent.py` (41KB, 869 lines)
  - `presentation_reviewer_agent.py` (33KB, 734 lines)
  - `application_discovery_agent.py` (25KB, 544 lines)
- **Issues**:
  - Individual agents without crew coordination
  - Direct agent-to-agent communication
  - No manager agent oversight
  - Missing collaboration patterns
- **Code Examples**:
  ```python
  # Individual agent pattern (DEPRECATED)
  class ApplicationDiscoveryAgent:
      def __init__(self):
          self.agent_id = "application_discovery"
          self.agent_name = "Application Discovery Agent"
          # No crew membership or manager coordination
  
  # Global instance pattern (DEPRECATED)
  application_discovery_agent = ApplicationDiscoveryAgent()
  ```
- **Replacement**: CrewAI Inventory Building Crew with Application Discovery Expert

##### **2.2 SixR Agents (Individual Pattern)**
- **Directory**: `backend/app/services/sixr_agents_handlers/`
- **Total Size**: ~43KB across 3 files
- **Files**:
  - `agent_manager.py` (8.9KB, 214 lines)
  - `response_handler.py` (18KB, 418 lines)
  - `task_coordinator.py` (16KB, 376 lines)
- **Issues**:
  - Individual agent management without crews
  - Task coordination without flow patterns
  - No hierarchical agent structure
- **Code Examples**:
  ```python
  # Individual agent creation (DEPRECATED)
  def _create_agents(self) -> Dict[str, Any]:
      agents = {}
      agents["discovery"] = Agent(
          role="6R Discovery Specialist",
          allow_delegation=False,  # No delegation patterns
          # No crew membership
      )
  ```
- **Replacement**: CrewAI Technical Debt Crew with proper crew structure

##### **2.3 SixR Agents Modular Service**
- **File**: `backend/app/services/sixr_agents_modular.py`
- **Size**: 12KB, 270 lines
- **Issues**:
  - Orchestrates individual agents instead of crews
  - No flow integration
  - Legacy compatibility layer
- **Code Examples**:
  ```python
  class SixRAnalysisAgents:
      def __init__(self, llm_service: Optional[Any] = None):
          self.agent_manager = AgentManagerHandler()  # Individual agent management
          self.agents = self.agent_manager.get_agents()  # Direct agent access
  ```
- **Replacement**: CrewAI Technical Debt Crew integration

##### **2.4 Agent Registry (Individual Agent Focus)**
- **File**: `backend/app/services/agent_registry.py`
- **Size**: 35KB, 815 lines
- **Issues**:
  - Registers individual agents instead of crews
  - No crew coordination tracking
  - Legacy agent registration patterns
- **Code Examples**:
  ```python
  # Individual agent registration (DEPRECATED)
  self.register_agent(AgentRegistration(
      agent_id="data_source_intelligence_001",
      name="Data Source Intelligence Agent",  # Individual agent
      # No crew membership information
  ))
  ```
- **Replacement**: CrewAI Flow crew registration system

---

### **Category 3: Non-Flow Service Patterns (Current Issues)**

#### **🔄 MEDIUM PRIORITY - Services Without CrewAI Flow Integration**

##### **3.1 Analysis Handlers (Non-Crew Pattern)**
- **Directory**: `backend/app/services/analysis_handlers/`
- **Total Size**: ~57KB across 3 files
- **Files**:
  - `placeholder_handler.py` (23KB, 574 lines)
  - `intelligence_engine.py` (18KB, 407 lines)
  - `core_analysis.py` (16KB, 385 lines)
- **Issues**:
  - Simple service classes without agent intelligence
  - No crew coordination
  - Placeholder logic instead of AI agents
- **Code Examples**:
  ```python
  class PlaceholderHandler:
      def placeholder_wave_planning(self, wave_data: Dict[str, Any]) -> Dict[str, Any]:
          # Simple logic instead of AI agents
          if total_apps <= 10:
              wave_count = 1  # Hard-coded logic
  ```
- **Replacement**: CrewAI Wave Planning Crew (future implementation)

##### **3.2 SixR Handlers (Non-Agent Pattern)**
- **Directory**: `backend/app/services/sixr_handlers/`
- **Total Size**: ~28KB across 4 files
- **Files**:
  - `recommendation_engine.py` (4.3KB, 108 lines)
  - `cost_calculator.py` (2.0KB, 64 lines)
  - `risk_assessor.py` (1.7KB, 45 lines)
- **Issues**:
  - Simple calculation services without AI intelligence
  - No agent-based analysis
  - Static algorithms
- **Replacement**: CrewAI Technical Debt Crew with AI-driven analysis

##### **3.3 Legacy CrewAI Flow Service**
- **File**: `backend/app/services/archive_crewai_flow_service.py`
- **Size**: 26KB, 609 lines
- **Issues**:
  - Archived flow service with outdated patterns
  - Individual agent orchestration
  - No proper crew structure
- **Code Examples**:
  ```python
  async def initiate_data_source_analysis(self, data_source: Dict[str, Any], context: RequestContext):
      # Direct agent calls without crews
      if not self.data_source_agent:
          return self._fallback_data_analysis()
  ```
- **Replacement**: Current CrewAI Flow implementation

##### **3.4 Legacy Discovery Flow**
- **File**: `backend/app/services/crewai_flows/discovery_flow.py`
- **Size**: Contains both current and legacy patterns
- **Issues**:
  - Mixed individual agent and crew patterns
  - Fallback methods using individual agents
  - Legacy initialization patterns
- **Code Examples**:
  ```python
  # Legacy individual agent initialization (DEPRECATED)
  def _initialize_discovery_agents(self):
      from app.services.discovery_agents.data_source_intelligence_agent import DataSourceIntelligenceAgent
      self.data_source_agent = DataSourceIntelligenceAgent()  # Individual agent
  
  # Legacy fallback methods (DEPRECATED)
  def _fallback_data_analysis(self):
      logger.info("Using fallback data analysis")  # Non-agent fallback
  ```
- **Replacement**: Pure CrewAI Flow implementation in `discovery_flow_modular.py`

---

### **Category 4: Legacy API Endpoints and Handlers**

#### **🔄 MEDIUM PRIORITY - Non-Flow API Patterns**

##### **4.1 Individual Agent API Endpoints**
- **Directory**: `backend/app/api/v1/endpoints/agents/`
- **Files**:
  - `discovery/router.py` and handlers
  - Individual agent status endpoints
- **Issues**:
  - Exposes individual agents instead of crews
  - No flow integration
  - Legacy agent communication patterns
- **Replacement**: CrewAI Flow status endpoints

##### **4.2 SixR Analysis Endpoints**
- **File**: `backend/app/api/v1/endpoints/sixr_handlers/analysis_endpoints.py`
- **Issues**:
  - Individual analysis without crew coordination
  - No flow integration
  - Legacy parameter handling
- **Replacement**: CrewAI Technical Debt Crew endpoints

##### **4.3 Legacy Discovery Endpoints**
- **File**: `backend/app/api/v1/discovery/discovery_flow.py`
- **Issues**:
  - Mixed flow and individual agent endpoints
  - Legacy agent analysis endpoints
  - Fallback to non-agent analysis
- **Code Examples**:
  ```python
  @router.post("/agent/analysis")  # Individual agent endpoint (DEPRECATED)
  async def agent_analysis(data: Dict[str, Any]):
      # Direct agent calls without flow coordination
  ```
- **Replacement**: Pure CrewAI Flow endpoints

---

### **Category 5: Frontend Legacy Patterns**

#### **🔄 LOW PRIORITY - Frontend Individual Agent Patterns**

##### **5.1 Individual Agent Hooks**
- **File**: `src/hooks/useAttributeMapping.ts`
- **Issues**:
  - Hooks for individual agent status
  - Legacy critical attributes endpoint
  - Static heuristic-based queries
- **Code Examples**:
  ```typescript
  // Legacy individual agent hook (DEPRECATED)
  export const useCriticalAttributes = () => {
    return useQuery<CriticalAttributesData>({
      queryKey: ['critical-attributes'],  // Static endpoint
      queryFn: async () => {
        const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS);
      }
    });
  };
  ```
- **Replacement**: CrewAI Flow state hooks

---

## 🚀 **IMPLEMENTATION PLAN**

### **Phase 1: Critical Heuristic Removal (Weeks 1-2)**

#### **Task 1.1: Remove Strategy Analyzer Heuristics**
- **Priority**: CRITICAL
- **Effort**: 2 days
- **Actions**:
  1. Delete `backend/app/services/sixr_handlers/strategy_analyzer.py`
  2. Remove all imports and references
  3. Update Technical Debt Crew to handle 6R strategy analysis
  4. Test strategy analysis through CrewAI agents
- **Files to Remove**:
  - `backend/app/services/sixr_handlers/strategy_analyzer.py`
- **Files to Update**:
  - `backend/app/services/crewai_flows/crews/technical_debt_crew.py`

#### **Task 1.2: Remove Field Mapping Heuristics**
- **Priority**: CRITICAL
- **Effort**: 1 day
- **Actions**:
  1. Remove heuristic pattern matching from field mapping endpoints
  2. Update Field Mapping Crew to handle all mapping logic
  3. Remove static confidence calculations
- **Files to Remove**:
  - Heuristic functions in `backend/app/api/v1/endpoints/data_import/field_mapping.py`
  - Static patterns in `backend/app/knowledge_bases/field_mapping_patterns.json`

#### **Task 1.3: Remove Content Analysis Heuristics**
- **Priority**: HIGH
- **Effort**: 1 day
- **Actions**:
  1. Remove static content analysis from mapping engine
  2. Replace with AI-driven content analysis in Field Mapping Crew

#### **Task 1.4: Remove Validation and Analysis Tool Heuristics**
- **Priority**: HIGH
- **Effort**: 1 day
- **Actions**:
  1. Delete validation tools with hard-coded rules
  2. Delete analysis tools with static scoring
  3. Replace with CrewAI agent intelligence
- **Files to Remove**:
  - `backend/app/services/tools/sixr_handlers/validation_tools.py`
  - `backend/app/services/tools/sixr_handlers/analysis_tools.py`

### **Phase 2: Individual Agent Removal (Weeks 3-4)**

#### **Task 2.1: Remove Discovery Agents Directory**
- **Priority**: HIGH
- **Effort**: 3 days
- **Actions**:
  1. Delete entire `backend/app/services/discovery_agents/` directory
  2. Remove all imports and references
  3. Update CrewAI crews to handle all discovery functionality
  4. Test discovery flow without individual agents
- **Files to Remove**:
  - `backend/app/services/discovery_agents/` (entire directory)

#### **Task 2.2: Remove SixR Agents Handlers**
- **Priority**: HIGH
- **Effort**: 2 days
- **Actions**:
  1. Delete `backend/app/services/sixr_agents_handlers/` directory
  2. Remove `backend/app/services/sixr_agents_modular.py`
  3. Update Technical Debt Crew to handle all 6R functionality
- **Files to Remove**:
  - `backend/app/services/sixr_agents_handlers/` (entire directory)
  - `backend/app/services/sixr_agents_modular.py`

#### **Task 2.3: Update Agent Registry for Crews**
- **Priority**: MEDIUM
- **Effort**: 2 days
- **Actions**:
  1. Refactor agent registry to track crews instead of individual agents
  2. Update registration patterns for CrewAI Flow architecture
  3. Remove individual agent registrations
- **Files to Update**:
  - `backend/app/services/agent_registry.py`

### **Phase 3: Service Pattern Modernization (Weeks 5-6)**

#### **Task 3.1: Remove Analysis Handlers**
- **Priority**: MEDIUM
- **Effort**: 2 days
- **Actions**:
  1. Delete `backend/app/services/analysis_handlers/` directory
  2. Remove `backend/app/services/analysis_modular.py`
  3. Replace with CrewAI crew intelligence
- **Files to Remove**:
  - `backend/app/services/analysis_handlers/` (entire directory)
  - `backend/app/services/analysis_modular.py`

#### **Task 3.2: Remove SixR Handlers**
- **Priority**: MEDIUM
- **Effort**: 2 days
- **Actions**:
  1. Delete remaining files in `backend/app/services/sixr_handlers/`
  2. Replace with Technical Debt Crew functionality
- **Files to Remove**:
  - `backend/app/services/sixr_handlers/recommendation_engine.py`
  - `backend/app/services/sixr_handlers/cost_calculator.py`
  - `backend/app/services/sixr_handlers/risk_assessor.py`

#### **Task 3.3: Clean Up Legacy Flow Services**
- **Priority**: MEDIUM
- **Effort**: 1 day
- **Actions**:
  1. Delete `backend/app/services/archive_crewai_flow_service.py`
  2. Remove legacy patterns from `discovery_flow.py`
  3. Ensure pure CrewAI Flow implementation
- **Files to Remove**:
  - `backend/app/services/archive_crewai_flow_service.py`

### **Phase 4: API Endpoint Cleanup (Week 7)**

#### **Task 4.1: Remove Individual Agent API Endpoints**
- **Priority**: MEDIUM
- **Effort**: 2 days
- **Actions**:
  1. Delete `backend/app/api/v1/endpoints/agents/` directory
  2. Remove individual agent routes from discovery endpoints
  3. Update to use only CrewAI Flow endpoints
- **Files to Remove**:
  - `backend/app/api/v1/endpoints/agents/` (entire directory)

#### **Task 4.2: Remove Legacy Analysis Endpoints**
- **Priority**: MEDIUM
- **Effort**: 1 day
- **Actions**:
  1. Remove legacy analysis endpoints
  2. Update to use CrewAI Flow endpoints only
- **Files to Remove**:
  - `backend/app/api/v1/endpoints/sixr_handlers/analysis_endpoints.py`

#### **Task 4.3: Clean Up Discovery Flow Endpoints**
- **Priority**: LOW
- **Effort**: 1 day
- **Actions**:
  1. Remove legacy agent analysis endpoints
  2. Keep only CrewAI Flow endpoints

### **Phase 5: Frontend Cleanup (Week 8)**

#### **Task 5.1: Remove Legacy Frontend Hooks**
- **Priority**: LOW
- **Effort**: 1 day
- **Actions**:
  1. Remove individual agent hooks
  2. Update to use only CrewAI Flow state hooks
- **Files to Update**:
  - `src/hooks/useAttributeMapping.ts`

#### **Task 5.2: Update Frontend Components**
- **Priority**: LOW
- **Effort**: 1 day
- **Actions**:
  1. Remove individual agent monitoring components
  2. Update to use crew monitoring components

### **Phase 6: Testing and Validation (Week 9)**

#### **Task 6.1: Comprehensive Testing**
- **Priority**: CRITICAL
- **Effort**: 3 days
- **Actions**:
  1. Test all CrewAI Flow functionality
  2. Verify no legacy code remains
  3. Validate crew coordination works properly
  4. Test error handling and fallbacks

#### **Task 6.2: Documentation Updates**
- **Priority**: HIGH
- **Effort**: 2 days
- **Actions**:
  1. Update all documentation to remove legacy references
  2. Update API documentation for CrewAI Flow endpoints only
  3. Update development guides

---

## 📊 **REMOVAL IMPACT ANALYSIS**

### **Files to Delete (Complete Removal)**
- **Total Size**: ~400KB across 50+ files
- **Directories to Remove**:
  - `backend/app/services/discovery_agents/` (153KB)
  - `backend/app/services/sixr_agents_handlers/` (43KB)
  - `backend/app/services/analysis_handlers/` (57KB)
  - `backend/app/services/sixr_handlers/` (28KB)
  - `backend/app/api/v1/endpoints/agents/` (size TBD)

### **Files to Update (Partial Changes)**
- **Major Updates**:
  - `backend/app/services/agent_registry.py` (35KB) - Refactor for crews
  - `backend/app/services/crewai_flows/discovery_flow.py` - Remove legacy methods
  - `backend/app/api/v1/endpoints/discovery.py` - Remove individual agent routes
  - Multiple CrewAI crew files - Add functionality from removed services

### **Risk Assessment**
- **High Risk**: Removing core discovery agents without proper crew replacement
- **Medium Risk**: API endpoint changes affecting frontend
- **Low Risk**: Removing heuristic handlers (already have crew replacements)

### **Mitigation Strategies**
1. **Incremental Removal**: Remove components in phases with testing between each phase
2. **Crew Enhancement**: Ensure CrewAI crews can handle all functionality before removal
3. **Fallback Maintenance**: Keep critical fallback mechanisms during transition
4. **Comprehensive Testing**: Test each phase thoroughly before proceeding

---

## 🎯 **SUCCESS CRITERIA**

### **Phase Completion Criteria**
1. **Phase 1**: All heuristic-based logic removed, CrewAI crews handle strategy and mapping
2. **Phase 2**: No individual agent instances, all functionality through crews
3. **Phase 3**: No legacy service patterns, pure CrewAI Flow architecture
4. **Phase 4**: Clean API endpoints exposing only CrewAI Flow functionality
5. **Phase 5**: Frontend uses only CrewAI Flow state management
6. **Phase 6**: 100% test coverage, comprehensive documentation

### **Final Validation**
- **Code Search**: No references to removed files or patterns
- **Import Validation**: No broken imports or missing dependencies
- **Functionality Test**: All platform features work through CrewAI Flow
- **Performance Test**: No performance degradation from legacy removal
- **Documentation**: Complete and accurate documentation of current architecture

### **Completion Metrics**
- **Code Reduction**: ~400KB of legacy code removed
- **Architecture Purity**: 100% CrewAI Flow-based implementation
- **Maintenance Burden**: Significantly reduced complexity
- **Developer Clarity**: Clear separation between current and legacy patterns eliminated

This comprehensive removal plan ensures the platform maintains only the current CrewAI Flow-based architecture, eliminating confusion and preventing regression to deprecated patterns. 