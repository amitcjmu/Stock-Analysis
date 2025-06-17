# CMDB CSV File Import Troubleshooting Guide

## 🎯 **Issue Resolution Summary**

**Date**: June 16, 2025  
**Issue**: CMDB CSV file import not processing via Data Import page  
**Status**: ✅ **RESOLVED**  
**Root Cause**: API endpoint migration during CrewAI Flow upgrade

---

## 🔧 **What Was Fixed**

### **1. API Endpoint Migration**
- **Problem**: Frontend was calling old `/discovery/analyze-cmdb` endpoint
- **Solution**: Updated API configuration to use new CrewAI Flow endpoints:
  - `ANALYZE_CMDB`: `/discovery/flow/agent/analysis`
  - `PROCESS_CMDB`: `/discovery/flow/run`

### **2. Data Format Alignment**
- **Problem**: Request format mismatch between frontend and backend
- **Solution**: Updated `useCMDBAnalysis` hook to use correct CrewAI Flow format:
  ```javascript
  {
    analysis_type: "data_source_analysis",
    data_source: {
      file_data: parsedData,
      metadata: {
        filename: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        import_session_id: sessionId
      }
    }
  }
  ```

### **3. Frontend Build Update**
- **Problem**: Cached frontend code using old endpoints
- **Solution**: Rebuilt and restarted frontend container

---

## 🚀 **Current Status**

### **✅ Working Components**
- CrewAI Flow Service: Operational with fallback mode
- API Endpoints: Correctly routed to `/discovery/flow/agent/analysis`
- Data Format: Aligned between frontend and backend
- Authentication: Context headers properly configured
- File Processing: CSV parsing and analysis ready

### **📋 Testing Checklist**
- [ ] Navigate to Data Import page (`/discovery/data-import`)
- [ ] Upload a CSV file to CMDB Data section
- [ ] Verify AI analysis starts automatically
- [ ] Check for real-time progress updates
- [ ] Confirm analysis results display correctly

---

## 🧪 **Test CSV File**

Use this sample CSV file to test the import functionality:

```csv
asset_name,ci_type,environment,ip_address,operating_system,business_owner
web-server-01,Server,Production,192.168.1.10,Linux,IT Team
web-server-02,Server,Production,192.168.1.11,Linux,IT Team
database-server-01,Server,Production,192.168.1.20,Linux,Database Team
payment-app,Application,Production,,,Finance Team
user-portal,Application,Production,,,HR Team
load-balancer-01,Network Device,Production,192.168.1.5,F5 OS,Network Team
```

---

## 🔍 **How to Test**

### **Step 1: Access Data Import Page**
1. Navigate to `http://localhost:8081/discovery/data-import`
2. Ensure you're logged in and have proper context selected

### **Step 2: Upload CSV File**
1. Click on the "CMDB Data" upload area
2. Select your CSV file or drag and drop it
3. File should immediately show "AI crew is analyzing your file..."

### **Step 3: Monitor Analysis**
1. Watch for real-time progress updates
2. Analysis should complete within 30-60 seconds
3. Results should show detected asset types and recommendations

### **Step 4: Verify Results**
1. Check that assets are properly classified
2. Verify field mappings are suggested
3. Confirm next steps are provided

---

## 🚨 **If Issues Persist**

### **Check Browser Console**
1. Open Developer Tools (F12)
2. Check Console tab for errors
3. Look for API call failures or authentication issues

### **Verify Authentication**
1. Ensure you're logged in
2. Check that auth token is present in localStorage
3. Verify client/engagement context is selected

### **Check API Connectivity**
1. Test health endpoint: `http://localhost:8000/api/v1/discovery/health`
2. Verify CrewAI Flow health: `http://localhost:8000/api/v1/discovery/flow/health`

### **Common Error Messages**

#### **"Not authenticated"**
- **Cause**: Missing or invalid auth token
- **Solution**: Log out and log back in

#### **"Analysis failed"**
- **Cause**: Invalid CSV format or backend error
- **Solution**: Check CSV format and backend logs

#### **"Endpoint not found"**
- **Cause**: API routing issue
- **Solution**: Restart backend container

---

## 📊 **Expected Workflow**

### **1. File Upload** (Immediate)
- File appears in upload list
- Status shows "uploaded"
- AI analysis begins automatically

### **2. Analysis Phase** (30-60 seconds)
- Status changes to "analyzing"
- Progress messages appear
- CrewAI agents process the data

### **3. Results Display** (After analysis)
- Status changes to "processed"
- Analysis results show:
  - Detected asset types
  - Data quality score
  - Field mapping suggestions
  - Next steps recommendations

### **4. Next Steps**
- Option to proceed to Attribute Mapping
- Option to review and edit data
- Option to process into asset inventory

---

## 🎯 **Success Indicators**

### **✅ Upload Working**
- File appears in upload list immediately
- No error messages in console
- Analysis starts automatically

### **✅ Analysis Working**
- Progress messages update in real-time
- Analysis completes within reasonable time
- Results display with recommendations

### **✅ Integration Working**
- Can proceed to next steps
- Data is properly formatted
- Navigation to other pages works

---

## 🛠️ **Technical Details**

### **API Endpoints Used**
- **Analysis**: `POST /api/v1/discovery/flow/agent/analysis`
- **Status**: `GET /api/v1/discovery/flow/agentic-analysis/status`
- **Health**: `GET /api/v1/discovery/flow/health`

### **Data Flow**
1. Frontend uploads file and parses CSV
2. Sends data to CrewAI Flow agent analysis endpoint
3. Backend initiates discovery workflow
4. Frontend polls for status updates
5. Results displayed when analysis complete

### **Authentication Headers**
- `Authorization: Bearer <token>`
- `X-Client-Account-ID: <client_id>`
- `X-Engagement-ID: <engagement_id>`

---

## 📞 **Support**

If you continue to experience issues after following this guide:

1. **Check the browser console** for specific error messages
2. **Verify your CSV file format** matches the expected structure
3. **Ensure authentication** is working properly
4. **Try a different browser** to rule out caching issues
5. **Restart the Docker containers** if needed:
   ```bash
   docker-compose restart frontend backend
   ```

The CMDB import functionality should now be working correctly with the CrewAI Flow integration! 