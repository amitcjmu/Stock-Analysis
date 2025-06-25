# AI Force Migration Platform - Discovery Flow Redesign Specification

## 🎯 Executive Summary

This document outlines the redesign of the Discovery Flow from a crew-heavy architecture to an **agent-first, crew-when-needed** approach. The new design prioritizes individual agent efficiency for deterministic tasks while strategically deploying crews for complex analysis requiring multiple perspectives.

**Key Design Principles:**
- **Agent-First**: Individual agents handle specialized, focused tasks
- **Progressive Intelligence**: "Think" → "Ponder More" escalation for deeper analysis
- **Human-in-the-Loop**: Agent clarifications and insights through UI panels
- **Strategic Crew Deployment**: Crews only when collaboration adds value

---

## 🏗️ Architecture Overview

### Current vs. Redesigned Flow

| Phase | Current Approach | Redesigned Approach | Rationale |
|-------|------------------|-------------------|-----------|
| Data Import Validation | Crew | **Individual Agent** | Deterministic security/PII scanning |
| Attribute Mapping | Crew | **Individual Agent** | Focused field mapping with confidence scoring |
| Data Cleansing | Crew | **Individual Agent** | Rule-based standardization post-mapping |
| Asset Inventory | Crew | **Individual Agent** | Classification with learned patterns |
| Dependency Analysis | Crew | **Agent + Optional Crew** | Start with agent, escalate to crew if needed |
| Tech Debt Analysis | Crew | **Agent + Optional Crew** | Start with agent, escalate to crew if needed |

### Flow Execution Pattern

```
Data Import → Attribute Mapping → Data Cleansing → [Parallel Execution]
                                                      ├── Asset Inventory Agent
                                                      ├── Dependency Analysis Agent
                                                      └── Tech Debt Analysis Agent
                                                           ↓
                                              [User Interaction: "Think" Buttons]
                                                           ↓
                                              [Optional Crew Escalation: "Ponder More"]
```

---

## 🤖 Agent Specifications

### 1. Data Import Validation Agent

**Role:** "Enterprise Data Security and Validation Specialist"

**Goal:** "Perform comprehensive security scanning, PII detection, and data structure validation to ensure enterprise-grade data safety and compliance before processing"

**Backstory:** "You are a cybersecurity expert with 15+ years of experience in enterprise data governance. You specialize in identifying sensitive information, detecting security threats, and validating data structures. You have a methodical approach to data validation that prioritizes security without compromising processing efficiency."

**Key Capabilities:**
- PII/PHI detection and classification
- Security threat assessment
- File format validation
- Data structure analysis
- Compliance checking (GDPR, HIPAA, SOX)

**Tools:**
- File analysis tools
- Security scanning utilities
- Pattern recognition engines
- Compliance validation frameworks

**Output Format:** Structured validation report with security clearance status

---

### 2. Attribute Mapping Agent

**Role:** "Enterprise Asset Schema Mapping Specialist"

**Goal:** "Intelligently map source data fields to the 50-60+ fields in the assets table, with primary focus on the 20+ critical migration attributes, ensuring comprehensive field identification for downstream processing"

**Backstory:** "You are a data migration expert with deep knowledge of enterprise asset inventories and database schemas. You've mapped thousands of different data sources to standardized migration schemas. You excel at pattern recognition and can identify field relationships even when naming conventions vary significantly across organizations. You understand both the critical migration attributes and the full asset table schema."

**Key Capabilities:**
- Field pattern recognition across full asset table schema (50-60+ fields)
- Confidence scoring (0-100%) for all field mappings
- Critical attribute mapping prioritization (Identity, Business, Technical, Network, etc.)
- Secondary field mapping for comprehensive data capture
- Learning from user feedback and mapping corrections
- Ambiguity detection and flagging for unclear mappings

**Tools:**
- Field mapping engine with full asset schema knowledge
- Pattern recognition algorithms for field similarity
- Confidence scoring models for mapping accuracy
- Learning feedback integration for continuous improvement

**Output Format:** Comprehensive field mapping dictionary with confidence scores for all identified fields

**UI Integration:**
- **Agent Clarifications Panel (Existing):** MCQ for ambiguous field mappings using existing Agent-UI-monitor panel
- **Agent Insights Panel (Existing):** Overall mapping confidence and recommendations through existing interface

---

### 3. Data Cleansing Agent

**Role:** "Enterprise Data Standardization and Bulk Processing Specialist"

**Goal:** "Apply intelligent data cleansing and standardization rules based on confirmed field mappings, perform bulk data population for missing values, and execute mass data edits based on user clarifications"

**Backstory:** "You are a data quality expert who understands that clean data is the foundation of successful migrations. With the field mappings confirmed, you can apply precise standardization rules. You excel at bulk operations, pattern-based data population, and mass corrections. You balance automation with accuracy, using user clarifications to guide bulk transformations across entire datasets."

**Key Capabilities:**
- Format standardization (dates, currencies, addresses)
- Data validation and correction
- **Bulk missing data population** based on patterns and user guidance
- **Mass data editing** operations from user clarifications
- Quality metrics calculation
- Duplicate detection and resolution
- Completeness assessment and gap filling
- Pattern-based data inference for missing values

**Tools:**
- Data validation engines
- Format standardization utilities
- **Bulk data processing engines**
- **Mass edit transformation utilities**
- Quality assessment frameworks
- Deduplication algorithms
- Pattern recognition for data inference

**Output Format:** Cleaned dataset with quality metrics report and bulk operation summaries

**UI Integration:**
- **Agent Clarifications Panel (Existing):** User guidance for bulk operations and mass edits through existing Agent-UI-monitor panel
- **Agent Insights Panel (Existing):** Data quality metrics and bulk operation recommendations

---

### 4. Asset Inventory Agent

**Role:** "Enterprise Asset Classification and Inventory Specialist"

**Goal:** "Classify and categorize assets (servers, applications, devices) with high accuracy using AI-powered classification models and learned organizational patterns"

**Backstory:** "You are an IT asset management expert with experience across diverse enterprise environments. You understand how different organizations structure their IT assets and can quickly identify asset types, criticality levels, and business relationships. You learn from each engagement to improve classification accuracy."

**Key Capabilities:**
- Asset type classification (servers, applications, devices, databases)
- Criticality assessment
- Business function mapping
- Environment classification (prod, dev, test)
- Asset relationship identification

**Tools:**
- Asset classification models
- Pattern learning engines
- Business function mapping tools
- Environment detection utilities

**Output Format:** Structured asset inventory with classifications

**UI Integration:**
- **Think Button:** Escalate to Asset Intelligence Crew for complex classifications
- **Agent Insights (Existing):** Asset distribution analysis and anomaly detection through existing Agent-UI-monitor panel

---

### 5. Dependency Analysis Agent

**Role:** "Application and Infrastructure Dependency Mapping Specialist"

**Goal:** "Identify and map critical dependencies between applications, servers, and infrastructure components to support migration planning and risk assessment"

**Backstory:** "You are a systems architect with deep understanding of enterprise application landscapes. You excel at identifying both obvious and hidden dependencies. You understand that missed dependencies are the leading cause of migration failures, so you approach this task with methodical precision."

**Key Capabilities:**
- Application dependency mapping
- Infrastructure dependency identification
- Network dependency analysis
- Database relationship mapping
- Critical path identification

**Tools:**
- Network analysis tools
- Application scanning utilities
- Database relationship analyzers
- Dependency visualization engines

**Output Format:** Dependency map with criticality ratings

**UI Integration:**
- **Think Button:** Escalate to Dependency Analysis Crew for complex enterprise architectures
- **Ponder More:** Enable crew collaboration for comprehensive dependency analysis
- **Agent Insights (Existing):** Dependency mapping insights through existing Agent-UI-monitor panel

---

### 6. Tech Debt Analysis Agent

**Role:** "Technical Debt Assessment and Modernization Opportunity Specialist"

**Goal:** "Assess technical debt levels, identify modernization opportunities, and provide 6R strategy recommendations based on current technology stack analysis"

**Backstory:** "You are a technology modernization consultant who has guided hundreds of legacy system transformations. You can quickly assess technical debt indicators and identify the best modernization approach. You balance technical possibilities with business realities."

**Key Capabilities:**
- Technical debt scoring
- Modernization opportunity identification
- 6R strategy recommendation (Rehost, Replatform, Refactor, etc.)
- Technology stack analysis
- Risk and complexity assessment

**Tools:**
- Technology assessment frameworks
- Modernization pattern libraries
- 6R decision engines
- Risk assessment models

**Output Format:** Tech debt report with modernization recommendations

**UI Integration:**
- **Think Button:** Escalate to Tech Debt Analysis Crew for complex modernization decisions
- **Ponder More:** Enable crew collaboration for comprehensive technology strategy
- **Agent Insights (Existing):** Tech debt analysis and modernization recommendations through existing Agent-UI-monitor panel

---

## 👥 Strategic Crew Specifications

### 1. Asset Intelligence Crew

**Activation Trigger:** User clicks "Think" on Asset Inventory page

**Composition:**
- **Asset Classification Expert**: Specialized in complex asset categorization
- **Business Context Analyst**: Maps assets to business functions and criticality
- **Environment Specialist**: Identifies production, development, and testing environments

**Collaboration Pattern:** Sequential with feedback loops

**Use Case:** When asset classification confidence is low or when assets don't fit standard categories

**Tools:**
- MCP knowledge repository search
- Historical classification patterns
- Industry-specific asset databases

---

### 2. Dependency Analysis Crew

**Activation Trigger:** User clicks "Think" on Dependencies page

**Composition:**
- **Network Architecture Specialist**: Focuses on network-level dependencies
- **Application Integration Expert**: Identifies application-to-application dependencies
- **Infrastructure Dependencies Analyst**: Maps infrastructure and platform dependencies

**Collaboration Pattern:** Parallel analysis with synthesis

**Use Case:** Complex enterprise architectures with multiple integration patterns

**Escalation:** "Ponder More" enables delegation and creative problem-solving

---

### 3. Tech Debt Analysis Crew

**Activation Trigger:** User clicks "Think" on Tech Debt page

**Composition:**
- **Legacy Systems Modernization Expert**: Specializes in legacy technology assessment
- **Cloud Migration Strategist**: Focuses on cloud-native modernization opportunities
- **Risk Assessment Specialist**: Evaluates modernization risks and business impact

**Collaboration Pattern:** Debate-driven consensus building

**Use Case:** Complex technology stacks requiring multiple expert perspectives

**Escalation:** "Ponder More" enables comprehensive technology strategy development

---

## 🔄 User Interaction Design

### Existing Agent-UI-Monitor Panel Integration

**Current Status:** Fully functional Agent-UI-monitor panel already exists in codebase

**Integration Approach:** Leverage existing panel components instead of rebuilding

#### **Agent Clarifications Panel (Top - Existing)**

**Purpose:** Resolve agent uncertainties through user input using existing interface

**Format:** Multiple Choice Questions (MCQ) through existing Agent-UI-monitor

**Examples:**
- "Field 'SYS_ENV' appears to contain environment data. Which asset table field should this map to?"
  - [ ] Environment Type (critical attribute)
  - [ ] System Category (secondary field)
  - [ ] Application Tier (secondary field)
  - [ ] Other asset table field (specify)

**Bulk Operations Examples:**
- "Found 150 records with missing 'Environment' data. How should we populate these?"
  - [ ] Infer from hostname patterns
  - [ ] Set all to 'Production' (most common)
  - [ ] Leave blank for manual review
  - [ ] Apply custom rule (specify)

**Behavior:** 
- Questions appear as agents encounter ambiguities
- User selections immediately update agent knowledge
- Progress indicator shows remaining questions
- **Existing functionality preserved and enhanced**

#### **Agent Insights Panel (Bottom - Existing)**

**Purpose:** Provide analysis-specific insights and actionable items through existing interface

**Content:**
- Overall confidence scores
- Data quality metrics
- Anomaly detection results
- Actionable recommendations
- **Bulk operation summaries**

**User Feedback:**
- Thumbs up/down on insights (existing functionality)
- Correction suggestions (existing functionality)
- Additional context provision (existing functionality)
- **Mass edit confirmations for bulk operations**

### Think/Ponder More Buttons

**Think Button:**
- **Label:** "Think" (initial state)
- **Action:** Escalate current page data to relevant crew
- **Processing:** Show crew collaboration progress
- **Result:** Enhanced analysis with crew insights
- **New Label:** "Ponder More"

**Ponder More Button:**
- **Label:** "Ponder More" (after Think is complete)
- **Action:** Enable delegation and creative collaboration
- **Processing:** Show extended crew deliberation
- **Result:** Comprehensive analysis with multiple perspectives
- **Expectation:** User accepts longer processing time for deeper insights

---

## 📊 Flow State Management

### Enhanced State Schema

```python
class EnhancedDiscoveryFlowState(BaseModel):
    # Core identification
    flow_id: str
    session_id: str
    client_account_id: int
    engagement_id: int
    user_id: str
    
    # Processing data
    raw_data: List[Dict[str, Any]] = []
    field_mappings: Dict[str, Any] = {}
    cleaned_data: List[Dict[str, Any]] = []
    asset_inventory: Dict[str, Any] = {}
    dependencies: Dict[str, Any] = {}
    technical_debt: Dict[str, Any] = {}
    
    # Agent confidence and feedback
    agent_confidences: Dict[str, float] = {}
    user_clarifications: Dict[str, Any] = {}
    agent_insights: Dict[str, List[str]] = {}
    
    # Crew escalation tracking
    crew_escalations: Dict[str, bool] = {}
    crew_results: Dict[str, Any] = {}
    
    # User interaction state
    current_page: str = "data_import"
    pending_clarifications: List[Dict[str, Any]] = []
    completed_clarifications: List[Dict[str, Any]] = []
    
    # Flow control
    status: str = "running"
    current_phase: str = "initialization"
    errors: List[str] = []
    warnings: List[str] = []
```

---

## 🚀 Performance Expectations

### Processing Time Targets

| Phase | Agent Processing | Crew Escalation | Ponder More |
|-------|------------------|------------------|-------------|
| Data Import Validation | 5-10 seconds | N/A | N/A |
| Attribute Mapping | 10-15 seconds | +30 seconds | +60 seconds |
| Data Cleansing | 5-10 seconds | N/A | N/A |
| Asset Inventory | 15-20 seconds | +45 seconds | +90 seconds |
| Dependency Analysis | 20-25 seconds | +60 seconds | +120 seconds |
| Tech Debt Analysis | 15-20 seconds | +45 seconds | +90 seconds |

**Total Initial Processing:** 70-100 seconds (vs. current 30-45 seconds)
**With User Engagement:** Variable based on clarifications and escalations

### Quality Improvements Expected

- **Accuracy:** 15-20% improvement through user clarifications
- **Confidence:** Higher confidence scores through agent specialization
- **Learning:** Continuous improvement through feedback integration
- **User Satisfaction:** Better control over depth vs. speed trade-offs

---

## 🔧 Technical Implementation Strategy

### Phase 1: Agent Extraction and Specialization

**Goal:** Convert existing crews to specialized individual agents

**Tasks:**
1. Extract agent definitions from existing crews
2. Enhance agent roles, goals, and backstories
3. Implement confidence scoring for all agents
4. Add agent clarification mechanisms
5. Create agent insights generation

**Timeline:** 2 weeks

### Phase 2: UI Integration and User Interaction

**Goal:** Implement agent clarifications and insights panels

**Tasks:**
1. Create agent clarifications MCQ system
2. Implement agent insights display
3. Add Think/Ponder More button functionality
4. Integrate user feedback loops
5. Add progress tracking and notifications

**Timeline:** 2 weeks

### Phase 3: Strategic Crew Implementation

**Goal:** Implement crew escalation system

**Tasks:**
1. Create Asset Intelligence Crew
2. Create Dependency Analysis Crew  
3. Create Tech Debt Analysis Crew
4. Implement crew escalation triggers
5. Add delegation and collaboration features

**Timeline:** 2 weeks

### Phase 4: Performance Optimization and Learning

**Goal:** Optimize performance and enable learning

**Tasks:**
1. Implement parallel agent execution where possible
2. Add intelligent caching for crew results
3. Enable agent learning from user feedback
4. Optimize crew collaboration patterns
5. Add performance monitoring and analytics

**Timeline:** 2 weeks

---

## 📈 Success Metrics

### Primary Metrics

1. **User Engagement:** 
   - Clarification response rate > 90%
   - Think button usage > 60%
   - Ponder More usage > 30%

2. **Accuracy Improvement:**
   - Field mapping accuracy: +20%
   - Asset classification accuracy: +15%
   - Dependency identification completeness: +25%

3. **User Satisfaction:**
   - Control over process depth: 4.5/5
   - Clarity of agent insights: 4.5/5
   - Overall experience improvement: 4.0/5

### Secondary Metrics

1. **Performance Balance:**
   - Initial processing time: 70-100 seconds
   - User clarification time: < 30 seconds average
   - Crew escalation success rate: > 85%

2. **Learning Effectiveness:**
   - Agent confidence improvement over time
   - Reduction in clarification frequency
   - Improvement in crew escalation relevance

---

## 🎯 Conclusion

This redesign transforms the Discovery Flow from a crew-heavy architecture to an intelligent, user-centric system that balances speed with accuracy. By prioritizing individual agent efficiency and providing strategic crew escalation, we create a system that:

- **Respects User Time:** Fast initial processing with optional depth
- **Maximizes Accuracy:** User clarifications and expert crew analysis
- **Enables Learning:** Continuous improvement through feedback
- **Provides Control:** User decides when to invest time for better results

The agent-first approach aligns with CrewAI best practices while the progressive intelligence model ("Think" → "Ponder More") gives users control over the speed vs. accuracy trade-off.

---

**Next Steps:** Review and approve this specification, then proceed with the detailed execution plan for implementation. 