# Discovery Flow - Correct Design According to Requirements

> **📖 For the complete detailed design with CrewAI Flow plots, agent collaboration, memory management, and comprehensive implementation details, see [DISCOVERY_FLOW_DETAILED_DESIGN.md](./DISCOVERY_FLOW_DETAILED_DESIGN.md)**

## 🎯 **Proper Flow Sequence**

Based on your requirements and following CrewAI best practices for high complexity + high precision use cases, here's how the Discovery Flow should be designed:

### **Phase 1: Field-Attribute Mapping** (FIRST - Critical Foundation)
```python
@start()
def initialize_discovery_flow(self):
    """Initialize with data structure analysis"""

@listen(initialize_discovery_flow)
def execute_field_mapping_crew(self, previous_result):
    """
    CREW: Field Mapping Specialists
    PURPOSE: Understand data structure before any processing
    
    Agents:
    - Schema Analysis Expert: Analyzes incoming data structure and field meanings
    - Attribute Mapping Specialist: Maps source fields to standard migration attributes
    
    Tasks:
    - Analyze field semantics and data types
    - Map to standard migration schema (asset_name, asset_type, environment, etc.)
    - Identify unmapped fields requiring clarification
    - Create field confidence scores
    
    OUTPUT: Complete field mapping dictionary + confidence scores
    """
```

### **Phase 2: Data Cleansing** (Based on Mapped Understanding)
```python
@listen(execute_field_mapping_crew)
def execute_data_cleansing_crew(self, previous_result):
    """
    CREW: Data Quality Specialists
    PURPOSE: Clean data based on understood field mappings
    
    Agents:
    - Data Validation Expert: Validates data against expected field types
    - Data Standardization Specialist: Standardizes formats and values
    
    Tasks:
    - Validate data quality using field mappings
    - Standardize formats (dates, IPs, names, etc.)
    - Handle missing/null values appropriately
    - Generate data quality metrics
    
    OUTPUT: Cleaned, standardized dataset ready for inventory building
    """
```

### **Phase 3: Inventory Building** (Asset Classification)
```python
@listen(execute_data_cleansing_crew)
def execute_inventory_building_crew(self, previous_result):
    """
    CREW: Asset Inventory Specialists
    PURPOSE: Build structured inventory of servers, devices, and applications
    
    Agents:
    - Server Classification Expert: Specializes in server/infrastructure assets
    - Application Discovery Expert: Identifies and categorizes applications
    - Device Classification Expert: Handles network devices, storage, etc.
    
    Tasks:
    - Classify assets into: Servers, Applications, Network Devices, Storage
    - Assign business criticality and environment classifications
    - Identify asset ownership and management details
    - Create structured asset records
    
    OUTPUT: Categorized asset inventory (servers, apps, devices)
    """
```

### **Phase 4: App-to-Server Dependency Mapping**
```python
@listen(execute_inventory_building_crew)
def execute_app_server_dependency_crew(self, previous_result):
    """
    CREW: App-Server Dependency Specialists
    PURPOSE: Map application to server hosting relationships
    
    Agents:
    - Application Topology Expert: Maps apps to their hosting infrastructure
    - Infrastructure Relationship Analyst: Understands server-app relationships
    
    Tasks:
    - Identify which applications run on which servers
    - Map application deployment patterns
    - Analyze resource utilization and sizing
    - Document hosting dependencies for migration planning
    
    OUTPUT: App-to-server dependency matrix
    """
```

### **Phase 5: App-to-App Dependency Mapping**
```python
@listen(execute_app_server_dependency_crew)
def execute_app_app_dependency_crew(self, previous_result):
    """
    CREW: Application Integration Specialists
    PURPOSE: Map application-to-application dependencies and communication
    
    Agents:
    - Application Integration Expert: Understands app communication patterns
    - API and Service Dependency Analyst: Maps service-to-service dependencies
    
    Tasks:
    - Identify application communication patterns
    - Map API dependencies and service calls
    - Analyze data flow between applications
    - Document integration complexity for migration sequencing
    
    OUTPUT: App-to-app dependency graph with communication details
    """
```

### **Phase 6: Technical Debt Evaluation**
```python
@listen(execute_app_app_dependency_crew)
def execute_technical_debt_crew(self, previous_result):
    """
    CREW: Technical Debt Assessment Specialists
    PURPOSE: Evaluate technical debt across all assets for migration strategy
    
    Agents:
    - Legacy Technology Analyst: Assesses outdated technologies and frameworks
    - Modernization Strategy Expert: Recommends modernization approaches
    - Risk Assessment Specialist: Evaluates migration risks and complexity
    
    Tasks:
    - Assess technology stack age and support status
    - Identify technical debt and modernization opportunities
    - Evaluate security and compliance gaps
    - Generate migration strategy recommendations (6R analysis prep)
    
    OUTPUT: Technical debt scores and modernization recommendations per asset
    """
```

### **Phase 7: Final Integration and Summary**
```python
@listen(execute_technical_debt_crew)
def execute_discovery_integration(self, previous_result):
    """
    FLOW STEP: Final integration and database persistence
    PURPOSE: Consolidate all analysis into structured output for Assessment Flow
    
    Process:
    - Combine all crew outputs into comprehensive asset profiles
    - Store structured data in database for Assessment Flow consumption
    - Generate discovery summary and quality metrics
    - Prepare data package for 6R treatment analysis
    
    OUTPUT: Complete discovery dataset ready for Assessment Flow
    """
```

## 🏗️ **Corrected Crew Specifications**

### **1. Field Mapping Crew** (Phase 1)
```python
def _execute_field_mapping_crew(self):
    """Execute Field Mapping Crew - FIRST in sequence"""
    
    schema_analyst = Agent(
        role="Schema Analysis Expert",
        goal="Analyze incoming data structure and understand field semantics",
        backstory="Expert in data schema analysis with deep knowledge of CMDB and migration data structures. Can understand field meanings from context and naming patterns.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    mapping_specialist = Agent(
        role="Attribute Mapping Specialist", 
        goal="Map source fields to standardized migration attributes with high confidence",
        backstory="Specialist in field mapping with extensive experience in migration data standardization. Expert in resolving ambiguous field mappings.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    # Collaborative tasks
    schema_analysis_task = Task(
        description=f"Analyze the structure and semantics of {len(self.state.raw_data)} records. Understand what each field represents in the context of IT asset management.",
        expected_output="Field analysis report with semantic understanding of each field",
        agent=schema_analyst
    )
    
    mapping_task = Task(
        description="Create precise mappings from source fields to standard migration attributes (asset_name, asset_type, environment, business_criticality, etc.). Provide confidence scores.",
        expected_output="Complete field mapping dictionary with confidence scores and unmapped fields",
        agent=mapping_specialist,
        context=[schema_analysis_task]
    )
    
    mapping_crew = Crew(
        agents=[schema_analyst, mapping_specialist],
        tasks=[schema_analysis_task, mapping_task],
        process=Process.sequential,
        verbose=True
    )
    
    return mapping_crew.kickoff({
        "raw_data": self.state.raw_data,
        "sample_records": self.state.raw_data[:5]  # Sample for analysis
    })
```

### **2. Data Cleansing Crew** (Phase 2)
```python
def _execute_data_cleansing_crew(self):
    """Execute Data Cleansing based on understood field mappings"""
    
    validation_expert = Agent(
        role="Data Validation Expert",
        goal="Validate data quality using the established field mappings",
        backstory="Expert in data validation with deep knowledge of IT asset data quality requirements and migration standards.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    standardization_specialist = Agent(
        role="Data Standardization Specialist",
        goal="Standardize data formats and values for consistent processing",
        backstory="Specialist in data standardization with expertise in normalizing IT asset data for migration workflows.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    # Tasks based on field mapping results
    validation_task = Task(
        description="Validate data quality using the field mappings. Check for missing values, invalid formats, inconsistent data.",
        expected_output="Data quality report with identified issues and validation results",
        agent=validation_expert
    )
    
    standardization_task = Task(
        description="Standardize data formats, normalize values, and ensure consistency across all records using field mappings.",
        expected_output="Cleaned and standardized dataset ready for inventory building",
        agent=standardization_specialist,
        context=[validation_task]
    )
    
    cleansing_crew = Crew(
        agents=[validation_expert, standardization_specialist],
        tasks=[validation_task, standardization_task],
        process=Process.sequential,
        verbose=True
    )
    
    return cleansing_crew.kickoff({
        "raw_data": self.state.raw_data,
        "field_mappings": self.state.field_mappings
    })
```

### **3. Inventory Building Crew** (Phase 3)
```python
def _execute_inventory_building_crew(self):
    """Build comprehensive asset inventory"""
    
    server_expert = Agent(
        role="Server Classification Expert",
        goal="Identify and classify server and infrastructure assets",
        backstory="Expert in server and infrastructure classification with deep knowledge of enterprise environments and migration requirements.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    app_expert = Agent(
        role="Application Discovery Expert",
        goal="Identify and categorize application assets and services",
        backstory="Specialist in application discovery and classification with expertise in enterprise application portfolios.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    device_expert = Agent(
        role="Device Classification Expert",
        goal="Classify network devices, storage systems, and other infrastructure components",
        backstory="Expert in infrastructure device classification with knowledge of enterprise IT environments.",
        llm=self.crewai_service.llm,
        verbose=True
    )
    
    # Collaborative inventory building
    server_classification_task = Task(
        description="Classify servers and infrastructure assets using cleaned data. Assign environment, criticality, and technical details.",
        expected_output="Classified server inventory with technical specifications and migration readiness",
        agent=server_expert
    )
    
    app_classification_task = Task(
        description="Identify and classify applications and services. Understand application types and business functions.",
        expected_output="Application inventory with business context and technical characteristics",
        agent=app_expert
    )
    
    device_classification_task = Task(
        description="Classify network devices, storage systems, and other infrastructure components.",
        expected_output="Device inventory with technical specifications and migration considerations",
        agent=device_expert
    )
    
    inventory_crew = Crew(
        agents=[server_expert, app_expert, device_expert],
        tasks=[server_classification_task, app_classification_task, device_classification_task],
        process=Process.sequential,  # Could be parallel for better performance
        verbose=True
    )
    
    return inventory_crew.kickoff({
        "cleaned_data": self.state.parsed_data,
        "field_mappings": self.state.field_mappings
    })
```

## 🔄 **Current Issues to Fix**

### **1. Wrong Flow Sequence**
```python
# CURRENT (WRONG):
initialize → data_ingestion → asset_analysis → field_mapping → quality → integration

# SHOULD BE (CORRECT):
initialize → field_mapping → data_cleansing → inventory_building → app_server_deps → app_app_deps → technical_debt → integration
```

### **2. Missing Specialized Crews**
- **No dependency mapping crews** (critical for your requirements)
- **No technical debt evaluation crew** (needed for 6R preparation)
- **Generic crews instead of specialized ones**

### **3. Task Dependencies Issues**
```python
# CURRENT PROBLEM:
# Trying to classify assets before understanding field meanings
@listen(execute_asset_analysis_crew)
def execute_field_mapping_crew(self, previous_result):

# SHOULD BE:
# Understand fields first, then process data
@listen(initialize_discovery_flow)
def execute_field_mapping_crew(self, previous_result):
```

## 📊 **Recommendation: Complete Redesign**

The current implementation needs a complete restructure to match your requirements. The issues are:

1. **Flow sequence is backwards** - field mapping must be first
2. **Crews are too generic** - need specialized dependency and technical debt crews
3. **Missing critical analysis phases** - no app-to-app dependencies or technical debt evaluation
4. **Wrong task dependencies** - trying to process before understanding

Would you like me to implement the corrected Discovery Flow design that properly follows:
- Your specific flow sequence (field mapping → cleansing → inventory → dependencies → technical debt)
- CrewAI best practices for crew specialization
- Proper task dependencies and state management
- Integration for Assessment Flow preparation

This will create a single, consistent design pattern that eliminates the parallel designs causing confusion. 