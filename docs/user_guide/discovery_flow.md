# Discovery Flow User Guide

## 📋 **Overview**

This guide provides step-by-step instructions for using the enhanced Discovery Flow with CrewAI agents, automatic state persistence, and intelligent database integration. The Discovery Flow has been completely redesigned to leverage AI agents that learn and adapt, with **automatic data persistence** throughout the entire process.

## 🎯 **What's New in the Enhanced Discovery Flow**

### **AI-Powered Agent Teams with Automatic Persistence**
- **6 Sequential Phases**: Field Mapping → Data Cleansing → Inventory Building → App-Server Dependencies → App-App Dependencies → Technical Debt
- **21 Intelligent Agents**: Manager agents coordinate specialist agents for optimal results
- **Automatic State Management**: Flow state automatically persisted at each phase completion
- **Database Integration**: Assets automatically created in database after inventory building phase
- **Real-Time Progress Tracking**: Live updates via WebSocket and REST API endpoints

### **Automatic Persistence Architecture**
- **Phase-Level Persistence**: Each crew completion automatically updates flow state in `DataImportSession.agent_insights`
- **Asset Auto-Creation**: After inventory building, assets are automatically persisted to database with full multi-tenant context
- **User Modification Support**: Users can review and modify data through UI; changes are tracked and persisted
- **No Manual Confirmation Required**: System automatically saves progress - no user buttons needed for persistence

### **Key Benefits**
- **90%+ Accuracy**: AI agents achieve superior field mapping and asset classification accuracy
- **Seamless Data Flow**: Automatic persistence ensures no data loss between phases
- **Real-Time Monitoring**: Live progress updates and phase completion tracking
- **Multi-Tenant Security**: All data properly scoped by client account and engagement
- **User-Friendly Experience**: Review and modify data without worrying about manual saves

---

## 🚀 **Getting Started**

### **Step 1: Access the Discovery Flow**

1. **Navigate to Discovery Phase**
   - From the main dashboard, click **"Discovery"** in the navigation sidebar
   - Select your engagement from the engagement selector
   - Click **"Start Discovery Flow"**

2. **Verify Prerequisites**
   - ✅ Engagement created and configured
   - ✅ User has Discovery permissions
   - ✅ Data source prepared (CMDB export, CSV file, or API integration)

### **Step 2: Initialize Discovery Session**

1. **Data Source Selection**
   ```
   Choose your data source:
   • CMDB Import (ServiceNow, BMC, etc.)
   • CSV Upload (Excel exports, custom formats)
   • API Integration (Real-time data feeds)
   ```

2. **Upload or Configure Data**
   - **For CSV Upload**: Drag and drop your file or click "Browse"
   - **For CMDB Import**: Enter connection details and select export options
   - **For API Integration**: Configure endpoint and authentication

3. **Data Preview and Automatic Initialization**
   - Review the first 10 rows of your data
   - Verify column headers and data quality
   - System automatically initializes flow state with your data
   - **Flow state is immediately persisted** - no action required

---

## 🔄 **Discovery Flow Phases (Automatic Execution)**

### **Phase 1: Field Mapping** 🗂️ (Auto-Persisted)

**What Happens Automatically:**
- AI agents analyze your data structure and create precise field mappings
- Results automatically stored in flow state upon completion
- Confidence scores calculated and persisted
- System automatically prepares for data cleansing phase

**User Interface:**
- **Real-time progress**: Watch field mapping confidence scores build
- **Review and Modify**: Click "Review Field Mappings" to see and adjust results
- **Automatic Save**: All changes automatically saved to flow state
- **No Manual Action Required**: Phase completes and persists automatically

**Success Indicators:**
- ✅ Field mapping confidence > 0.8
- ✅ Unmapped fields < 10%
- ✅ **Flow state automatically updated**
- ✅ **Ready for next phase indicator appears**

### **Phase 2: Data Cleansing** 🧹 (Auto-Persisted)

**What Happens Automatically:**
- AI agents cleanse and standardize data using field mapping insights
- Data quality metrics calculated and stored
- Cleansed data automatically prepared for inventory building
- **All results automatically persisted to flow state**

**User Interface:**
- **Quality Dashboard**: Real-time data quality score updates
- **Before/After Comparison**: See data transformation results
- **Automatic Progression**: Phase automatically completes when quality thresholds met
- **No Save Button Needed**: All progress automatically saved

**Success Indicators:**
- ✅ Data quality score > 0.85
- ✅ **Cleansed data automatically stored**
- ✅ **Flow state updated with quality metrics**
- ✅ **System ready for asset classification**

### **Phase 3: Inventory Building** 🏭 (Auto-Persisted + Database Creation)

**What Happens Automatically:**
- AI agents classify assets across servers, applications, and devices
- **Assets automatically created in database upon completion**
- Multi-tenant context (client_account_id, engagement_id, session_id) automatically applied
- Asset relationships and dependencies automatically identified

**User Interface:**
- **Asset Classification Dashboard**: Real-time asset categorization
- **Database Integration Status**: Shows when assets are created in database
- **Review and Modify**: Adjust asset classifications; changes automatically saved
- **Automatic Database Persistence**: No manual action required for database creation

**Critical Automatic Actions:**
- ✅ **Assets automatically created in `assets` table**
- ✅ **Multi-tenant isolation automatically applied**
- ✅ **Discovery metadata automatically populated**
- ✅ **Flow state updated with asset inventory**

**Success Indicators:**
- ✅ Asset classification complete
- ✅ **Database assets created (visible in asset count)**
- ✅ **Flow state contains asset inventory**
- ✅ **Ready for dependency analysis**

### **Phase 4: App-Server Dependencies** 🔗 (Auto-Persisted)

**What Happens Automatically:**
- AI agents map application-to-server hosting relationships
- Infrastructure dependencies automatically identified
- **Dependency data automatically stored in flow state**
- System prepares for application-to-application dependency analysis

**User Interface:**
- **Dependency Visualization**: Interactive topology maps
- **Automatic Updates**: Dependency relationships appear in real-time
- **Review and Validate**: Confirm or adjust dependencies; changes auto-saved
- **No Manual Persistence**: All dependency data automatically stored

### **Phase 5: App-App Dependencies** 🔄 (Auto-Persisted)

**What Happens Automatically:**
- AI agents map application-to-application integration dependencies
- Communication patterns and API relationships identified
- **Integration data automatically stored in flow state**
- System prepares for technical debt assessment

**User Interface:**
- **Integration Flow Diagram**: Visual representation of app communications
- **API Discovery Results**: Automatically discovered service relationships
- **Automatic Completion**: Phase completes when integration analysis done
- **No Save Actions Required**: All integration data automatically persisted

### **Phase 6: Technical Debt Assessment** 🏗️ (Auto-Persisted)

**What Happens Automatically:**
- AI agents evaluate technical debt and prepare 6R migration strategies
- Risk assessments and modernization recommendations generated
- **Complete discovery analysis automatically stored**
- Final flow state automatically updated with comprehensive results

**User Interface:**
- **6R Strategy Dashboard**: Automatic strategy recommendations
- **Risk Assessment Matrix**: Auto-generated migration risk analysis
- **Final Review**: Complete discovery results available for review
- **Automatic Completion**: Flow automatically marked as completed

---

## 🔍 **Real-Time Monitoring and Status**

### **Flow Status API**
The system provides real-time flow status via:
- **REST Endpoint**: `GET /api/v1/discovery/flow/status?session_id={session_id}`
- **WebSocket Updates**: Live progress updates
- **Frontend Integration**: Automatic status polling every 5 seconds

### **Status Response Example:**
```json
{
  "status": "success",
  "flow_state": {
    "current_phase": "inventory_building",
    "progress_percentage": 60,
    "phase_completion": {
      "field_mapping": true,
      "data_cleansing": true,
      "inventory_building": false,
      "app_server_dependency": false,
      "app_app_dependency": false,
      "technical_debt": false
    },
    "database_integration_status": "pending",
    "created_assets_count": 0
  },
  "phase_data": {
    "field_mappings": {...},
    "data_quality_metrics": {...}
  }
}
```

---

## 💾 **Data Persistence Architecture**

### **Automatic Persistence Layers**

#### **1. Flow State Persistence**
- **Storage**: `DataImportSession.agent_insights` JSON field
- **Frequency**: After each phase completion
- **Content**: Complete flow state including all phase results
- **Trigger**: Automatic upon crew completion

#### **2. Database Asset Creation**
- **Storage**: `assets` table with full schema
- **Trigger**: Automatic after inventory building phase completion
- **Context**: Full multi-tenant context automatically applied
- **Metadata**: Discovery method, source, timestamps automatically populated

#### **3. User Modification Tracking**
- **Storage**: Flow state with `user_modified` flags
- **Trigger**: Automatic when user makes changes via UI
- **Persistence**: Immediate automatic save
- **Integration**: Changes flow into subsequent phases

### **Multi-Tenant Data Isolation**
All persistence automatically includes:
- `client_account_id`: Tenant isolation
- `engagement_id`: Project scoping
- `session_id`: Discovery session tracking
- `user_id`: User attribution
- **Automatic enforcement**: No manual configuration required

---

## 🛠️ **User Interaction Patterns**

### **Review and Modify Workflow**
1. **Automatic Processing**: Agents complete phase automatically
2. **Review Notification**: User notified when phase ready for review
3. **Optional Modification**: User can review and modify results
4. **Automatic Save**: All changes automatically persisted
5. **Continue Flow**: System automatically proceeds to next phase

### **No Manual Save Required**
- ❌ **No "Save" buttons needed**
- ❌ **No manual persistence confirmation**
- ❌ **No risk of data loss**
- ✅ **Everything automatically saved**
- ✅ **Real-time state updates**
- ✅ **Seamless user experience**

### **Data Modification Impact**
- **Immediate**: Changes applied to current session
- **Future Phases**: Modified data flows into subsequent analysis
- **Learning**: Agent patterns updated based on user corrections
- **Persistence**: All modifications automatically saved

---

## 🔧 **Technical Implementation Details**

### **State Manager Integration**
The `DiscoveryFlowStateManager` handles:
- Flow state initialization and persistence
- Phase completion tracking
- Asset database creation
- Multi-tenant context management
- Real-time status updates

### **Database Schema Integration**
Assets created with complete schema:
```sql
-- Automatic population
client_account_id, engagement_id, session_id  -- Multi-tenant context
discovery_method, discovery_source, discovery_timestamp  -- Discovery metadata
imported_by, imported_at, source_filename  -- Import tracking
field_mappings_used, raw_data  -- Original data preservation
created_at, created_by, updated_at, updated_by  -- Audit trail
```

### **API Endpoint Integration**
- `/api/v1/discovery/flow/run` - Initialize and execute flow
- `/api/v1/discovery/flow/status` - Real-time status monitoring
- `/api/v1/discovery/flow/execute-phase` - Manual phase execution (if needed)

---

## 📊 **Success Metrics and Validation**

### **Automatic Success Validation**
- **Flow Completion**: All 6 phases completed successfully
- **Database Integration**: Assets created with proper context
- **State Persistence**: Complete flow state saved
- **Multi-Tenant Isolation**: Proper data scoping verified
- **Real-Time Updates**: Status API functioning correctly

### **User Experience Metrics**
- **Zero Data Loss**: Automatic persistence prevents data loss
- **Seamless Flow**: No manual save actions required
- **Real-Time Feedback**: Live progress updates
- **Easy Modification**: Simple review and modify workflow
- **Complete Automation**: End-to-end automated processing

---

## 🚨 **Important Notes**

### **Automatic vs Manual Operations**
- **✅ AUTOMATIC**: Phase execution, state persistence, asset creation, progress tracking
- **👤 MANUAL**: Data review, result modification, flow initiation
- **🔄 HYBRID**: User modifications automatically integrated into flow

### **Data Safety**
- **No Data Loss Risk**: Everything automatically persisted
- **Session Recovery**: Flow state preserved across browser sessions
- **Error Recovery**: Graceful handling of failures with state preservation
- **Audit Trail**: Complete history of all changes and operations

### **Multi-Tenant Security**
- **Automatic Isolation**: All data automatically scoped by tenant
- **No Configuration Required**: Multi-tenancy handled automatically
- **Secure by Default**: No risk of cross-tenant data leakage
- **Audit Compliance**: Complete audit trail automatically maintained

---

This comprehensive user guide ensures users understand that the Discovery Flow operates with **full automatic persistence** - no manual save actions are required, and all data flows seamlessly through the system with complete database integration and real-time monitoring. 