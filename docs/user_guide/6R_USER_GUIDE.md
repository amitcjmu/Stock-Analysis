# 6R Treatment Analysis - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Application Selection](#application-selection)
4. [Parameter Configuration](#parameter-configuration)
5. [Qualifying Questions](#qualifying-questions)
6. [Analysis Progress](#analysis-progress)
7. [Understanding Recommendations](#understanding-recommendations)
8. [Analysis History](#analysis-history)
9. [Bulk Analysis](#bulk-analysis)
10. [Export and Reporting](#export-and-reporting)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Introduction

The 6R Treatment Analysis is an AI-powered tool that helps organizations make informed decisions about cloud migration strategies for their applications. The system analyzes application characteristics, business requirements, and organizational constraints to recommend the most appropriate migration approach from six possible strategies:

### The 6R Strategies

#### Minimal Modernization
- **Rehost** (Lift and Shift): Move applications to the cloud with minimal changes
- **Replatform** (Lift, Tinker, and Shift): Make minor optimizations during migration

#### High Modernization  
- **Refactor** (Re-architect): Modify application architecture for cloud optimization
- **Rearchitect** (Rebuild): Significantly redesign application architecture
- **Rewrite** (Replace with Custom): Build new cloud-native applications

#### Non-Migration
- **Retire**: Decommission applications that are no longer needed
- **Replace** (for COTS): Replace with SaaS or cloud-native alternatives

## Getting Started

### Accessing the 6R Analysis

1. Navigate to the **Assess** section in the main menu
2. Click on **Treatment** to access the 6R Treatment Analysis page
3. You'll see a tabbed interface with seven main sections:
   - **Selection**: Choose applications for analysis
   - **Parameters**: Configure analysis parameters
   - **Questions**: Answer qualifying questions
   - **Analysis**: Monitor analysis progress
   - **Results**: View recommendations
   - **History**: Review past analyses
   - **Bulk**: Manage bulk analysis jobs

### Prerequisites

Before starting an analysis, ensure you have:
- Applications imported into the CMDB system
- Appropriate permissions to perform analyses
- Basic understanding of your application portfolio
- Access to application stakeholders for detailed questions

## Application Selection

### Single Application Analysis

1. **Browse Applications**: Use the application selector to browse available applications
2. **Search and Filter**: Use search functionality to find specific applications
   - Search by name, department, or technology stack
   - Filter by criticality, complexity, or business unit
3. **Application Details**: Click on an application to view:
   - Technology stack information
   - Business metadata (department, criticality)
   - Complexity scores and dependencies
4. **Select Application**: Click the application card to select it for analysis

### Application Information Required

The system uses the following application data for analysis:
- **Name and Description**: Basic identification
- **Technology Stack**: Programming languages, frameworks, databases
- **Business Context**: Department, business unit, criticality level
- **Technical Metrics**: Complexity score, user count, data volume
- **Dependencies**: Integration points and external systems
- **Compliance Requirements**: Regulatory and security constraints

## Parameter Configuration

### Understanding Parameters

The 6R analysis uses seven key parameters to evaluate migration strategies:

#### 1. Business Value (1-10)
- **Low (1-3)**: Limited business impact, minimal revenue generation
- **Medium (4-7)**: Moderate business importance, some revenue impact
- **High (8-10)**: Critical business function, significant revenue impact

#### 2. Technical Complexity (1-10)
- **Low (1-3)**: Simple architecture, standard technologies
- **Medium (4-7)**: Moderate complexity, some custom components
- **High (8-10)**: Complex architecture, legacy technologies, many dependencies

#### 3. Migration Urgency (1-10)
- **Low (1-3)**: No immediate pressure, flexible timeline
- **Medium (4-7)**: Moderate timeline pressure, some business drivers
- **High (8-10)**: Urgent migration required, strong business drivers

#### 4. Compliance Requirements (1-10)
- **Low (1-3)**: Minimal regulatory requirements
- **Medium (4-7)**: Standard compliance needs (SOX, basic security)
- **High (8-10)**: Strict regulations (HIPAA, PCI-DSS, financial services)

#### 5. Cost Sensitivity (1-10)
- **Low (1-3)**: Budget flexibility, cost not primary concern
- **Medium (4-7)**: Moderate budget constraints
- **High (8-10)**: Tight budget, cost optimization critical

#### 6. Risk Tolerance (1-10)
- **Low (1-3)**: Risk-averse, prefer proven approaches
- **Medium (4-7)**: Balanced risk approach
- **High (8-10)**: Willing to accept higher risk for greater benefits

#### 7. Innovation Priority (1-10)
- **Low (1-3)**: Stability preferred, minimal change desired
- **Medium (4-7)**: Balanced approach to innovation
- **High (8-10)**: Innovation critical, willing to adopt new technologies

### Application Type Selection

Choose the appropriate application type:

#### Custom Applications
- Built in-house by your organization
- Full access to source code
- Can be modified and rewritten
- All 6R strategies available

#### COTS (Commercial Off-The-Shelf)
- Purchased from vendors
- Limited or no source code access
- Cannot be significantly modified
- Limited to Rehost, Replatform, Replace, or Retire

#### Hybrid Applications
- Combination of custom and COTS components
- Mixed modification capabilities
- Strategy options depend on component analysis

### Parameter Configuration Tips

1. **Be Realistic**: Base parameters on actual business and technical realities
2. **Involve Stakeholders**: Consult with business owners and technical teams
3. **Consider Context**: Factor in organizational capabilities and constraints
4. **Document Assumptions**: Note any assumptions made during parameter setting
5. **Review and Adjust**: Parameters can be modified during analysis iterations

## Qualifying Questions

### Question Categories

The system generates dynamic questions based on your application and parameters:

#### Application Classification
- Application type and architecture details
- Technology stack specifics
- Integration patterns

#### Business Impact
- User base and usage patterns
- Revenue impact and business criticality
- Downtime tolerance and availability requirements

#### Technical Assessment
- Code quality and maintainability
- Performance characteristics
- Security and compliance posture

#### Migration Constraints
- Timeline requirements and flexibility
- Budget constraints and cost considerations
- Resource availability and expertise

#### Compliance and Security
- Regulatory requirements
- Data sensitivity and privacy needs
- Security architecture requirements

### Question Types

#### Single Select
Choose one option from a predefined list
- Example: "What is the primary business function?"

#### Multiple Select
Choose multiple applicable options
- Example: "Which compliance requirements apply?"

#### Numeric Input
Provide quantitative information
- Example: "How many active users does the application have?"

#### Boolean (Yes/No)
Simple true/false questions
- Example: "Is comprehensive documentation available?"

#### Text Input
Provide detailed explanations
- Example: "Describe any unique technical constraints"

#### File Upload
Upload supporting documentation
- Source code samples
- Architecture diagrams
- Technical documentation
- Performance reports

### Answering Questions Effectively

1. **Be Accurate**: Provide truthful, data-driven answers
2. **Consult Experts**: Involve technical and business stakeholders
3. **Provide Context**: Use text fields to explain nuances
4. **Upload Documentation**: Include relevant files for better analysis
5. **Mark Confidence**: Indicate your confidence level in answers
6. **Save Progress**: Use partial submission to save work in progress

## Analysis Progress

### Analysis Phases

The 6R analysis consists of six main phases:

#### 1. Data Discovery
- CMDB data extraction and validation
- Technology stack analysis
- Dependency mapping
- Business context evaluation

#### 2. Initial Analysis
- Preliminary strategy scoring
- Parameter-based evaluation
- Risk and benefit assessment
- Confidence calculation

#### 3. Question Generation
- Dynamic question creation based on data gaps
- Priority-based question ordering
- Context-aware question selection
- Validation rule establishment

#### 4. Response Processing
- Answer validation and scoring
- Impact assessment on recommendations
- Confidence adjustment
- Additional data integration

#### 5. Analysis Refinement
- Strategy re-evaluation with new data
- Confidence score updates
- Risk factor reassessment
- Recommendation optimization

#### 6. Final Validation
- Cross-validation of recommendations
- Consistency checks
- Final confidence calculation
- Report generation

### Monitoring Progress

#### Real-time Updates
- Progress bars show completion percentage
- Step-by-step status indicators
- Estimated time remaining
- Current activity descriptions

#### Progress Controls
- **Pause**: Temporarily halt analysis
- **Resume**: Continue paused analysis
- **Cancel**: Stop and discard analysis
- **Retry**: Restart failed analysis steps

#### Error Handling
- Automatic retry for transient failures
- Clear error messages and resolution steps
- Support contact information
- Manual intervention options

## Understanding Recommendations

### Recommendation Structure

Each recommendation includes:

#### Primary Recommendation
- **Strategy**: The recommended 6R approach
- **Confidence Score**: AI confidence level (0-100%)
- **Rationale**: Key reasons for the recommendation

#### Strategy Comparison
- **All Strategies Scored**: Comparative analysis of all applicable strategies
- **Score Breakdown**: Detailed scoring for each strategy
- **Risk Assessment**: Risk factors for each approach
- **Benefit Analysis**: Expected benefits and outcomes

#### Implementation Guidance
- **Key Factors**: Critical considerations for implementation
- **Assumptions**: Underlying assumptions in the analysis
- **Next Steps**: Recommended actions to proceed
- **Timeline Estimates**: Expected implementation duration
- **Effort Estimates**: Resource requirements
- **Cost Impact**: Financial implications

### Confidence Levels

#### High Confidence (80-100%)
- Strong data quality and completeness
- Clear strategy differentiation
- Consistent parameter alignment
- Minimal conflicting factors

#### Medium Confidence (60-79%)
- Good data quality with some gaps
- Moderate strategy differentiation
- Some parameter conflicts
- Additional validation recommended

#### Low Confidence (40-59%)
- Limited data quality or completeness
- Close strategy scores
- Significant parameter conflicts
- Further analysis strongly recommended

#### Very Low Confidence (0-39%)
- Poor data quality
- Unclear strategy differentiation
- Major parameter inconsistencies
- Analysis iteration required

### Strategy-Specific Guidance

#### Rehost Recommendations
- **When Recommended**: Low complexity, urgent timeline, cost-sensitive
- **Key Considerations**: Minimal changes, quick migration, limited optimization
- **Next Steps**: Infrastructure planning, migration tooling, testing strategy

#### Replatform Recommendations
- **When Recommended**: Moderate complexity, balanced priorities
- **Key Considerations**: Minor optimizations, managed services adoption
- **Next Steps**: Platform selection, optimization planning, skill assessment

#### Refactor Recommendations
- **When Recommended**: High business value, moderate complexity, innovation focus
- **Key Considerations**: Code modernization, architecture improvements
- **Next Steps**: Code analysis, refactoring scope, development planning

#### Rearchitect Recommendations
- **When Recommended**: High value, high complexity, transformation goals
- **Key Considerations**: Significant architecture changes, new patterns
- **Next Steps**: Architecture design, proof of concept, team training

#### Rewrite Recommendations
- **When Recommended**: High innovation priority, legacy constraints, custom apps only
- **Key Considerations**: Complete rebuild, cloud-native design
- **Next Steps**: Requirements analysis, technology selection, development planning

#### Replace Recommendations
- **When Recommended**: COTS applications, better alternatives available
- **Key Considerations**: SaaS options, data migration, integration changes
- **Next Steps**: Vendor evaluation, pilot testing, migration planning

#### Retire Recommendations
- **When Recommended**: Low business value, high complexity, redundant functionality
- **Key Considerations**: Data archival, user migration, dependency removal
- **Next Steps**: Retirement planning, data preservation, communication strategy

## Analysis History

### Viewing Analysis History

#### History Table
- **Application Name**: Application analyzed
- **Analysis Date**: When analysis was performed
- **Analyst**: User who performed the analysis
- **Status**: Completion status
- **Strategy**: Recommended strategy
- **Confidence**: Confidence score
- **Iterations**: Number of analysis iterations

#### Filtering and Search
- **Date Range**: Filter by analysis date
- **Strategy**: Filter by recommended strategy
- **Confidence**: Filter by confidence level
- **Status**: Filter by completion status
- **Analyst**: Filter by performing user
- **Department**: Filter by application department

### Analysis Comparison

#### Selecting Analyses
- Use checkboxes to select up to 5 analyses for comparison
- Click "Compare Selected" to open comparison view

#### Comparison View
- **Side-by-side Strategy Comparison**: Visual comparison of recommendations
- **Parameter Differences**: Highlight parameter variations
- **Confidence Comparison**: Compare confidence levels
- **Timeline Analysis**: Track recommendation changes over time
- **Factor Analysis**: Compare key factors and assumptions

#### Comparison Insights
- **Trend Analysis**: Identify patterns in recommendations
- **Consistency Check**: Validate recommendation consistency
- **Evolution Tracking**: See how recommendations change over time
- **Decision Support**: Support for final strategy selection

### Managing History

#### Archive Analyses
- Archive old or superseded analyses
- Maintain clean active history
- Preserve data for compliance

#### Delete Analyses
- Remove test or invalid analyses
- Permanent deletion with confirmation
- Audit trail maintenance

#### Export History
- Export analysis history to CSV/Excel
- Include detailed analysis data
- Support for reporting and compliance

## Bulk Analysis

### Creating Bulk Analysis Jobs

#### Job Configuration
1. **Job Details**
   - **Name**: Descriptive job name
   - **Description**: Purpose and scope
   - **Priority**: High, Medium, or Low

2. **Application Selection**
   - Select multiple applications from the portfolio
   - Use filters to select by criteria
   - Import application lists from CSV

3. **Analysis Parameters**
   - **Parallel Limit**: Number of concurrent analyses
   - **Retry Failed**: Automatically retry failed analyses
   - **Auto-approve High Confidence**: Automatically accept high-confidence recommendations
   - **Confidence Threshold**: Minimum confidence for auto-approval

#### Parameter Templates
- **Default Parameters**: Use system defaults
- **Custom Parameters**: Set specific parameter values
- **Application-specific**: Different parameters per application
- **Template Library**: Save and reuse parameter sets

### Managing Bulk Jobs

#### Job Queue Management
- **Start/Stop Jobs**: Control job execution
- **Pause/Resume**: Temporarily halt processing
- **Priority Adjustment**: Change job priority
- **Resource Allocation**: Manage system resources

#### Progress Monitoring
- **Overall Progress**: Total job completion percentage
- **Individual Progress**: Per-application analysis status
- **Performance Metrics**: Processing speed and efficiency
- **Resource Utilization**: System resource usage

#### Results Management
- **Completed Analyses**: View finished analyses
- **Failed Analyses**: Review and retry failures
- **Pending Analyses**: Monitor queue status
- **Summary Statistics**: Overall job performance

### Bulk Analysis Best Practices

1. **Job Sizing**: Limit jobs to 50-100 applications for optimal performance
2. **Parameter Consistency**: Use consistent parameters for comparable results
3. **Resource Planning**: Schedule large jobs during off-peak hours
4. **Quality Control**: Review auto-approved recommendations
5. **Progress Monitoring**: Regularly check job progress and address issues

## Export and Reporting

### Export Options

#### Individual Analysis Export
- **PDF Report**: Comprehensive analysis report
- **CSV Data**: Structured data for analysis
- **JSON**: Raw analysis data
- **Excel**: Formatted spreadsheet with charts

#### Bulk Export
- **Multiple Analyses**: Export selected analyses
- **Portfolio Summary**: High-level portfolio analysis
- **Comparison Reports**: Side-by-side analysis comparison
- **Executive Summary**: Business-focused summary

### Report Contents

#### Executive Summary
- **Portfolio Overview**: High-level statistics
- **Strategy Distribution**: Breakdown by recommended strategy
- **Confidence Analysis**: Confidence level distribution
- **Risk Assessment**: Portfolio-wide risk factors
- **Investment Priorities**: Recommended focus areas

#### Detailed Analysis
- **Application Details**: Complete application information
- **Parameter Analysis**: Parameter values and rationale
- **Strategy Evaluation**: Detailed strategy comparison
- **Implementation Guidance**: Step-by-step recommendations
- **Risk and Benefit Analysis**: Comprehensive impact assessment

#### Technical Appendix
- **Methodology**: Analysis approach and algorithms
- **Data Sources**: Information sources and quality
- **Assumptions**: Key assumptions and limitations
- **Validation**: Quality assurance and validation steps

### Custom Reporting

#### Report Templates
- **Standard Templates**: Pre-built report formats
- **Custom Templates**: Organization-specific formats
- **Template Library**: Shared template repository
- **Template Editor**: Create and modify templates

#### Data Integration
- **External Data**: Integrate with other systems
- **Custom Fields**: Add organization-specific data
- **Calculated Fields**: Create derived metrics
- **Data Validation**: Ensure data quality and consistency

## Best Practices

### Analysis Preparation

1. **Data Quality**
   - Ensure CMDB data is current and accurate
   - Validate application metadata
   - Update technology stack information
   - Verify business context data

2. **Stakeholder Engagement**
   - Involve application owners in parameter setting
   - Consult technical teams for complexity assessment
   - Engage business users for value evaluation
   - Include compliance teams for regulatory requirements

3. **Parameter Setting**
   - Use consistent parameter definitions across analyses
   - Document parameter rationale and assumptions
   - Consider organizational context and capabilities
   - Validate parameters with stakeholders

### Analysis Execution

1. **Question Answering**
   - Provide accurate, data-driven responses
   - Include supporting documentation when available
   - Indicate confidence levels honestly
   - Consult subject matter experts for technical questions

2. **Iteration Management**
   - Review initial recommendations critically
   - Adjust parameters based on new insights
   - Document changes and rationale
   - Limit iterations to avoid analysis paralysis

3. **Quality Assurance**
   - Review recommendations for consistency
   - Validate against organizational constraints
   - Check for obvious errors or inconsistencies
   - Seek peer review for critical applications

### Results Management

1. **Recommendation Review**
   - Understand the rationale behind recommendations
   - Consider implementation feasibility
   - Evaluate resource requirements
   - Assess timeline constraints

2. **Decision Making**
   - Use recommendations as input, not final decisions
   - Consider factors beyond the analysis
   - Involve appropriate stakeholders in decisions
   - Document decision rationale

3. **Implementation Planning**
   - Develop detailed implementation plans
   - Identify required resources and skills
   - Establish timelines and milestones
   - Plan for risk mitigation

## Troubleshooting

### Common Issues

#### Analysis Fails to Start
**Symptoms**: Analysis doesn't begin after clicking start
**Causes**: 
- Missing application data
- Invalid parameters
- System connectivity issues
**Solutions**:
- Verify application data completeness
- Check parameter values
- Refresh page and retry
- Contact system administrator

#### Low Confidence Recommendations
**Symptoms**: Confidence scores below 60%
**Causes**:
- Incomplete application data
- Conflicting parameters
- Insufficient question responses
**Solutions**:
- Review and complete application data
- Reassess parameter values
- Answer additional qualifying questions
- Iterate analysis with refined inputs

#### Unexpected Recommendations
**Symptoms**: Recommendations don't align with expectations
**Causes**:
- Incorrect parameter values
- Missing context information
- Misunderstood question responses
**Solutions**:
- Review parameter settings
- Check question responses for accuracy
- Consider organizational constraints not captured
- Iterate with adjusted parameters

#### Performance Issues
**Symptoms**: Slow analysis completion
**Causes**:
- High system load
- Complex application analysis
- Large file uploads
**Solutions**:
- Retry during off-peak hours
- Break down complex analyses
- Optimize file uploads
- Contact system administrator

### Getting Help

#### Self-Service Resources
- **User Guide**: This comprehensive guide
- **FAQ**: Frequently asked questions
- **Video Tutorials**: Step-by-step walkthroughs
- **Best Practices**: Proven approaches and tips

#### Support Channels
- **Help Desk**: Technical support for system issues
- **Training**: Formal training sessions and workshops
- **Consultation**: Expert guidance for complex analyses
- **Community**: User community and knowledge sharing

#### Escalation Process
1. **Self-Service**: Try self-service resources first
2. **Help Desk**: Contact help desk for technical issues
3. **Subject Matter Experts**: Engage SMEs for methodology questions
4. **Management**: Escalate business-critical issues

### System Maintenance

#### Scheduled Maintenance
- **Maintenance Windows**: Planned system downtime
- **Advance Notice**: Notification of upcoming maintenance
- **Impact Assessment**: Expected impact on operations
- **Contingency Plans**: Alternative approaches during maintenance

#### Data Backup and Recovery
- **Automatic Backups**: Regular system backups
- **Data Recovery**: Process for recovering lost data
- **Business Continuity**: Maintaining operations during outages
- **Disaster Recovery**: Plans for major system failures

---

## Appendix

### Glossary

**6R Strategies**: The six cloud migration strategies (Rehost, Replatform, Refactor, Rearchitect, Rewrite, Retire/Replace)

**CMDB**: Configuration Management Database - repository of application and infrastructure data

**COTS**: Commercial Off-The-Shelf software purchased from vendors

**Confidence Score**: AI-generated score indicating the reliability of a recommendation

**Iteration**: Repeated analysis with modified parameters or additional data

**Parameter**: Configurable value that influences the analysis algorithm

**Qualifying Questions**: Dynamic questions generated to gather additional analysis data

### Contact Information

- **System Administrator**: admin@company.com
- **Help Desk**: helpdesk@company.com
- **Training Team**: training@company.com
- **Product Owner**: product@company.com

### Version History

- **v1.0**: Initial release with core 6R analysis functionality
- **v1.1**: Added bulk analysis and enhanced reporting
- **v1.2**: Improved AI algorithms and user interface
- **v2.0**: Added real-time collaboration and advanced analytics

---

*This user guide is maintained by the Migration UI Orchestrator team. For updates and additional resources, visit the internal documentation portal.* 