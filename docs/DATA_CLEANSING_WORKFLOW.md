# Data Cleansing Workflow Documentation

## Overview

The Data Cleansing workflow has been completely redesigned to use **real agentic AI processing** and eliminate mock data. The AI crew now performs continuous analysis from Data Import through Data Cleansing to Attribute Mapping.

## Workflow Architecture

### 1. Data Import Phase
**Location**: `src/pages/discovery/CMDBImport.tsx`

#### Real AI Analysis Process:
1. **File Upload & Analysis**: When users upload data files, the AI crew analyzes the actual content
2. **Backend Analysis**: Real call to `http://localhost:8000/api/v1/discovery/analyze-cmdb`
3. **Data Quality Detection**: Backend performs actual DataFrame analysis:
   - Missing data detection (null values, empty fields)
   - Duplicate record identification
   - Data format inconsistencies (abbreviations, capitalization)
   - Critical field validation
   - Asset type standardization needs

#### Key Functions:
- `generateIntelligentInsights()`: Now uses real `analysisResult.dataQuality.issues` instead of mock data
- Issues are categorized into Data Cleansing focus areas:
  - **missing_data**: Empty fields, null values
  - **duplicate**: Duplicate hostnames/records
  - **misclassification**: Abbreviated values, format issues
  - **incorrect_mapping**: Capitalization inconsistencies

### 2. Data Cleansing Phase
**Location**: `src/pages/discovery/DataCleansing.tsx`

#### Seamless Continuation:
1. **State Transfer**: Real data quality issues passed via navigation state
2. **Context Awareness**: Page detects `fromDataImport` flag and shows import context
3. **Real Issue Display**: Shows actual issues from AI crew analysis
4. **Fallback Mode**: If accessed directly, fetches real issues from persisted data

#### New Backend Endpoints:
- `GET /api/v1/discovery/assets/data-issues`: Analyzes persisted assets for real quality issues
- `POST /api/v1/discovery/assets/validate-data`: Re-runs AI analysis on stored data
- `POST /api/v1/discovery/assets/data-issues/{id}/approve`: Applies suggested fixes
- `POST /api/v1/discovery/assets/data-issues/{id}/reject`: Records AI feedback

### 3. Data Quality Analysis (Backend)
**Location**: `backend/app/api/v1/discovery/cmdb_analysis.py`

#### Enhanced Analysis Functions:
- `_extract_data_quality()`: Performs real DataFrame analysis
- Focuses on migration-critical issues:
  - **Missing data**: Critical fields (environment, department, asset_type, hostname)
  - **Duplicates**: Actual duplicate detection using pandas
  - **Format issues**: Abbreviations, capitalization, whitespace
  - **Field validation**: Asset type standardization, environment classification

#### Real Issue Generation:
- `get_data_issues()` in `asset_management.py`: Analyzes actual persisted assets
- Creates specific, actionable issues with real asset data
- Provides intelligent suggestions based on asset context

## Key Improvements

### 1. No Mock Data
- ❌ **Before**: Generated fake data quality issues
- ✅ **After**: Uses real AI crew analysis results and actual asset data

### 2. Seamless AI Continuity
- ❌ **Before**: Disconnected workflow with mock transitions
- ✅ **After**: AI crew context flows from Import → Cleansing → Attribute Mapping

### 3. Real Data Focus Areas
- **De-duplication**: Actual duplicate hostname detection
- **Data Format Issues**: Real abbreviation and capitalization analysis
- **Missing Data**: Actual missing field identification

### 4. Persistent Data Processing
- Issues are generated from actual persisted assets
- AI suggestions based on real data patterns
- Context-aware value suggestions

## Data Flow

```
Data Import (Real File)
    ↓ (AI Crew Analysis)
Backend Analysis (Real DataFrame processing)
    ↓ (Real Issues Identified)
Data Cleansing (Actual Issues Display)
    ↓ (Human-in-the-loop approval)
Attribute Mapping (Context Continues)
```

## Implementation Details

### Frontend Changes:
1. **CMDBImport.tsx**: 
   - `generateIntelligentInsights()` uses real `dataQuality.issues`
   - Transforms backend issues into Data Cleansing format
   - Passes real issues via navigation state

2. **DataCleansing.tsx**:
   - Detects import context and displays real issues
   - Falls back to fetching from persisted data if accessed directly
   - Real approval/rejection workflow

### Backend Changes:
1. **cmdb_analysis.py**:
   - `_extract_data_quality()` performs comprehensive DataFrame analysis
   - Generates real issues focused on migration requirements

2. **asset_management.py**:
   - New endpoints for data quality issue management
   - Real asset analysis for quality issues
   - Intelligent suggestion algorithms

## Testing the Workflow

1. **Upload real data** in Data Import page
2. **AI crew analyzes** actual file content and structure
3. **Real issues identified** based on data quality analysis
4. **Navigate to Data Cleansing** with real issues passed
5. **Review actual suggestions** from AI analysis
6. **Approve/reject** to train the AI crew
7. **Continue to Attribute Mapping** with updated context

## Benefits

1. **Authentic AI Processing**: Real crew analysis instead of mock data
2. **Migration-Focused**: Issues prioritized for cloud migration needs
3. **Learning AI**: Human feedback improves future analysis
4. **Seamless Workflow**: Context preserved across pages
5. **Data-Driven**: All suggestions based on actual asset analysis 