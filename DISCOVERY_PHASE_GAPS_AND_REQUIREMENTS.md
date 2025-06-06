# Discovery Phase - Critical Gaps and Requirements

## 🚨 **Current State Assessment**

### **What Exists:**
- ✅ Database models for assets, workflow progress, learning patterns
- ✅ Basic data import functionality (CSV → raw_import_records → assets)
- ✅ Learning services for field mapping and asset classification (backend only)
- ✅ CrewAI agent definitions and tools
- ✅ Frontend UI structure for discovery workflow

### **What's Missing - Critical Gaps:**

## 1. **Workflow Progression Integration**

### **Problem:**
- 56 assets stuck in `discovery_status: discovered, mapping_status: pending`
- No automatic workflow progression after data import
- `workflow_progress` table empty - no tracking of asset progression

### **Required Implementation:**
```python
# Missing: Auto-workflow progression service
class DiscoveryWorkflowOrchestrator:
    async def process_imported_assets(self, import_session_id: str):
        # 1. Get assets from import session
        # 2. Run AI classification on each asset
        # 3. Apply field mapping intelligence
        # 4. Create workflow progress records
        # 5. Move assets to appropriate workflow phase
        pass
    
    async def advance_assets_through_workflow(self):
        # Auto-advance assets based on completeness criteria
        pass
```

### **Integration Points:**
- Data import completion → trigger workflow progression
- Asset classification → update workflow status
- Field mapping completion → advance to cleanup phase
- Data quality threshold → advance to assessment ready

## 2. **Agentic Asset Classification Integration**

### **Problem:**
- Assets classified as basic types (SERVER, DATABASE) without AI analysis
- CrewAI agents exist but not connected to import pipeline
- No application discovery happening automatically

### **Required Implementation:**
```python
# Missing: Integration in data import flow
async def process_raw_to_assets_with_ai(import_session_id: str):
    raw_records = get_raw_import_records(import_session_id)
    
    for record in raw_records:
        # 1. Use Asset Classification Learner for intelligent typing
        classification = await asset_classification_learner.classify_asset_automatically(
            asset_data=record.parsed_data,
            client_account_id=record.client_account_id
        )
        
        # 2. Apply field mapping intelligence
        field_mappings = await field_mapping_learner.suggest_field_mappings(
            source_fields=list(record.parsed_data.keys()),
            sample_data=record.parsed_data
        )
        
        # 3. Create enhanced asset with AI insights
        asset = create_asset_with_ai_classification(
            raw_data=record.parsed_data,
            ai_classification=classification,
            field_mappings=field_mappings
        )
        
        # 4. Create workflow progress tracking
        create_workflow_progress(asset.id, "discovery", "completed")
```

## 3. **Application Discovery and Portfolio View**

### **Problem:**
- API returns 0 applications despite having assets
- No intelligent asset-to-application grouping
- Missing application portfolio with cloud readiness scores

### **Required Implementation:**
```python
# Missing: Application discovery service
class ApplicationDiscoveryService:
    async def discover_applications_from_assets(self, client_account_id: str):
        assets = get_all_assets(client_account_id)
        
        # 1. Use AI to group assets into logical applications
        application_groups = await self.group_assets_into_applications(assets)
        
        # 2. Calculate cloud readiness for each application
        for app_group in application_groups:
            app_group.cloud_readiness_score = calculate_cloud_readiness(app_group)
            app_group.migration_complexity = assess_migration_complexity(app_group)
            app_group.recommended_strategy = determine_6r_strategy(app_group)
        
        # 3. Store application portfolio
        await self.store_application_portfolio(application_groups)
        
        return application_groups
```

## 4. **Discovery Overview Data Pipeline**

### **Problem:**
- Frontend shows 0s despite assets in database
- API endpoints return inconsistent data (24 vs 56 assets)
- Missing real-time metrics calculation

### **Required Implementation:**
```python
# Missing: Comprehensive discovery metrics service
class DiscoveryMetricsService:
    async def calculate_discovery_overview(self, client_account_id: str, engagement_id: str):
        # 1. Get all assets for the engagement
        assets = await get_assets_by_engagement(client_account_id, engagement_id)
        
        # 2. Calculate application discovery
        applications = await self.discover_applications(assets)
        
        # 3. Calculate workflow progress
        workflow_stats = await self.calculate_workflow_progress(assets)
        
        # 4. Calculate quality and completeness
        quality_metrics = await self.calculate_data_quality(assets)
        
        # 5. Calculate tech debt and critical issues
        tech_debt = await self.calculate_tech_debt(assets)
        
        return {
            "totalAssets": len(assets),
            "totalApplications": len(applications),
            "applicationToServerMapping": workflow_stats.mapping_completion,
            "dependencyMappingComplete": workflow_stats.dependency_completion,
            "techDebtItems": tech_debt.total_items,
            "criticalIssues": tech_debt.critical_count,
            "discoveryCompleteness": quality_metrics.overall_completeness,
            "dataQuality": quality_metrics.data_quality_score
        }
```

## 5. **Learning Integration in UI**

### **Problem:**
- Learning services work in isolation but not connected to user workflow
- No feedback loop for users to correct AI suggestions
- Learning insights not surfaced in discovery UI

### **Required Implementation:**
```typescript
// Missing: Learning feedback components
interface LearningFeedbackProps {
  suggestion: AISuggestion;
  onAccept: (suggestion: AISuggestion) => void;
  onCorrect: (suggestion: AISuggestion, correction: any) => void;
  onReject: (suggestion: AISuggestion) => void;
}

// Missing: Integration in data import flow
const DataImportWithLearning: React.FC = () => {
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [userFeedback, setUserFeedback] = useState([]);
  
  const handleImportComplete = async (importSession: ImportSession) => {
    // 1. Trigger AI analysis
    const aiResults = await triggerAIAnalysis(importSession.id);
    
    // 2. Show AI suggestions to user
    setAiSuggestions(aiResults.suggestions);
    
    // 3. Collect user feedback
    // 4. Send feedback to learning service
    // 5. Update AI models with user corrections
  };
};
```

## 6. **End-to-End Discovery Flow Integration**

### **Current Broken Flow:**
```
User uploads CSV → Raw records stored → Basic assets created → STOPS
Assets remain in "discovered" state forever
No AI processing, no workflow progression, no learning
```

### **Required Complete Flow:**
```
User uploads CSV → 
Raw records stored → 
AI Classification & Field Mapping → 
Enhanced assets created with AI insights → 
Workflow progression tracking → 
Application discovery → 
Portfolio analysis → 
Cloud readiness assessment → 
User feedback collection → 
Learning model updates → 
Discovery overview populated
```

## 📋 **Implementation Priority**

### **Phase 1: Core Discovery Pipeline (Critical)**
1. **Workflow Progression Service** - Move assets through discovery phases
2. **Discovery Metrics Integration** - Fix frontend showing zeros
3. **AI Classification in Import Flow** - Connect CrewAI to actual import

### **Phase 2: Application Intelligence**
4. **Application Discovery Service** - Group assets into applications
5. **Cloud Readiness Assessment** - Calculate portfolio metrics
6. **6R Strategy Integration** - Connect to assessment phase

### **Phase 3: Learning Integration**
7. **UI Learning Feedback Components** - User correction interface
8. **Learning Pipeline Integration** - Connect learning to import flow
9. **Agent Learning Dashboard** - Show learning insights

## 🎯 **Success Criteria**

### **Discovery Overview Should Show:**
- ✅ Actual asset count (not 0)
- ✅ Discovered applications with cloud readiness scores
- ✅ Real workflow progress percentages
- ✅ Actual tech debt and critical issues
- ✅ Learning insights from AI analysis

### **User Should Be Able To:**
- ✅ Upload CSV and see AI classification suggestions
- ✅ Provide feedback on AI suggestions
- ✅ See assets progress through workflow phases automatically
- ✅ View application portfolio with migration recommendations
- ✅ Track data quality improvements over time

### **Agentic Model Should:**
- ✅ Automatically classify assets during import
- ✅ Learn from user corrections
- ✅ Suggest field mappings based on learned patterns
- ✅ Discover application groupings intelligently
- ✅ Provide migration strategy recommendations

## 🚨 **Critical Truth**

The current system has the **foundation** for learning and agentic intelligence, but **none of it is connected to the actual user workflow**. The learning services work in isolation, the CrewAI agents exist but aren't triggered during import, and the workflow progression is completely missing.

**This is a classic case of "impressive backend capabilities with zero user-facing integration."** 