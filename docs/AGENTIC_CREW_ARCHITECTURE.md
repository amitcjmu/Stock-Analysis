# Agentic Crew Architecture for Discovery Workflow

## Overview

The Discovery workflow employs specialized AI crews at each stage to provide intelligent analysis, recommendations, and automation. Each crew consists of agents with specific roles, tools, and tasks designed to optimize cloud migration planning and analysis.

## Workflow Sequence & Data Persistence

```
Data Import → Attribute Mapping → Data Cleansing → Inventory → Dependencies → Tech Debt
     ↓              ↓                ↓              ↓           ↓            ↓
Raw Data    →  Field Mappings  →  Clean Data  →  Assets  →  Relationships → Analysis
```

### Data Flow Architecture
- **Raw Data**: Original imported CMDB/CSV files stored in PostgreSQL
- **Field Mappings**: User-approved attribute mappings stored for reuse
- **Clean Data**: Processed and standardized asset data
- **Enriched Assets**: Assets with dependencies and technical debt analysis
- **Migration Readiness**: Complete 6R recommendations and wave planning data

## Stage 1: Data Import Crew

### Primary Agent: **Data Import Specialist**
**Role**: Analyze uploaded files and determine data structure, quality, and migration relevance

**Tools**:
- File format analyzers (CSV, Excel, JSON parsers)
- Data type detection algorithms
- Statistical analysis functions
- Pattern recognition for CMDB formats

**Tasks**:
1. **File Analysis Task**
   - Analyze file structure and format
   - Detect column headers and data types
   - Identify potential asset records vs metadata
   - Calculate data quality metrics

2. **Content Classification Task**
   - Classify records as Applications, Servers, Databases, Network devices
   - Detect CMDB export format (ServiceNow, BMC Remedy, custom)
   - Identify migration-relevant vs irrelevant data

3. **Quality Assessment Task**
   - Calculate completeness percentages
   - Identify missing critical fields
   - Detect duplicate records
   - Assess data consistency

**Prompt Template**:
```
You are a Data Import Specialist analyzing uploaded CMDB data for cloud migration planning.

CONTEXT:
- File: {filename} ({file_size} KB, {record_count} records)
- Format: {detected_format}
- Intended Type: {user_intended_type}

ANALYZE:
1. Data Structure: What columns exist and what do they represent?
2. Asset Types: How many applications, servers, databases are present?
3. Quality Score: What percentage of critical migration fields are complete?
4. Migration Relevance: How suitable is this data for 6R analysis?

PROVIDE:
- Quality score (0-100)
- Asset breakdown by type
- Missing critical fields list
- Recommendations for next steps
```

### Supporting Agent: **Migration Readiness Assessor**
**Role**: Evaluate data readiness for migration analysis

**Tools**:
- Field requirement matrices for 6R analysis
- Business criticality assessment algorithms
- Technical complexity calculators

**Tasks**:
1. **Readiness Scoring Task**
   - Score data completeness for 6R analysis (Rehost, Replatform, etc.)
   - Assess availability of business context (criticality, ownership)
   - Evaluate technical specifications completeness

2. **Recommendation Task**
   - Suggest immediate data enrichment opportunities
   - Recommend optimal next workflow step
   - Identify high-value missing information

## Stage 2: Attribute Mapping Crew

### Primary Agent: **Field Mapping Specialist**
**Role**: Map imported fields to critical migration attributes using semantic analysis

**Tools**:
- Semantic field matching algorithms
- Pattern recognition for field names
- Sample value analysis functions
- Confidence scoring models

**Tasks**:
1. **Semantic Mapping Task**
   - Map column names to critical attributes (hostname, asset_type, etc.)
   - Analyze sample values for pattern recognition
   - Calculate confidence scores for each mapping

2. **Critical Attribute Assessment Task**
   - Identify which critical attributes are mappable
   - Assess completeness for 6R analysis requirements
   - Flag unmapped but essential fields

**Prompt Template**:
```
You are a Field Mapping Specialist training AI to understand data structure for migration analysis.

CRITICAL ATTRIBUTES NEEDED:
- Identity: hostname, asset_name, asset_type
- Business: department, business_criticality, environment, application_owner
- Technical: operating_system, cpu_cores, memory_gb, storage_gb
- Network: ip_address, location

ANALYZE COLUMNS:
{column_list}

SAMPLE VALUES:
{sample_data}

FOR EACH COLUMN:
1. Semantic match to critical attributes
2. Confidence score (0.0-1.0)
3. Mapping reasoning
4. Sample value validation

FOCUS ON: Fields essential for 6R strategy selection and wave planning
```

### Supporting Agent: **Migration Planning Agent**
**Role**: Assess data readiness for comprehensive migration analysis

**Tools**:
- 6R requirement matrices
- Wave planning field dependencies
- Business impact assessment frameworks

**Tasks**:
1. **Readiness Assessment Task**
   - Evaluate mapped attributes against 6R analysis requirements
   - Assess wave planning data completeness
   - Calculate business impact analysis readiness

2. **Training Effectiveness Task**
   - Monitor mapping accuracy improvements
   - Identify learning patterns from user feedback
   - Suggest additional training data needs

### Supporting Agent: **6R Strategy Agent**
**Role**: Evaluate data completeness for 6R treatment recommendations

**Tools**:
- Strategy requirement matrices for each R (Rehost, Replatform, etc.)
- Technical specification requirements
- Business context requirement frameworks

**Tasks**:
1. **Strategy Readiness Task**
   - Assess data completeness for each 6R strategy
   - Identify required fields for accurate recommendations
   - Calculate strategy confidence scores

## Stage 3: Data Cleansing Crew

### Primary Agent: **Data Quality Specialist**
**Role**: Identify and resolve data quality issues using mapped attributes

**Tools**:
- Data validation rules based on mapped attributes
- Standardization algorithms for critical fields
- Duplicate detection using mapped identifiers
- Missing value inference models

**Tasks**:
1. **Quality Analysis Task**
   - Analyze mapped critical attributes for completeness
   - Identify format inconsistencies in standardized fields
   - Detect duplicates using mapped identity fields

2. **Standardization Task**
   - Standardize asset_type values (expand abbreviations)
   - Normalize environment values (Prod→Production)
   - Cleanse business_criticality levels

3. **Enhancement Task**
   - Suggest missing values based on asset patterns
   - Infer department from hostname conventions
   - Recommend environment based on asset naming

**Prompt Template**:
```
You are a Data Quality Specialist improving mapped migration data.

MAPPED ATTRIBUTES:
{approved_field_mappings}

QUALITY ISSUES TO ANALYZE:
1. Missing Values: Critical attributes with empty/null values
2. Format Issues: Abbreviated or inconsistent values in mapped fields
3. Duplicates: Assets with identical mapped identifiers

FOR EACH ISSUE:
- Asset identification using mapped fields
- Current value assessment
- Suggested improvement with confidence
- Impact on 6R analysis if not resolved

PRIORITIZE: Issues that directly impact 6R strategy accuracy and wave planning
```

### Supporting Agent: **Migration Data Validator**
**Role**: Ensure cleaned data meets migration analysis requirements

**Tools**:
- Migration tool compatibility validators
- 6R analysis requirement checkers
- Wave planning data completeness assessments

**Tasks**:
1. **Compatibility Validation Task**
   - Validate data formats against migration tool requirements
   - Ensure critical attribute completeness for 6R engines
   - Check business context completeness for wave planning

## Stage 4: Asset Inventory Crew

### Primary Agent: **Asset Cataloging Specialist**
**Role**: Organize and enrich cleaned assets for migration analysis

**Tools**:
- Asset classification algorithms using cleaned attributes
- Technology stack analysis based on mapped OS/vendor fields
- Business impact calculation using criticality and department mappings

**Tasks**:
1. **Asset Classification Task**
   - Classify assets using cleaned asset_type attribute
   - Group by environment using standardized environment values
   - Organize by department using cleaned business context

2. **Enrichment Task**
   - Calculate technical specifications summaries
   - Assess cloud readiness based on OS and technical attributes
   - Generate migration complexity scores

**Prompt Template**:
```
You are an Asset Cataloging Specialist organizing cleaned migration data.

CLEANED ASSET DATA:
- {asset_count} assets with mapped and cleaned attributes
- Critical attributes: {mapped_critical_attributes}
- Quality score: {data_quality_percentage}%

CATALOG TASKS:
1. Asset Classification: Group by type, environment, department
2. Technical Assessment: Analyze OS, specs, technology stack
3. Business Context: Evaluate criticality, ownership, dependencies
4. Cloud Readiness: Score based on technical and business factors

OUTPUT: Comprehensive asset inventory ready for dependency mapping
```

### Supporting Agent: **Cloud Readiness Assessor**
**Role**: Evaluate each asset's readiness for cloud migration

**Tools**:
- Cloud compatibility matrices for OS and technology stacks
- Right-sizing calculators using CPU/memory specifications
- Security and compliance requirement assessors

**Tasks**:
1. **Technical Readiness Task**
   - Assess OS compatibility with cloud platforms
   - Evaluate application architecture for cloud-native potential
   - Calculate resource right-sizing recommendations

## Stage 5: Dependencies Mapping Crew

### Primary Agent: **Dependency Analysis Specialist**
**Role**: Map relationships between assets using enriched inventory data

**Tools**:
- Network connectivity analyzers using IP address mappings
- Application communication pattern detectors
- Database relationship mappers

**Tasks**:
1. **Relationship Discovery Task**
   - Analyze communication patterns between mapped assets
   - Identify database connections using technical specifications
   - Map application-to-infrastructure dependencies

2. **Migration Impact Analysis Task**
   - Assess impact of moving assets based on dependency chains
   - Identify critical path dependencies for wave planning
   - Calculate blast radius for migration decisions

**Prompt Template**:
```
You are a Dependency Analysis Specialist mapping asset relationships for migration.

ENRICHED ASSETS:
- {categorized_asset_count} categorized assets
- Mapped attributes: {critical_attributes_available}
- Technical specifications: {technical_data_completeness}%

ANALYZE DEPENDENCIES:
1. Application-Database connections using technical attributes
2. Inter-application communication patterns
3. Infrastructure dependencies based on location/network data
4. Business process dependencies using department mappings

FOCUS: Dependencies that impact migration wave sequencing and 6R strategy selection
```

### Supporting Agent: **Wave Planning Specialist**
**Role**: Use dependency analysis for migration wave recommendations

**Tools**:
- Wave optimization algorithms
- Business impact minimization models
- Technical complexity balancing tools

**Tasks**:
1. **Wave Optimization Task**
   - Group assets into migration waves based on dependencies
   - Minimize business disruption using criticality mappings
   - Balance technical complexity across waves

## Stage 6: Tech Debt Analysis Crew

### Primary Agent: **Technology Assessment Specialist**
**Role**: Analyze technology stack for modernization opportunities

**Tools**:
- Technology lifecycle databases
- End-of-life detection algorithms
- Modernization opportunity assessors
- Security vulnerability scanners

**Tasks**:
1. **Technology Lifecycle Analysis Task**
   - Assess OS versions against support lifecycles
   - Identify end-of-life software using version mappings
   - Calculate technical debt scores based on age and support status

2. **Modernization Opportunity Analysis Task**
   - Identify candidates for containerization based on technical attributes
   - Assess cloud-native refactoring potential
   - Recommend technology stack upgrades

**Prompt Template**:
```
You are a Technology Assessment Specialist analyzing technical debt for migration.

ASSET TECHNOLOGY STACK:
- Operating Systems: {os_distribution}
- Applications: {application_technology_summary}
- Technical Specifications: {resource_utilization_patterns}

ANALYZE TECHNICAL DEBT:
1. End-of-Life Assessment: Which technologies need immediate attention?
2. Modernization Opportunities: What can be containerized or refactored?
3. 6R Strategy Impact: How does technical debt affect strategy selection?
4. Cost Implications: What are the financial impacts of technical debt?

OUTPUT: Comprehensive technical debt analysis with 6R strategy recommendations
```

### Supporting Agent: **6R Strategy Recommendation Engine**
**Role**: Generate final 6R treatment recommendations using complete analysis

**Tools**:
- Multi-factor 6R decision matrices
- Cost-benefit analyzers for each strategy
- Risk assessment models
- Timeline optimization algorithms

**Tasks**:
1. **Strategy Selection Task**
   - Analyze all collected data (technical, business, dependencies, debt)
   - Apply 6R decision frameworks for each asset
   - Generate confidence-scored recommendations

2. **Migration Planning Task**
   - Create wave-sequenced migration plans
   - Estimate timelines and resources
   - Identify risks and mitigation strategies

## Crew Coordination & Data Flow

### Inter-Crew Communication
- **State Handoffs**: Each crew receives enriched data from the previous stage
- **Context Preservation**: Critical decisions and mappings persist through workflow
- **Feedback Loops**: User corrections improve subsequent crew accuracy
- **Quality Gates**: Each stage validates prerequisites before proceeding

### Data Persistence Strategy
- **PostgreSQL Storage**: All crew analysis results stored with versioning
- **Audit Trail**: Complete history of AI decisions and user modifications
- **Rollback Capability**: Ability to revert to previous analysis states
- **Integration Points**: APIs for external migration tools to consume crew outputs

### Performance Monitoring
- **Crew Accuracy Tracking**: Monitor and improve each crew's performance
- **User Satisfaction Metrics**: Track user approval/rejection patterns
- **Analysis Quality Scores**: Measure output quality at each stage
- **Workflow Efficiency**: Optimize crew coordination and data flow

## Error Handling & Fallbacks

### Missing Data Scenarios
- **Graceful Degradation**: Crews provide partial analysis when data is incomplete
- **Alternative Strategies**: Multiple approach paths when preferred data unavailable
- **User Guidance**: Clear recommendations for data collection priorities

### Quality Assurance
- **Cross-Validation**: Multiple crews validate critical decisions
- **Confidence Thresholds**: Minimum confidence requirements for automated decisions
- **Human-in-the-Loop**: User review points for low-confidence recommendations

This architecture ensures that each stage of the Discovery workflow builds intelligently upon the previous stage's outputs, creating a comprehensive and accurate foundation for cloud migration planning and 6R strategy selection. 