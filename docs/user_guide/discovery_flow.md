# Discovery Flow User Guide

## 📋 **Overview**

This guide provides step-by-step instructions for using the enhanced Discovery Flow with CrewAI agents, hierarchical crew management, shared memory, and intelligent collaboration. The Discovery Flow has been completely redesigned to leverage AI agents that learn and adapt, providing superior accuracy and insights for cloud migration planning.

## 🎯 **What's New in the Enhanced Discovery Flow**

### **AI-Powered Agent Teams**
- **6 Specialized Crews**: Field Mapping, Data Cleansing, Inventory Building, App-Server Dependencies, App-App Dependencies, and Technical Debt
- **21 Intelligent Agents**: Manager agents coordinate specialist agents for optimal results
- **Shared Memory**: Agents learn from each phase and share insights across crews
- **Real-Time Collaboration**: Agents collaborate in real-time to improve accuracy

### **Key Benefits**
- **90%+ Accuracy**: AI agents achieve superior field mapping and asset classification accuracy
- **Learning Capability**: System improves with each discovery session
- **Comprehensive Analysis**: Complete dependency mapping and technical debt assessment
- **6R Strategy Preparation**: Automatic preparation for Assessment phase with strategic recommendations

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

![Discovery Flow Entry Point](../screenshots/discovery-entry-point.png)

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

3. **Data Preview**
   - Review the first 10 rows of your data
   - Verify column headers and data quality
   - Note any obvious data issues

![Data Upload Interface](../screenshots/data-upload.png)

### **Step 3: Configure Discovery Options**

1. **Crew Configuration**
   ```
   ✅ Enable Field Mapping (Required)
   ✅ Enable Data Cleansing (Recommended) 
   ✅ Enable Inventory Building (Required)
   ✅ Enable Dependency Analysis (Recommended)
   ✅ Enable Technical Debt Analysis (For 6R preparation)
   ```

2. **Advanced Options**
   - **Parallel Execution**: Enable for faster processing
   - **Memory Sharing**: Enable for improved accuracy (Recommended)
   - **Knowledge Integration**: Apply industry patterns (Recommended)
   - **Confidence Threshold**: Set to 0.8 for high accuracy

3. **Click "Initialize Discovery Flow"**

![Configuration Options](../screenshots/discovery-configuration.png)

---

## 🧠 **Understanding the Discovery Flow Interface**

### **Main Dashboard Overview**

The Discovery Flow interface provides real-time visibility into all crew activities:

![Discovery Flow Dashboard](../screenshots/discovery-dashboard.png)

#### **1. Progress Overview**
- **Overall Progress**: Shows completion percentage across all crews
- **Current Phase**: Indicates which crew is currently active
- **Estimated Time**: Real-time estimate of remaining processing time
- **Session Info**: Session ID, flow fingerprint, and timing details

#### **2. Crew Status Cards**
Each crew has a dedicated status card showing:
- **Crew Name and Manager**: e.g., "Field Mapping Crew" managed by "Field Mapping Manager"
- **Progress Bar**: Visual progress indicator with percentage
- **Agent Status**: Individual agent status (completed, in-progress, pending)
- **Key Metrics**: Crew-specific metrics (confidence scores, assets processed, etc.)
- **Execution Time**: Time spent in current crew

#### **3. Real-Time Agent Activity**
- **Active Agents**: Shows which agents are currently working
- **Current Tasks**: Displays what each agent is currently doing
- **Collaboration Events**: Shows when agents share insights or coordinate
- **Performance Metrics**: Real-time efficiency and quality indicators

#### **4. Memory and Knowledge Visualization**
- **Shared Memory Usage**: Shows insights stored and cross-crew connections
- **Knowledge Base Hits**: Displays successful pattern matches
- **Learning Indicators**: Shows when agents learn new patterns
- **Memory Efficiency**: Real-time memory usage and optimization

---

## 📊 **Phase-by-Phase Walkthrough**

### **Phase 1: Field Mapping Crew** 🎯

**Purpose**: Analyzes your data structure and creates precise field mappings to migration standards.

#### **What Happens**
1. **Schema Analysis Expert** analyzes field meanings and relationships
2. **Attribute Mapping Specialist** creates precise mappings with confidence scores
3. **Field Mapping Manager** coordinates and validates the overall strategy

#### **User Interface**

![Field Mapping Phase](../screenshots/field-mapping-phase.png)

#### **What to Watch For**
- **High Confidence Scores**: Look for mappings with 0.8+ confidence
- **Unmapped Fields**: Review any fields that couldn't be automatically mapped
- **Semantic Insights**: Check the semantic patterns identified by agents

#### **User Actions Available**
- **Review Mappings**: Click "Review Field Mappings" to see detailed mapping results
- **Adjust Confidence**: Lower confidence threshold if too many fields unmapped
- **Manual Override**: Manually map any unmapped or incorrectly mapped fields
- **Knowledge Feedback**: Provide feedback to improve future mapping accuracy

#### **Success Indicators**
- ✅ Field mapping confidence > 0.8
- ✅ Unmapped fields < 10%
- ✅ Semantic patterns identified
- ✅ Validation rules created

### **Phase 2: Data Cleansing Crew** 🧹

**Purpose**: Cleanses and standardizes data using the field mapping insights.

#### **What Happens**
1. **Data Quality Manager** plans comprehensive cleansing strategy
2. **Data Validation Expert** validates data against field mapping rules
3. **Data Standardization Specialist** standardizes formats and values

#### **User Interface**

![Data Cleansing Phase](../screenshots/data-cleansing-phase.png)

#### **Key Metrics to Monitor**
- **Data Quality Score**: Overall quality improvement percentage
- **Records Processed**: Number of records cleaned
- **Issues Resolved**: Types and counts of data issues fixed
- **Standardization Applied**: List of standardization rules applied

#### **User Actions Available**
- **Quality Report**: Download detailed data quality report
- **Preview Cleaned Data**: See before/after comparison
- **Custom Rules**: Add custom validation or standardization rules
- **Exception Review**: Review records that couldn't be automatically cleaned

#### **Success Indicators**
- ✅ Data quality score > 0.85
- ✅ Standardization complete
- ✅ Critical data issues resolved
- ✅ Quality patterns learned

### **Phase 3: Inventory Building Crew** 🏭

**Purpose**: Classifies assets across servers, applications, and devices with cross-domain insights.

#### **What Happens**
1. **Inventory Manager** coordinates multi-domain classification strategy
2. **Server Classification Expert** identifies and categorizes servers
3. **Application Discovery Expert** catalogs applications and services
4. **Device Classification Expert** classifies network devices
5. **Cross-domain collaboration** generates relationship insights

#### **User Interface**

![Inventory Building Phase](../screenshots/inventory-building-phase.png)

#### **Asset Classification Results**
- **Servers Tab**: View classified servers with hosting capabilities
- **Applications Tab**: See discovered applications with business context
- **Devices Tab**: Review network devices and infrastructure
- **Relationships Tab**: Explore cross-domain insights and connections

#### **Key Metrics**
- **Assets Classified**: Total number of assets processed
- **Classification Accuracy**: Confidence in asset categorization
- **Cross-Domain Insights**: Relationships discovered between asset types
- **Business Criticality**: Business impact assessment for each asset

#### **User Actions Available**
- **Asset Details**: Click any asset for detailed classification information
- **Bulk Corrections**: Correct multiple asset classifications at once
- **Export Inventory**: Download complete asset inventory
- **Business Context**: Add business criticality and ownership information

#### **Success Indicators**
- ✅ Asset classification complete
- ✅ Cross-domain validation passed
- ✅ Business criticality assigned
- ✅ Hosting relationships identified

### **Phase 4: App-Server Dependencies** 🔗

**Purpose**: Maps application-to-server hosting relationships and infrastructure dependencies.

#### **What Happens**
1. **Dependency Manager** orchestrates hosting relationship analysis
2. **Application Topology Expert** maps applications to hosting infrastructure
3. **Infrastructure Relationship Analyst** analyzes server-application coupling

#### **User Interface**

![App-Server Dependencies](../screenshots/app-server-dependencies.png)

#### **Dependency Visualization**
- **Topology Map**: Interactive visualization of hosting relationships
- **Resource Utilization**: Server capacity and application resource usage
- **Dependency Strength**: Coupling strength between applications and servers
- **Migration Impact**: Potential impact of server changes on applications

#### **Key Insights**
- **Hosting Patterns**: Common hosting configurations identified
- **Resource Bottlenecks**: Servers with high utilization or constraints
- **Single Points of Failure**: Critical hosting dependencies
- **Migration Complexity**: Assessment of hosting migration difficulty

#### **User Actions Available**
- **Explore Topology**: Interactive exploration of hosting relationships
- **Resource Planning**: View resource utilization and capacity planning
- **Dependency Validation**: Confirm or correct hosting relationships
- **Migration Notes**: Add notes about hosting migration considerations

### **Phase 5: App-App Dependencies** 🔄

**Purpose**: Maps application-to-application integration dependencies and communication patterns.

#### **What Happens**
1. **Integration Manager** coordinates application dependency analysis
2. **Application Integration Expert** maps communication patterns
3. **API and Service Dependency Analyst** analyzes service-to-service dependencies

#### **User Interface**

![App-App Dependencies](../screenshots/app-app-dependencies.png)

#### **Integration Analysis**
- **Communication Flow**: Visual representation of application communication
- **API Dependencies**: Service-to-service API relationships
- **Integration Complexity**: Assessment of integration architecture complexity
- **Data Flows**: How data moves between applications

#### **Critical Insights**
- **Integration Patterns**: Common integration architectures identified
- **Critical Paths**: Essential application communication paths
- **API Contracts**: Service contracts and compatibility requirements
- **Migration Risks**: Integration-related migration risks

#### **User Actions Available**
- **Dependency Graph**: Explore interactive application dependency graph
- **API Documentation**: View discovered API contracts and documentation
- **Integration Validation**: Confirm application communication patterns
- **Risk Assessment**: Review integration-related migration risks

### **Phase 6: Technical Debt Assessment** 🏗️

**Purpose**: Evaluates technical debt and prepares 6R migration strategy recommendations.

#### **What Happens**
1. **Technical Debt Manager** coordinates comprehensive debt assessment
2. **Legacy Technology Analyst** evaluates technology stack age and debt
3. **Modernization Strategy Expert** recommends 6R strategies and modernization approaches
4. **Risk Assessment Specialist** evaluates migration risks and complexity

#### **User Interface**

![Technical Debt Assessment](../screenshots/technical-debt-assessment.png)

#### **Strategic Analysis Results**
- **Debt Scores**: Technical debt scores by asset and category
- **6R Recommendations**: Rehost, Replatform, Refactor, Rearchitect, Retire, Retain strategies
- **Modernization Roadmap**: Prioritized modernization recommendations
- **Risk Assessment**: Migration risks and mitigation strategies

#### **6R Strategy Dashboard**
```
📊 6R Strategy Distribution:
• Rehost: 25% (Lift and shift candidates)
• Replatform: 35% (Minor optimizations needed)
• Refactor: 20% (Code changes required)
• Rearchitect: 15% (Significant redesign needed)
• Retire: 3% (End-of-life applications)
• Retain: 2% (Keep on-premises)
```

#### **User Actions Available**
- **Strategy Review**: Review and adjust 6R strategy recommendations
- **Priority Setting**: Set migration priorities and wave planning
- **Risk Mitigation**: Review and plan risk mitigation strategies
- **Business Case**: Generate business case for modernization initiatives

---

## 🔍 **Advanced Features**

### **Real-Time Agent Monitoring**

#### **Agent Communication Panel**
- **Collaboration Events**: See when agents share insights
- **Decision Points**: View critical decisions made by manager agents
- **Learning Moments**: Watch agents learn new patterns from your data
- **Performance Metrics**: Real-time agent efficiency and quality scores

#### **Memory Analytics**
- **Insight Storage**: Track insights stored by each crew
- **Cross-Crew Sharing**: See how insights flow between crews
- **Knowledge Application**: View successful knowledge base pattern matches
- **Learning Progress**: Monitor improvements in agent accuracy

### **Feedback and Learning System**

#### **Providing Feedback**
1. **Field Mapping Corrections**
   - Click "Provide Feedback" on any mapping
   - Correct field mappings or confidence scores
   - Add context about field meanings
   - Submit to improve future accuracy

2. **Asset Classification Feedback**
   - Correct asset types or categories
   - Add business context and criticality
   - Confirm or adjust relationships
   - Provide migration preferences

3. **Dependency Validation**
   - Confirm or correct dependency relationships
   - Add missing dependencies
   - Adjust dependency strength assessments
   - Provide integration complexity feedback

#### **Learning Impact**
- **Immediate**: Corrections applied to current session
- **Future Sessions**: Patterns learned for future discoveries
- **Knowledge Base Updates**: Industry patterns updated based on feedback
- **Accuracy Improvement**: Measurable improvement in agent accuracy over time

### **Export and Integration**

#### **Export Options**
- **Complete Discovery Report**: Comprehensive PDF report with all findings
- **Asset Inventory**: Excel export of classified assets
- **Dependency Mappings**: Visio-compatible dependency diagrams
- **6R Strategy Report**: Strategic recommendations and business case
- **Raw Data Export**: JSON/CSV export for integration with other tools

#### **Assessment Flow Integration**
- **Automatic Handoff**: Discovery results automatically feed Assessment Flow
- **6R Strategy Input**: Technical debt assessment becomes 6R strategy foundation
- **Business Prioritization**: Asset criticality drives assessment prioritization
- **Risk Integration**: Migration risks inform assessment planning

---

## 🛠️ **Troubleshooting and Support**

### **Common Issues and Solutions**

#### **Field Mapping Issues**
**Issue**: Low confidence scores or many unmapped fields
**Solutions**:
- Lower confidence threshold to 0.6 for initial mapping
- Review data quality - clean field names and values
- Provide manual mappings for key fields
- Add field descriptions or context in source data

**Issue**: Incorrect field mappings
**Solutions**:
- Use manual override for specific mappings
- Provide feedback to improve agent learning
- Check field data patterns and examples
- Verify source data quality and consistency

#### **Performance Issues**
**Issue**: Slow processing or timeouts
**Solutions**:
- Reduce dataset size for initial testing
- Enable parallel execution if not already enabled
- Check system resources and network connectivity
- Contact support for large enterprise datasets (>10,000 assets)

#### **Agent Collaboration Issues**
**Issue**: Agents not sharing insights effectively
**Solutions**:
- Ensure memory sharing is enabled
- Check knowledge base loading status
- Verify agent collaboration configuration
- Review crew coordination metrics

### **Getting Help**

#### **Built-in Help**
- **Context Help**: Click "?" icons throughout the interface
- **Agent Insights**: Click on any agent to see what it's currently doing
- **Progress Details**: Click crew cards for detailed execution information
- **Performance Metrics**: Monitor efficiency and quality indicators

#### **Support Resources**
- **User Community**: Join user forums for tips and best practices
- **Documentation**: Access complete API and technical documentation
- **Training Videos**: Watch step-by-step video tutorials
- **Support Tickets**: Submit support requests for technical issues

#### **Best Practices**
- **Data Quality**: Ensure clean, consistent data for best results
- **Incremental Approach**: Start with smaller datasets to test and learn
- **Feedback Loop**: Provide feedback to improve agent accuracy
- **Regular Updates**: Keep knowledge bases updated with latest patterns

---

## 📊 **Success Metrics and KPIs**

### **Discovery Flow Success Indicators**
- **Completion Rate**: >95% successful completion of all phases
- **Field Mapping Accuracy**: >90% confidence in field mappings
- **Asset Classification Accuracy**: >92% correct asset categorization
- **Dependency Detection**: >88% accurate relationship mapping
- **6R Strategy Relevance**: >85% appropriate strategy recommendations

### **Business Value Metrics**
- **Time Savings**: 70% reduction in discovery preparation time
- **Accuracy Improvement**: 40% improvement in migration planning accuracy
- **Risk Reduction**: 60% reduction in migration-related surprises
- **Cost Optimization**: 25% improvement in migration cost estimates

### **Continuous Improvement**
- **Agent Learning**: Measurable improvement in accuracy over time
- **Pattern Recognition**: Improved industry pattern matching
- **Knowledge Growth**: Expansion of knowledge base patterns
- **User Satisfaction**: High user satisfaction with discovery insights

---

This comprehensive user guide ensures users can effectively leverage the enhanced Discovery Flow with CrewAI agents to achieve superior cloud migration discovery results. The AI-powered approach provides unprecedented accuracy and insights while learning and improving with each use. 