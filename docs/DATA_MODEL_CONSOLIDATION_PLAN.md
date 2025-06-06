# Data Model Consolidation & Agent Learning Enhancement Plan

## 🎯 **Executive Summary**

This document addresses critical architectural issues in the AI Force Migration Platform where disconnected data models and non-functional agent learning are preventing the platform from achieving its agentic intelligence goals.

### **Core Problems Identified**

1. **Dual Asset Models**: Two disconnected asset tables (`assets` and `cmdb_assets`) serving similar purposes with different schemas
2. **Data Fragmentation**: All data (56 assets) stored in `cmdb_assets` while `assets` table is empty, causing frontend/backend confusion
3. **Non-Functional Agent Learning**: Learning tables are empty (0 records) - agents aren't storing or retrieving patterns
4. **Application Detection Failure**: Agents failing to automatically classify applications from asset_name and metadata
5. **Attribute Mapping Regression**: Manual mappings not being learned, requiring repeated manual intervention

---

## 📊 **Current State Analysis**

### **Database Schema Issues**

#### **Asset Data Distribution**
- **`migration.assets`**: 0 records (76 columns, comprehensive schema)
- **`migration.cmdb_assets`**: 56 records (51 columns, limited schema)
- **`migration.mapping_learning_patterns`**: 0 records (learning not functioning)
- **`migration.import_field_mappings`**: 0 records (mapping history lost)

#### **Schema Comparison**

| Feature | assets | cmdb_assets | Issue |
|---------|--------|-------------|--------|
| **Row Count** | 0 | 56 | All data in wrong table |
| **Application Fields** | ✅ application_id, programming_language, framework | ❌ Only application_name | Limited app classification |
| **AI Fields** | ✅ ai_recommendations, confidence_score, strategy_rationale | ❌ Missing | No AI insights stored |
| **Learning Fields** | ✅ ai_confidence_score, last_ai_analysis | ❌ Missing | No learning tracking |
| **Complex Attributes** | ✅ 76 comprehensive fields | ❌ 51 basic fields | Reduced analytics capability |
| **Multi-tenant** | ✅ UUID-based | ✅ UUID-based | Both support multi-tenancy |

### **Agent Learning Breakdown**

#### **Learning Infrastructure Status**
```sql
-- Current Learning Table Status (ALL EMPTY)
mapping_learning_patterns: 0 records  -- Should store field mapping patterns
import_field_mappings: 0 records       -- Should store successful mappings
cmdb_asset_embeddings: ? records       -- Vector embeddings for AI
asset_tags: ? records                  -- AI-generated tags
```

#### **Missing Learning Capabilities**
1. **Field Mapping Intelligence**: No storage of successful source→target mappings
2. **Pattern Recognition**: No learned patterns from asset names/data for classification
3. **User Feedback Integration**: Manual corrections not being captured
4. **Cross-Session Learning**: No persistence of insights between import sessions

---

## 🏗️ **Proposed Solution Architecture**

### **Phase 1: Data Model Unification (Week 1)**

#### **1.1 Master Asset Model Selection**
**Decision**: Use `assets` table as the single source of truth
**Rationale**: 
- More comprehensive schema (76 vs 51 columns)
- Better application classification fields
- Enhanced AI insight storage
- Comprehensive business context fields

#### **1.2 Data Migration Strategy**
```sql
-- Step 1: Migrate data from cmdb_assets to assets
INSERT INTO migration.assets (
    name, hostname, asset_type, description, ip_address, 
    environment, operating_system, cpu_cores, memory_gb, storage_gb,
    business_owner, department, application_name as asset_name,
    technology_stack as programming_language, criticality as business_criticality,
    migration_priority, migration_complexity, six_r_strategy,
    client_account_id, engagement_id, created_at, updated_at
) 
SELECT 
    name, hostname, asset_type, description, ip_address,
    environment, operating_system, cpu_cores, memory_gb, storage_gb,
    business_owner, department, application_name,
    technology_stack, criticality,
    migration_priority, migration_complexity, six_r_strategy,
    client_account_id, engagement_id, created_at, updated_at
FROM migration.cmdb_assets;

-- Step 2: Update foreign key references
UPDATE migration.asset_tags SET asset_id = (
    SELECT a.id FROM migration.assets a 
    WHERE a.name = (SELECT c.name FROM migration.cmdb_assets c WHERE c.id = asset_tags.cmdb_asset_id)
);

-- Step 3: Deprecate cmdb_assets (keep for transition period)
ALTER TABLE migration.cmdb_assets ADD COLUMN migrated_to_assets_id INTEGER;
```

#### **1.3 Application Model Integration**
```python
# Enhanced Asset Model with Application Intelligence
class Asset(Base):
    # Existing fields...
    
    # Enhanced Application Detection Fields
    application_name = Column(String(255))  # From asset_name parsing
    application_type = Column(String(100))  # Web, Database, Service, etc.
    application_version = Column(String(50))
    programming_language = Column(String(100))
    framework = Column(String(100))
    technology_stack = Column(String(255))
    
    # AI-Driven Classification
    intelligent_asset_type = Column(String(100))  # AI-determined type
    classification_confidence = Column(Float)     # AI confidence score
    classification_method = Column(String(50))    # rule_based, ml_model, pattern_match
    last_classification_update = Column(DateTime)
    
    # Learning Integration
    ai_insights = Column(JSON)                    # Learned patterns applied
    manual_corrections = Column(JSON)             # User feedback history
    learning_pattern_ids = Column(JSON)          # Applied learning patterns
```

### **Phase 2: Agent Learning Infrastructure (Week 2)**

#### **2.1 Enhanced Learning Models**

```python
class MappingLearningPattern(Base):
    """Stores successful field mapping patterns for future use."""
    __tablename__ = "mapping_learning_patterns"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID, ForeignKey('client_accounts.id'))
    
    # Pattern Definition
    source_field_pattern = Column(String(255))    # e.g., "DR_TIER", "Environment_Type"
    content_pattern = Column(String(500))         # e.g., "Critical|High|Medium|Low"
    target_field = Column(String(255))           # e.g., "business_criticality"
    
    # Learning Metrics
    pattern_confidence = Column(Float)            # 0.0-1.0 confidence
    success_count = Column(Integer, default=1)   # Times successfully applied
    failure_count = Column(Integer, default=0)   # Times failed
    
    # Context
    learned_from_mapping_id = Column(UUID, ForeignKey('import_field_mappings.id'))
    user_feedback = Column(JSON)                  # User corrections/confirmations
    
    # Pattern Metadata
    matching_rules = Column(JSON)                 # Regex/fuzzy match rules
    transformation_hints = Column(JSON)          # Data transformation logic
    quality_checks = Column(JSON)                # Validation rules
    
    # Application
    times_applied = Column(Integer, default=0)
    last_applied_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class AssetClassificationPattern(Base):
    """Stores patterns for automatic asset classification."""
    __tablename__ = "asset_classification_patterns"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID, ForeignKey('client_accounts.id'))
    
    # Classification Rule
    pattern_type = Column(String(50))             # name_pattern, technology_stack, port_analysis
    pattern_value = Column(String(500))          # Regex or matching criteria
    target_classification = Column(JSON)         # {asset_type, application_type, technology_stack}
    
    # Learning History
    confidence_score = Column(Float)             # Pattern reliability
    examples_learned_from = Column(JSON)        # Sample assets that created this pattern
    user_confirmations = Column(Integer, default=0)
    user_rejections = Column(Integer, default=0)
    
    # Application Context
    applicable_environments = Column(JSON)       # Where this pattern applies
    exclusion_patterns = Column(JSON)           # When NOT to apply
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

#### **2.2 Agent Learning Services**

```python
class AgentLearningService:
    """Centralized agent learning and pattern management."""
    
    async def learn_from_mapping(self, mapping_event: FieldMappingEvent):
        """Learn patterns from successful field mappings."""
        # Extract patterns from source field names and values
        patterns = self._extract_field_patterns(mapping_event)
        
        # Store or update learning patterns
        for pattern in patterns:
            await self._update_learning_pattern(pattern)
            
        # Update agent knowledge
        await self._notify_mapping_agents(patterns)
    
    async def learn_from_classification(self, classification_event: ClassificationEvent):
        """Learn from asset classification events."""
        if classification_event.user_corrected:
            # User provided feedback - high value learning
            await self._store_classification_correction(classification_event)
        
        # Extract naming and attribute patterns
        patterns = self._extract_classification_patterns(classification_event)
        await self._update_classification_patterns(patterns)
    
    async def suggest_field_mapping(self, source_field: str, sample_values: List[str]) -> List[MappingSuggestion]:
        """Use learned patterns to suggest field mappings."""
        # Query learning patterns for similar fields
        patterns = await self._find_matching_patterns(source_field, sample_values)
        
        # Score suggestions by confidence
        suggestions = []
        for pattern in patterns:
            confidence = self._calculate_suggestion_confidence(pattern, sample_values)
            suggestions.append(MappingSuggestion(
                target_field=pattern.target_field,
                confidence=confidence,
                reasoning=pattern.matching_rules,
                examples=pattern.user_feedback
            ))
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    async def classify_asset_automatically(self, asset_data: dict) -> AssetClassification:
        """Use learned patterns to classify assets automatically."""
        # Apply name-based patterns
        name_classification = await self._classify_by_name_patterns(asset_data.get('name', ''))
        
        # Apply technology stack patterns
        tech_classification = await self._classify_by_technology_patterns(asset_data)
        
        # Apply port/service patterns
        service_classification = await self._classify_by_service_patterns(asset_data)
        
        # Combine classifications with confidence scoring
        final_classification = self._combine_classifications([
            name_classification, tech_classification, service_classification
        ])
        
        return final_classification
```

### **Phase 3: Enhanced Agent Architecture (Week 3)**

#### **3.1 Learning-Enabled Discovery Agents**

```python
class EnhancedAssetDiscoveryAgent:
    """Asset discovery with learning capabilities."""
    
    def __init__(self):
        self.learning_service = AgentLearningService()
        self.classification_patterns = {}
        self.field_mapping_patterns = {}
    
    async def analyze_asset(self, asset_data: dict) -> AssetAnalysis:
        """Analyze asset with learned intelligence."""
        # Get learned classification suggestions
        classification = await self.learning_service.classify_asset_automatically(asset_data)
        
        # Apply learned field mappings
        enhanced_data = await self._apply_learned_mappings(asset_data)
        
        # Extract application characteristics
        app_analysis = await self._analyze_application_patterns(enhanced_data)
        
        return AssetAnalysis(
            asset_type=classification.asset_type,
            application_type=classification.application_type,
            confidence=classification.confidence,
            enhanced_attributes=enhanced_data,
            application_insights=app_analysis,
            learning_patterns_applied=classification.patterns_used
        )
    
    async def _analyze_application_patterns(self, asset_data: dict) -> ApplicationAnalysis:
        """Enhanced application detection using learned patterns."""
        name = asset_data.get('name', '').lower()
        
        # Apply learned naming patterns
        for pattern in await self._get_application_patterns():
            if pattern.matches(name):
                return ApplicationAnalysis(
                    detected_application=pattern.application_name,
                    application_type=pattern.application_type,
                    technology_stack=pattern.technology_stack,
                    confidence=pattern.confidence_score,
                    detection_method="learned_pattern",
                    pattern_id=pattern.id
                )
        
        # Apply heuristic analysis as fallback
        return await self._heuristic_application_analysis(asset_data)
```

#### **3.2 Learning Integration in CrewAI Agents**

```python
from crewai import Agent, Task, Crew
from crewai_tools import BaseTool

class LearningAssetClassificationTool(BaseTool):
    name: str = "learning_asset_classification"
    description: str = "Classify assets using learned patterns and user feedback"
    
    def __init__(self):
        super().__init__()
        self.learning_service = AgentLearningService()
    
    def _run(self, asset_data: str) -> str:
        """Run asset classification with learning."""
        import json
        data = json.loads(asset_data)
        
        # Get learned classification
        classification = asyncio.run(
            self.learning_service.classify_asset_automatically(data)
        )
        
        # If high confidence, return learned classification
        if classification.confidence > 0.8:
            return f"Asset classified as {classification.asset_type} with {classification.confidence:.1%} confidence using learned patterns: {classification.patterns_used}"
        
        # If low confidence, use AI reasoning
        return self._ai_classification_with_learning_context(data, classification)
    
    def _ai_classification_with_learning_context(self, asset_data: dict, learned_classification: AssetClassification) -> str:
        """Use AI with learning context for complex cases."""
        context = f"""
        Asset Data: {asset_data}
        
        Learned Patterns Suggest: {learned_classification.asset_type} (confidence: {learned_classification.confidence:.1%})
        Patterns Used: {learned_classification.patterns_used}
        
        Please analyze this asset and provide classification, considering the learned patterns but using your reasoning for final decision.
        If you disagree with learned patterns, explain why.
        """
        
        # Use CrewAI agent reasoning here
        return self._use_ai_reasoning(context)

# Enhanced Asset Discovery Agent with Learning
asset_discovery_agent = Agent(
    role='Senior Asset Discovery Specialist with Learning Capabilities',
    goal='Discover and classify assets using learned patterns from previous successful classifications',
    backstory="""You are an expert asset discovery specialist who learns from past 
    classification patterns and user feedback. You combine AI reasoning with learned 
    organizational patterns to provide accurate asset classification.""",
    tools=[
        LearningAssetClassificationTool(),
        LearningFieldMappingTool(),
        ApplicationDetectionTool()
    ],
    memory=True,  # Enable agent memory
    max_iter=3,
    allow_delegation=False
)
```

### **Phase 4: Application Detection Enhancement (Week 4)**

#### **4.1 Enhanced Application Detection Logic**

```python
class ApplicationDetectionEngine:
    """Advanced application detection using multiple strategies."""
    
    def __init__(self):
        self.detection_strategies = [
            NamePatternDetector(),
            TechnologyStackDetector(),
            ServicePortDetector(),
            DirectoryStructureDetector(),
            ProcessDetector()
        ]
    
    async def detect_applications(self, asset_data: dict) -> List[ApplicationDetection]:
        """Multi-strategy application detection."""
        detections = []
        
        for strategy in self.detection_strategies:
            detection = await strategy.detect(asset_data)
            if detection.confidence > 0.5:
                detections.append(detection)
        
        # Combine and rank detections
        final_detections = self._combine_detections(detections)
        
        # Learn from successful detections
        await self._learn_from_detections(asset_data, final_detections)
        
        return final_detections
    
    async def _learn_from_detections(self, asset_data: dict, detections: List[ApplicationDetection]):
        """Store successful detection patterns for future use."""
        for detection in detections:
            if detection.confidence > 0.8:  # High confidence detections
                pattern = AssetClassificationPattern(
                    pattern_type=detection.strategy_type,
                    pattern_value=detection.pattern_matched,
                    target_classification={
                        "application_type": detection.application_type,
                        "technology_stack": detection.technology_stack
                    },
                    confidence_score=detection.confidence,
                    examples_learned_from=[asset_data]
                )
                await self._store_classification_pattern(pattern)

class NamePatternDetector:
    """Detect applications from asset naming patterns."""
    
    def __init__(self):
        # Load learned naming patterns
        self.learned_patterns = []
        self.builtin_patterns = [
            (r'.*sql.*|.*database.*|.*db.*', 'database', 'Database Service'),
            (r'.*web.*|.*apache.*|.*nginx.*|.*iis.*', 'web_server', 'Web Server'),
            (r'.*app.*|.*application.*', 'application', 'Application Server'),
            (r'.*exchange.*|.*mail.*|.*smtp.*', 'email', 'Email Server'),
            (r'.*sharepoint.*|.*portal.*', 'collaboration', 'Collaboration Platform')
        ]
    
    async def detect(self, asset_data: dict) -> ApplicationDetection:
        """Detect application type from asset name."""
        name = asset_data.get('name', '').lower()
        hostname = asset_data.get('hostname', '').lower()
        
        # Check learned patterns first (higher priority)
        for pattern in self.learned_patterns:
            if pattern.matches(name) or pattern.matches(hostname):
                return ApplicationDetection(
                    application_type=pattern.application_type,
                    technology_stack=pattern.technology_stack,
                    confidence=pattern.confidence_score,
                    strategy_type="learned_name_pattern",
                    pattern_matched=pattern.pattern_value,
                    detection_source="learned_intelligence"
                )
        
        # Fallback to builtin patterns
        for pattern, app_type, tech_stack in self.builtin_patterns:
            import re
            if re.search(pattern, name) or re.search(pattern, hostname):
                return ApplicationDetection(
                    application_type=app_type,
                    technology_stack=tech_stack,
                    confidence=0.7,  # Medium confidence for builtin patterns
                    strategy_type="builtin_name_pattern",
                    pattern_matched=pattern,
                    detection_source="builtin_rules"
                )
        
        return ApplicationDetection(confidence=0.0)  # No detection
```

---

## 🚀 **Implementation Roadmap**

### **Week 1: Data Model Unification**
- [x] **Day 1-2**: Analyze current schema differences
- [ ] **Day 3**: Create data migration scripts
- [ ] **Day 4**: Execute data migration (cmdb_assets → assets)
- [ ] **Day 5**: Update all API endpoints to use unified model

### **Week 2: Learning Infrastructure**
- [ ] **Day 1-2**: Implement learning models and services
- [ ] **Day 3**: Create agent learning integration
- [ ] **Day 4**: Build learning pattern storage
- [ ] **Day 5**: Test learning pipeline end-to-end

### **Week 3: Enhanced Agent Architecture**
- [ ] **Day 1-2**: Upgrade CrewAI agents with learning tools
- [ ] **Day 3**: Implement intelligent field mapping
- [ ] **Day 4**: Add classification learning capabilities
- [ ] **Day 5**: Integration testing

### **Week 4: Application Detection**
- [ ] **Day 1-2**: Build multi-strategy detection engine
- [ ] **Day 3**: Implement pattern learning for applications
- [ ] **Day 4**: Create user feedback integration
- [ ] **Day 5**: Performance optimization and testing

---

## 🔧 **Critical Implementation Details**

### **Agent Learning Integration**

```python
# Example: How agents will learn from user corrections
async def handle_user_correction(correction_event: UserCorrectionEvent):
    """Process user feedback and update agent intelligence."""
    
    # Store the correction
    learning_event = LearningEvent(
        event_type="user_correction",
        original_suggestion=correction_event.agent_suggestion,
        user_correction=correction_event.user_value,
        asset_context=correction_event.asset_data,
        confidence_impact=-0.1  # Reduce confidence in wrong pattern
    )
    
    # Update learning patterns
    await learning_service.process_learning_event(learning_event)
    
    # Notify agents of the correction
    await agent_registry.notify_correction(learning_event)
    
    # Update future suggestions immediately
    await update_agent_patterns(correction_event.pattern_id, learning_event)
```

### **Field Mapping Intelligence**

```python
# Example: Intelligent field mapping suggestions
async def suggest_field_mappings(source_fields: List[str], sample_data: dict) -> List[MappingSuggestion]:
    """Provide intelligent field mapping suggestions based on learned patterns."""
    
    suggestions = []
    
    for field in source_fields:
        # Get sample values for pattern matching
        sample_values = sample_data.get(field, [])
        
        # Query learned patterns
        learned_suggestions = await learning_service.suggest_field_mapping(field, sample_values)
        
        # Apply AI reasoning for novel fields
        if not learned_suggestions or max(s.confidence for s in learned_suggestions) < 0.6:
            ai_suggestions = await ai_field_mapper.suggest_mapping(field, sample_values)
            learned_suggestions.extend(ai_suggestions)
        
        suggestions.extend(learned_suggestions)
    
    return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
```

---

## 📊 **Success Metrics**

### **Phase 1 Metrics: Data Unification**
- [ ] All 56 assets migrated to unified model
- [ ] Zero data loss during migration
- [ ] All API endpoints using single asset model
- [ ] Frontend displaying unified data correctly

### **Phase 2 Metrics: Learning Infrastructure**
- [ ] Learning patterns stored for 90%+ of mappings
- [ ] User corrections captured and applied
- [ ] Pattern confidence scores improving over time
- [ ] Cross-session learning persistence verified

### **Phase 3 Metrics: Agent Enhancement**
- [ ] 90%+ field mapping accuracy using learned patterns
- [ ] 80%+ application detection accuracy
- [ ] User correction frequency decreasing over time
- [ ] Agent confidence scores aligned with accuracy

### **Phase 4 Metrics: Application Detection**
- [ ] Automatic classification of 85%+ applications
- [ ] Technology stack detection accuracy >75%
- [ ] Pattern learning improving detection over time
- [ ] User satisfaction with detection quality

---

## ⚠️ **Risk Mitigation**

### **Data Migration Risks**
- **Risk**: Data loss during migration
- **Mitigation**: Full backup before migration, validation scripts, rollback plan

### **Learning System Risks**
- **Risk**: Learning from incorrect patterns
- **Mitigation**: Confidence thresholds, user validation, pattern expiration

### **Performance Risks**
- **Risk**: Learning queries slowing down operations
- **Mitigation**: Async learning, caching, pattern indexing

---

## 📋 **Required Clarifications**

Before proceeding with implementation, please clarify:

1. **Migration Timeline**: Is the 4-week timeline acceptable, or do you need faster results?

2. **Data Retention**: Should we keep `cmdb_assets` table as backup during transition, or can we remove it after migration?

3. **Learning Scope**: Should learning be:
   - Global across all clients (shared intelligence)
   - Client-specific (isolated learning per organization)
   - Hybrid (shared patterns + client-specific overrides)

4. **Agent Memory Storage**: Where should we store agent learning data:
   - PostgreSQL database (current approach)
   - Vector database (ChromaDB/Pinecone)
   - File-based storage (JSON/pickle)

5. **Confidence Thresholds**: What confidence levels should trigger:
   - Automatic application (no user confirmation needed)
   - Suggested application (user confirmation recommended)
   - No application (insufficient confidence)

6. **Rollback Strategy**: If the unified model causes issues, what's the acceptable rollback timeline and process?

7. **Performance Requirements**: What are the acceptable response times for:
   - Field mapping suggestions
   - Asset classification
   - Learning pattern queries

Please provide feedback on these clarifications so we can finalize the implementation approach and begin execution. 