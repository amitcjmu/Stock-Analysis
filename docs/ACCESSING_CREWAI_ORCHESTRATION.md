# Accessing the CrewAI Agent Orchestration Panel
## Step-by-Step Guide to See the New Agentic Interface

The CrewAI Discovery Flow redesign is **already active** in the platform. Here's how to access the new Agent Orchestration Panel that shows specialized crews in action:

---

## 🎯 **Prerequisites**

### **1. Start the Platform**
```bash
# Navigate to the platform directory
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator

# Start all services in Docker
docker-compose up -d --build

# Verify services are running
docker-compose ps
```

### **2. Check Service Health**
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend accessible
open http://localhost:3000
```

---

## 🚀 **Steps to Access the New Interface**

### **Step 1: Navigate to Data Import**
1. Open your browser and go to `http://localhost:3000`
2. Navigate to **Discovery** → **Data Import** (or directly to `/discovery/data-import`)

### **Step 2: Upload a CMDB File**
1. In the **CMDB Data** section, either:
   - **Drag and drop** a CSV file, OR
   - **Click to browse** and select a CSV file

2. **Use this sample CSV data** for testing:
```csv
Asset_Name,CI_Type,Environment,Owner,Location,Business_Criticality
server-01,Server,Production,IT Team,Data Center A,High
app-web-01,Application,Development,Dev Team,Cloud,Medium
db-prod-01,Database,Production,DBA Team,Data Center A,Critical
network-fw-01,Network,Production,Network Team,Data Center A,High
storage-01,Storage,Production,Storage Team,Data Center B,Medium
```

### **Step 3: Watch the Magic Happen**
**Immediately after upload**, you'll see:

1. **File Analysis Section** appears showing:
   - File information (name, record count, session ID)
   - **Workflow Status** with real-time updates
   - **Refresh button** to check latest status

2. **Agent Orchestration Panel** automatically appears below, showing:
   - **Three tabs**: Overview, Crews, Results
   - **Real-time crew progress** with progress bars
   - **Specialized agent activities** in each crew
   - **Live status updates** as crews complete their work

### **Step 4: Explore the Interface**

#### **Overview Tab**
- See all 5 crews and their current status
- Watch progress bars update in real-time
- View overall completion percentage

#### **Crews Tab** 
- **Data Ingestion Crew**: Data Validation Specialist + Format Standardizer
- **Asset Analysis Crew**: Asset Classification Expert + Dependency Analyzer  
- **Field Mapping Crew**: Field Mapping Specialist + Pattern Recognition Agent
- **Quality Assessment Crew**: Data Quality Analyst + Consistency Validator
- **Database Integration**: Final persistence and validation

#### **Results Tab**
- Comprehensive processing summary
- Metrics from all crew executions
- Success/failure statistics
- Database integration results

---

## 🔧 **What You'll See in Real-Time**

### **Phase 1: Data Ingestion Crew (15% Progress)**
```
Status: Running
Current Task: "Validate 5 CMDB records for completeness and accuracy"
Agents: Data Validation Specialist, Format Standardizer
```

### **Phase 2: Asset Analysis Crew (35% Progress)**
```
Status: Running  
Current Task: "Classify each asset by type, business criticality, and migration readiness"
Agents: Asset Classification Expert, Dependency Analyzer
```

### **Phase 3: Field Mapping Crew (55% Progress)**
```
Status: Running
Current Task: "Map source fields to standard migration attributes"
Agents: Field Mapping Specialist, Pattern Recognition Agent
```

### **Phase 4: Quality Assessment Crew (75% Progress)**
```
Status: Running
Current Task: "Analyze data completeness and consistency"
Agents: Data Quality Analyst, Consistency Validator
```

### **Phase 5: Database Integration (100% Progress)**
```
Status: Completed
Results: "5 assets created in database with full metadata"
Database Assets: [asset-001, asset-002, asset-003, asset-004, asset-005]
```

---

## 🎨 **Interface Features**

### **Visual Indicators**
- **🔵 Blue spinning icons**: Crews currently working
- **✅ Green check marks**: Completed crews
- **❌ Red X marks**: Failed crews (with retry options)
- **⏳ Gray clock icons**: Pending crews

### **Real-Time Updates**
- **Status polling every 3 seconds** while processing
- **Progress bars** showing crew completion
- **Live task descriptions** showing what each crew is doing
- **Agent badges** showing which specialists are working

### **Interactive Elements**
- **Refresh button** to manually check status
- **Retry options** if crews fail
- **View Results button** when processing completes
- **Crew detail expansion** to see individual agent work

---

## 🐛 **Troubleshooting**

### **If the Panel Doesn't Appear**

1. **Check the File Upload**:
   ```bash
   # Check if the file was processed
   curl "http://localhost:8000/api/v1/discovery/flow/agent/crew/analysis/status?session_id=YOUR_SESSION_ID"
   ```

2. **Verify Backend Logs**:
   ```bash
   # Check CrewAI Flow execution
   docker-compose logs -f backend | grep -i "discovery\|crew\|flow"
   ```

3. **Frontend Console**:
   - Open browser Developer Tools (F12)
   - Check Console for any JavaScript errors
   - Look for network requests to flow endpoints

### **If Status Shows "idle"**
This means no workflow has started yet. Try:
1. **Re-upload the file** - sometimes the initial trigger doesn't fire
2. **Check browser console** for any API errors
3. **Verify the file format** - ensure it's a valid CSV with headers

### **If Processing Seems Stuck**
1. **Click the Refresh button** in the workflow status section
2. **Check the Crews tab** to see if any specific crew failed
3. **Look at backend logs** for specific error messages

---

## 📊 **Expected Timeline**

For a **5-row CSV file**:
- **Data Ingestion Crew**: ~10-15 seconds
- **Asset Analysis Crew**: ~15-20 seconds  
- **Field Mapping Crew**: ~10-15 seconds
- **Quality Assessment Crew**: ~5-10 seconds
- **Database Integration**: ~5-10 seconds

**Total Processing Time**: ~45-70 seconds

---

## 🎯 **Success Indicators**

You'll know the new interface is working when you see:

1. ✅ **Agent Orchestration Panel appears automatically** after file upload
2. ✅ **Three tabs (Overview, Crews, Results)** are visible and clickable
3. ✅ **Real-time progress updates** with crew names and percentages
4. ✅ **Specialized agent names** like "Data Validation Specialist" and "Asset Classification Expert"
5. ✅ **Live status changes** from "pending" → "running" → "completed"
6. ✅ **Final results showing database integration** with created asset IDs

---

## 🚀 **Next Steps After Successful Processing**

Once the workflow completes:

1. **Click "View Results"** to see processed assets
2. **Navigate to Attribute Mapping** to refine field mappings
3. **Go to Asset Inventory** to see the newly created assets
4. **Check Discovery Analytics** for comprehensive insights

---

## 🎪 **The Magic Behind the Scenes**

When you upload a file, here's what happens:

1. **Frontend** calls `/api/v1/discovery/flow/agent/analysis`
2. **CrewAI Flow Service** creates a `DiscoveryFlowRedesigned` instance
3. **Five specialized crews** execute in sequence with collaborative agents
4. **Real-time state updates** are polled by the frontend every 3 seconds
5. **Agent Orchestration Panel** displays live progress and results
6. **Database integration** saves processed assets for the next phase

This is a **true agentic workflow** where AI agents collaborate to process your data, following CrewAI best practices for High Complexity + High Precision use cases!

---

**🎉 Ready to see the future of agentic data processing in action? Upload a CSV file and watch the crews work their magic!** 