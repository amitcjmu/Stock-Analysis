# Discovery Flow API Documentation

## 📋 **Overview**

The Discovery Flow API provides comprehensive endpoints for managing the AI-powered cloud migration discovery process using CrewAI crews with hierarchical agent management, shared memory, and cross-crew collaboration.

## 🏗️ **Architecture Overview**

### **CrewAI Flow Structure**
The Discovery Flow follows CrewAI best practices with:
- **Hierarchical Process**: Manager agents coordinate specialist agents
- **Shared Memory**: LongTermMemory with vector storage across crews
- **Knowledge Bases**: Domain-specific knowledge integration
- **Planning**: Adaptive execution planning with success criteria
- **Collaboration**: Cross-crew agent communication and insight sharing

### **Flow Sequence**
```
initialize_discovery_flow → 
execute_field_mapping_crew → 
execute_data_cleansing_crew → 
execute_inventory_building_crew → 
execute_app_server_dependency_crew → 
execute_app_app_dependency_crew → 
execute_technical_debt_crew → 
execute_discovery_integration
```

## 🎯 **Base URLs**

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## 🔐 **Authentication**

All endpoints require:
- **Authorization Header**: `Bearer {jwt_token}`
- **Client Account Header**: `X-Client-Account-ID: {client_account_id}`

## 📊 **Discovery Flow Endpoints**

### **1. Flow Initialization**

#### `POST /discovery/flow/initialize`

Initialize a new Discovery Flow session with comprehensive planning.

**Request Body:**
```json
{
  "client_account_id": "string",
  "engagement_id": "string",
  "user_id": "string",
  "data_source": "cmdb_import|csv_upload|api_integration",
  "data_preview": [
    {
      "hostname": "web-server-01",
      "ip_address": "192.168.1.10",
      "application": "Web Application",
      "environment": "Production"
    }
  ],
  "configuration": {
    "enable_field_mapping": true,
    "enable_data_cleansing": true,
    "enable_inventory_building": true,
    "enable_dependency_analysis": true,
    "enable_technical_debt_analysis": true,
    "parallel_execution": true,
    "memory_sharing": true,
    "knowledge_integration": true
  }
}
```

**Response:**
```json
{
  "status": "initialized_with_planning",
  "session_id": "disc_flow_123456789",
  "flow_fingerprint": "fp_abcdef123456",
  "discovery_plan": {
    "phases": [
      {
        "name": "field_mapping",
        "crew": "FieldMappingCrew",
        "manager": "Field Mapping Manager",
        "dependencies": [],
        "success_criteria": [
          "field_mappings_confidence > 0.8",
          "unmapped_fields < 10%"
        ],
        "estimated_duration": "2-5 minutes"
      }
    ],
    "coordination_strategy": "hierarchical_with_collaboration",
    "memory_sharing": "enabled",
    "knowledge_integration": "cross_domain"
  },
  "crew_coordination": {
    "total_crews": 6,
    "total_agents": 21,
    "manager_agents": 6,
    "specialist_agents": 15
  },
  "shared_memory_id": "mem_vector_789012",
  "knowledge_base_refs": [
    "field_mapping_kb",
    "asset_classification_kb",
    "dependency_patterns_kb"
  ]
}
```

### **2. Crew Execution Endpoints**

#### `POST /discovery/flow/crews/field-mapping/execute`

Execute the Field Mapping Crew with manager coordination.

**Request Body:**
```json
{
  "session_id": "disc_flow_123456789",
  "data": [
    {
      "hostname": "web-server-01",
      "ip_address": "192.168.1.10",
      "application": "Web Application"
    }
  ],
  "options": {
    "use_shared_memory": true,
    "apply_knowledge_base": true,
    "enable_collaboration": true,
    "confidence_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "status": "completed",
  "execution_id": "exec_field_mapping_001",
  "crew_name": "FieldMappingCrew",
  "manager_agent": "Field Mapping Manager",
  "specialist_agents": [
    "Schema Analysis Expert",
    "Attribute Mapping Specialist"
  ],
  "execution_plan": {
    "planning_task": "completed",
    "schema_analysis_task": "completed", 
    "field_mapping_task": "completed"
  },
  "results": {
    "field_mappings": {
      "hostname": {
        "target_field": "asset_name",
        "confidence": 0.95,
        "mapping_type": "direct",
        "validation": "passed"
      },
      "ip_address": {
        "target_field": "primary_ip",
        "confidence": 0.98,
        "mapping_type": "direct",
        "validation": "passed"
      },
      "application": {
        "target_field": "hosted_applications",
        "confidence": 0.85,
        "mapping_type": "semantic",
        "validation": "passed"
      }
    },
    "confidence_scores": {
      "overall_confidence": 0.93,
      "high_confidence_fields": 3,
      "medium_confidence_fields": 0,
      "low_confidence_fields": 0
    },
    "unmapped_fields": [],
    "validation_results": {
      "total_validations": 3,
      "passed_validations": 3,
      "failed_validations": 0
    },
    "agent_insights": {
      "schema_analysis": {
        "field_relationships": ["hostname -> applications"],
        "semantic_patterns": ["server_identification", "network_configuration"]
      },
      "mapping_specialist": {
        "mapping_strategies": ["direct_mapping", "semantic_analysis"],
        "confidence_factors": ["pattern_recognition", "knowledge_base_match"]
      }
    }
  },
  "shared_memory_updates": {
    "insights_stored": 5,
    "knowledge_gained": ["hostname_patterns", "ip_validation_rules"]
  },
  "collaboration_activities": [
    {
      "from_agent": "Schema Analysis Expert",
      "to_agent": "Attribute Mapping Specialist", 
      "message_type": "field_insights",
      "insights": "Hostname pattern suggests web server infrastructure"
    }
  ],
  "performance_metrics": {
    "execution_time": "45 seconds",
    "memory_usage": "125 MB",
    "agent_efficiency": 0.92
  }
}
```

#### `POST /discovery/flow/crews/data-cleansing/execute`

Execute the Data Cleansing Crew using field mapping insights.

**Response:**
```json
{
  "status": "completed",
  "crew_name": "DataCleansingCrew",
  "manager_agent": "Data Quality Manager",
  "specialist_agents": [
    "Data Validation Expert",
    "Data Standardization Specialist"
  ],
  "results": {
    "cleaned_data": [
      {
        "asset_name": "web-server-01",
        "primary_ip": "192.168.1.10",
        "hosted_applications": ["Web Application"],
        "environment": "production",
        "data_quality_score": 0.96
      }
    ],
    "data_quality_metrics": {
      "completeness": 0.98,
      "accuracy": 0.94,
      "consistency": 0.92,
      "overall_quality": 0.95
    },
    "standardization_applied": [
      "hostname_normalization",
      "ip_address_validation",
      "environment_standardization"
    ],
    "validation_results": {
      "total_records": 1,
      "valid_records": 1,
      "invalid_records": 0,
      "quality_issues_resolved": 3
    }
  },
  "shared_memory_integration": {
    "field_mappings_applied": 3,
    "quality_patterns_learned": 2
  }
}
```

#### `POST /discovery/flow/crews/inventory-building/execute`

Execute the Inventory Building Crew with multi-domain classification.

**Response:**
```json
{
  "status": "completed",
  "crew_name": "InventoryBuildingCrew",
  "manager_agent": "Inventory Manager",
  "specialist_agents": [
    "Server Classification Expert",
    "Application Discovery Expert",
    "Device Classification Expert"
  ],
  "results": {
    "asset_inventory": {
      "servers": [
        {
          "asset_id": "srv_001",
          "asset_name": "web-server-01",
          "asset_type": "Physical Server",
          "primary_ip": "192.168.1.10",
          "environment": "production",
          "business_criticality": "high",
          "classification_confidence": 0.94,
          "infrastructure_role": "web_server",
          "hosting_capacity": "medium"
        }
      ],
      "applications": [
        {
          "asset_id": "app_001",
          "asset_name": "Web Application",
          "asset_type": "Web Application",
          "hosted_on": "srv_001",
          "environment": "production",
          "application_category": "web_service",
          "classification_confidence": 0.89
        }
      ],
      "devices": [],
      "classification_metadata": {
        "total_assets_classified": 2,
        "classification_accuracy": 0.92,
        "cross_domain_insights": 3
      }
    },
    "cross_domain_collaboration": [
      {
        "collaborating_agents": ["Server Classification Expert", "Application Discovery Expert"],
        "insight": "Web application hosted on physical server",
        "confidence": 0.91
      }
    ]
  }
}
```

#### `POST /discovery/flow/crews/app-server-dependency/execute`

Execute the App-Server Dependency Crew for hosting relationship analysis.

**Response:**
```json
{
  "status": "completed", 
  "crew_name": "AppServerDependencyCrew",
  "manager_agent": "Dependency Manager",
  "specialist_agents": [
    "Application Topology Expert",
    "Infrastructure Relationship Analyst"
  ],
  "results": {
    "app_server_dependencies": {
      "hosting_relationships": [
        {
          "application_id": "app_001",
          "application_name": "Web Application",
          "hosting_server_id": "srv_001", 
          "hosting_server_name": "web-server-01",
          "relationship_type": "hosted_on",
          "confidence": 0.96,
          "resource_utilization": {
            "cpu_allocation": "medium",
            "memory_allocation": "medium",
            "storage_dependency": "local"
          }
        }
      ],
      "resource_mappings": [
        {
          "server_id": "srv_001",
          "hosted_applications": ["app_001"],
          "resource_capacity": "available",
          "utilization_level": 0.65
        }
      ],
      "topology_insights": {
        "hosting_patterns": ["single_server_hosting"],
        "dependency_complexity": "low",
        "migration_considerations": ["application_server_coupling"]
      }
    }
  }
}
```

#### `POST /discovery/flow/crews/app-app-dependency/execute`

Execute the App-App Dependency Crew for application integration analysis.

**Response:**
```json
{
  "status": "completed",
  "crew_name": "AppAppDependencyCrew", 
  "manager_agent": "Integration Manager",
  "specialist_agents": [
    "Application Integration Expert",
    "API and Service Dependency Analyst"
  ],
  "results": {
    "app_app_dependencies": {
      "communication_patterns": [
        {
          "source_application": "app_001",
          "target_application": "database_service",
          "communication_type": "database_connection",
          "frequency": "high",
          "criticality": "high",
          "confidence": 0.87
        }
      ],
      "api_dependencies": [
        {
          "consumer_app": "app_001",
          "provider_service": "authentication_api",
          "api_type": "REST",
          "dependency_strength": "strong",
          "migration_impact": "high"
        }
      ],
      "integration_complexity": {
        "overall_complexity": "medium",
        "integration_points": 2,
        "critical_dependencies": 1,
        "migration_considerations": ["api_compatibility", "database_migration"]
      }
    }
  }
}
```

#### `POST /discovery/flow/crews/technical-debt/execute`

Execute the Technical Debt Crew for modernization assessment.

**Response:**
```json
{
  "status": "completed",
  "crew_name": "TechnicalDebtCrew",
  "manager_agent": "Technical Debt Manager", 
  "specialist_agents": [
    "Legacy Technology Analyst",
    "Modernization Strategy Expert",
    "Risk Assessment Specialist"
  ],
  "results": {
    "technical_debt_assessment": {
      "debt_scores": {
        "srv_001": {
          "technology_debt": 0.65,
          "architecture_debt": 0.45,
          "maintenance_debt": 0.55,
          "overall_debt_score": 0.55
        },
        "app_001": {
          "technology_debt": 0.40,
          "architecture_debt": 0.30,
          "maintenance_debt": 0.35,
          "overall_debt_score": 0.35
        }
      },
      "modernization_recommendations": [
        {
          "asset_id": "srv_001",
          "asset_name": "web-server-01",
          "six_r_strategy": "replatform",
          "modernization_priority": "medium",
          "recommended_actions": [
            "containerize_applications",
            "migrate_to_cloud_native"
          ],
          "effort_estimate": "medium",
          "risk_level": "low"
        },
        {
          "asset_id": "app_001", 
          "asset_name": "Web Application",
          "six_r_strategy": "refactor",
          "modernization_priority": "high",
          "recommended_actions": [
            "modernize_api_architecture",
            "implement_microservices"
          ],
          "effort_estimate": "high",
          "risk_level": "medium"
        }
      ],
      "risk_assessments": {
        "migration_risks": [
          {
            "risk_type": "technology_compatibility",
            "risk_level": "medium",
            "affected_assets": ["srv_001"],
            "mitigation_strategies": ["phased_migration", "compatibility_testing"]
          }
        ],
        "business_risks": [
          {
            "risk_type": "service_disruption",
            "risk_level": "low",
            "affected_services": ["Web Application"],
            "mitigation_strategies": ["blue_green_deployment"]
          }
        ]
      },
      "six_r_preparation": {
        "rehost_candidates": [],
        "replatform_candidates": ["srv_001"],
        "refactor_candidates": ["app_001"],
        "rearchitect_candidates": [],
        "retire_candidates": [],
        "retain_candidates": []
      }
    }
  }
}
```

### **3. Flow Status and Monitoring**

#### `GET /discovery/flow/status/{session_id}`

Get comprehensive flow status with crew coordination details.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "overall_status": "in_progress",
  "current_phase": "inventory_building",
  "completion_percentage": 65,
  "crew_status": {
    "field_mapping": {
      "status": "completed",
      "manager": "Field Mapping Manager",
      "agents_status": {
        "Schema Analysis Expert": "completed",
        "Attribute Mapping Specialist": "completed"
      },
      "success_criteria_met": true,
      "execution_time": "2 minutes"
    },
    "data_cleansing": {
      "status": "completed", 
      "manager": "Data Quality Manager",
      "agents_status": {
        "Data Validation Expert": "completed",
        "Data Standardization Specialist": "completed"
      },
      "success_criteria_met": true,
      "execution_time": "1.5 minutes"
    },
    "inventory_building": {
      "status": "in_progress",
      "manager": "Inventory Manager",
      "agents_status": {
        "Server Classification Expert": "completed",
        "Application Discovery Expert": "in_progress", 
        "Device Classification Expert": "pending"
      },
      "estimated_completion": "1 minute"
    }
  },
  "shared_memory_status": {
    "memory_id": "mem_vector_789012",
    "insights_stored": 15,
    "cross_crew_references": 8,
    "memory_usage": "245 MB"
  },
  "agent_collaboration_activities": [
    {
      "timestamp": "2025-01-27T10:30:00Z",
      "from_crew": "FieldMappingCrew",
      "to_crew": "DataCleansingCrew",
      "collaboration_type": "insight_sharing",
      "message": "Field mapping confidence scores available"
    }
  ],
  "performance_metrics": {
    "total_execution_time": "4.5 minutes",
    "average_crew_efficiency": 0.91,
    "memory_efficiency": 0.88,
    "collaboration_effectiveness": 0.93
  }
}
```

#### `GET /discovery/flow/crews/{crew_name}/details/{session_id}`

Get detailed crew execution information.

**Response:**
```json
{
  "crew_name": "FieldMappingCrew",
  "session_id": "disc_flow_123456789",
  "execution_details": {
    "manager_agent": {
      "name": "Field Mapping Manager",
      "role": "coordination_and_oversight",
      "tasks_delegated": 2,
      "decisions_made": 5,
      "coordination_effectiveness": 0.94
    },
    "specialist_agents": [
      {
        "name": "Schema Analysis Expert",
        "role": "semantic_field_analysis",
        "tasks_completed": 1,
        "insights_generated": 3,
        "collaboration_activities": 2,
        "performance_score": 0.91
      },
      {
        "name": "Attribute Mapping Specialist", 
        "role": "field_mapping_with_confidence",
        "tasks_completed": 1,
        "mappings_created": 3,
        "confidence_scores_generated": 3,
        "performance_score": 0.95
      }
    ],
    "task_execution_flow": [
      {
        "task_name": "planning_task",
        "assigned_to": "Field Mapping Manager",
        "status": "completed",
        "execution_time": "15 seconds",
        "output": "Field mapping execution plan with agent assignments"
      },
      {
        "task_name": "schema_analysis_task",
        "assigned_to": "Schema Analysis Expert",
        "status": "completed", 
        "execution_time": "25 seconds",
        "output": "Comprehensive field analysis report"
      },
      {
        "task_name": "field_mapping_task",
        "assigned_to": "Attribute Mapping Specialist",
        "status": "completed",
        "execution_time": "20 seconds", 
        "output": "Complete field mapping dictionary"
      }
    ],
    "collaboration_matrix": [
      {
        "agent_1": "Field Mapping Manager",
        "agent_2": "Schema Analysis Expert",
        "interactions": 3,
        "collaboration_type": "delegation_and_oversight"
      },
      {
        "agent_1": "Schema Analysis Expert",
        "agent_2": "Attribute Mapping Specialist",
        "interactions": 2,
        "collaboration_type": "insight_sharing"
      }
    ]
  },
  "knowledge_base_usage": {
    "knowledge_base_queries": 5,
    "relevant_patterns_found": 8,
    "knowledge_application_success": 0.87
  },
  "memory_interactions": {
    "memory_reads": 3,
    "memory_writes": 5,
    "cross_crew_insights_stored": 2
  }
}
```

### **4. Memory and Knowledge Management**

#### `GET /discovery/flow/memory/status/{session_id}`

Get shared memory status and insights.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "memory_status": {
    "memory_id": "mem_vector_789012",
    "storage_type": "vector",
    "total_insights": 18,
    "memory_size": "312 MB",
    "embedding_model": "text-embedding-3-small"
  },
  "insights_by_crew": {
    "field_mapping": {
      "insights_count": 5,
      "categories": ["field_patterns", "semantic_analysis", "mapping_confidence"]
    },
    "data_cleansing": {
      "insights_count": 4,
      "categories": ["quality_patterns", "standardization_rules"]
    },
    "inventory_building": {
      "insights_count": 9,
      "categories": ["classification_patterns", "cross_domain_insights", "asset_relationships"]
    }
  },
  "cross_crew_references": [
    {
      "source_crew": "field_mapping",
      "target_crew": "data_cleansing",
      "insight_type": "field_validation_rules",
      "reference_count": 3
    },
    {
      "source_crew": "data_cleansing", 
      "target_crew": "inventory_building",
      "insight_type": "quality_indicators",
      "reference_count": 4
    }
  ],
  "memory_analytics": {
    "retrieval_accuracy": 0.92,
    "insight_relevance": 0.89,
    "cross_crew_utilization": 0.85
  }
}
```

#### `GET /discovery/flow/knowledge/status/{session_id}`

Get knowledge base usage and effectiveness.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "knowledge_bases": [
    {
      "name": "field_mapping_kb",
      "type": "field_mapping_patterns",
      "sources": ["field_mapping_patterns.json"],
      "usage_statistics": {
        "queries": 15,
        "successful_matches": 12,
        "relevance_score": 0.87
      }
    },
    {
      "name": "asset_classification_kb",
      "type": "asset_classification_rules", 
      "sources": ["asset_classification_rules.json"],
      "usage_statistics": {
        "queries": 22,
        "successful_matches": 19,
        "relevance_score": 0.91
      }
    },
    {
      "name": "dependency_patterns_kb",
      "type": "dependency_analysis_patterns",
      "sources": ["dependency_analysis_patterns.json"],
      "usage_statistics": {
        "queries": 8,
        "successful_matches": 7,
        "relevance_score": 0.94
      }
    }
  ],
  "knowledge_effectiveness": {
    "overall_match_rate": 0.88,
    "average_relevance": 0.91,
    "knowledge_contribution_to_accuracy": 0.15
  }
}
```

### **5. Planning and Coordination**

#### `GET /discovery/flow/planning/status/{session_id}`

Get execution planning status and adaptations.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "planning_status": {
    "original_plan": {
      "estimated_total_time": "8 minutes",
      "planned_sequence": ["field_mapping", "data_cleansing", "inventory_building", "app_server_deps", "app_app_deps", "technical_debt"],
      "resource_allocation": "standard"
    },
    "current_execution": {
      "actual_time_elapsed": "4.5 minutes",
      "completion_percentage": 65,
      "sequence_adherence": "on_track"
    },
    "adaptive_adjustments": [
      {
        "phase": "inventory_building",
        "adjustment_type": "resource_reallocation", 
        "reason": "higher_data_complexity_detected",
        "impact": "15% additional processing time"
      }
    ],
    "success_criteria_tracking": [
      {
        "phase": "field_mapping",
        "criteria": "field_mappings_confidence > 0.8",
        "actual_value": 0.93,
        "status": "met"
      },
      {
        "phase": "data_cleansing",
        "criteria": "data_quality_score > 0.85",
        "actual_value": 0.95,
        "status": "met"
      }
    ],
    "next_phase_prediction": {
      "phase": "app_server_dependencies",
      "estimated_duration": "1.5 minutes",
      "confidence": 0.89
    }
  }
}
```

#### `POST /discovery/flow/planning/intelligence/{session_id}`

Get AI-powered planning intelligence and optimization recommendations.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "planning_intelligence": {
    "performance_analysis": {
      "crew_efficiency_scores": {
        "field_mapping": 0.94,
        "data_cleansing": 0.91,
        "inventory_building": 0.89
      },
      "bottleneck_identification": [
        {
          "location": "inventory_building.device_classification",
          "type": "resource_constraint",
          "impact": "minor",
          "recommendation": "parallel_processing"
        }
      ]
    },
    "optimization_recommendations": [
      {
        "category": "resource_allocation",
        "recommendation": "Increase memory allocation for inventory building crew",
        "expected_improvement": "15% faster execution",
        "implementation_priority": "medium"
      },
      {
        "category": "crew_coordination",
        "recommendation": "Enable parallel execution for app dependency crews",
        "expected_improvement": "25% reduction in total execution time",
        "implementation_priority": "high"
      }
    ],
    "predictive_analytics": {
      "completion_time_prediction": "7.2 minutes",
      "accuracy_prediction": 0.92,
      "resource_utilization_forecast": {
        "memory": "peak 450MB",
        "cpu": "average 65%"
      }
    }
  }
}
```

### **6. Collaboration and Analytics**

#### `GET /discovery/flow/collaboration/tracking/{session_id}`

Track agent collaboration activities and effectiveness.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "collaboration_tracking": {
    "intra_crew_collaboration": [
      {
        "crew": "FieldMappingCrew",
        "collaborations": [
          {
            "agents": ["Schema Analysis Expert", "Attribute Mapping Specialist"],
            "interaction_type": "insight_sharing",
            "frequency": "high",
            "effectiveness": 0.91
          }
        ]
      }
    ],
    "cross_crew_collaboration": [
      {
        "source_crew": "FieldMappingCrew",
        "target_crew": "DataCleansingCrew",
        "collaboration_type": "knowledge_handoff",
        "insights_shared": 5,
        "effectiveness": 0.94
      },
      {
        "source_crew": "DataCleansingCrew",
        "target_crew": "InventoryBuildingCrew",
        "collaboration_type": "quality_indicators",
        "insights_shared": 4,
        "effectiveness": 0.87
      }
    ],
    "collaboration_metrics": {
      "total_collaborations": 12,
      "successful_collaborations": 11,
      "average_effectiveness": 0.91,
      "knowledge_transfer_success_rate": 0.89
    }
  }
}
```

#### `GET /discovery/flow/collaboration/analytics/{session_id}`

Get detailed collaboration analytics and optimization insights.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "collaboration_analytics": {
    "collaboration_patterns": [
      {
        "pattern_type": "manager_specialist_coordination",
        "frequency": "high",
        "effectiveness": 0.93,
        "optimization_potential": "low"
      },
      {
        "pattern_type": "cross_domain_expert_collaboration",
        "frequency": "medium",
        "effectiveness": 0.87,
        "optimization_potential": "medium"
      }
    ],
    "communication_flow": {
      "total_messages": 28,
      "insight_messages": 18,
      "coordination_messages": 7,
      "clarification_messages": 3
    },
    "collaboration_effectiveness_by_phase": {
      "field_mapping": 0.94,
      "data_cleansing": 0.91,
      "inventory_building": 0.89
    },
    "improvement_recommendations": [
      {
        "area": "cross_crew_coordination",
        "recommendation": "Implement real-time insight sharing for inventory building",
        "expected_improvement": "12% better classification accuracy"
      }
    ]
  }
}
```

### **7. Performance and Monitoring**

#### `GET /discovery/flow/agents/performance/{session_id}`

Get detailed agent performance metrics.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "agent_performance": {
    "manager_agents": [
      {
        "name": "Field Mapping Manager",
        "crew": "FieldMappingCrew",
        "coordination_score": 0.94,
        "delegation_effectiveness": 0.91,
        "decision_quality": 0.96,
        "response_time": "2.3 seconds average"
      },
      {
        "name": "Inventory Manager",
        "crew": "InventoryBuildingCrew", 
        "coordination_score": 0.89,
        "delegation_effectiveness": 0.87,
        "decision_quality": 0.92,
        "response_time": "3.1 seconds average"
      }
    ],
    "specialist_agents": [
      {
        "name": "Schema Analysis Expert",
        "crew": "FieldMappingCrew",
        "task_completion_rate": 1.0,
        "insight_quality": 0.91,
        "collaboration_effectiveness": 0.88,
        "processing_speed": "high"
      },
      {
        "name": "Server Classification Expert",
        "crew": "InventoryBuildingCrew",
        "task_completion_rate": 1.0,
        "classification_accuracy": 0.94,
        "cross_domain_insights": 3,
        "processing_speed": "medium"
      }
    ],
    "performance_trends": {
      "efficiency_improvement": "5% over last 3 executions",
      "accuracy_trend": "stable_high",
      "collaboration_improvement": "8% better cross-crew communication"
    }
  }
}
```

#### `GET /discovery/flow/memory/analytics/{session_id}`

Get memory system analytics and optimization insights.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "memory_analytics": {
    "usage_statistics": {
      "total_memory_size": "312 MB",
      "active_insights": 18,
      "archived_insights": 5,
      "memory_efficiency": 0.88
    },
    "retrieval_performance": {
      "average_retrieval_time": "0.15 seconds",
      "cache_hit_rate": 0.82,
      "relevance_accuracy": 0.91
    },
    "insight_lifecycle": [
      {
        "insight_type": "field_patterns",
        "creation_phase": "field_mapping",
        "usage_phases": ["data_cleansing", "inventory_building"],
        "usage_frequency": "high",
        "value_score": 0.94
      }
    ],
    "optimization_opportunities": [
      {
        "area": "memory_compression",
        "potential_saving": "15% memory reduction",
        "impact": "minimal performance effect"
      },
      {
        "area": "insight_prioritization", 
        "potential_improvement": "20% faster retrieval",
        "implementation": "weighted_relevance_scoring"
      }
    ]
  }
}
```

### **8. UI Integration Endpoints**

#### `GET /discovery/flow/ui/dashboard-data/{session_id}`

Get comprehensive dashboard data for UI visualization.

**Response:**
```json
{
  "session_id": "disc_flow_123456789",
  "dashboard_data": {
    "overview": {
      "status": "in_progress",
      "completion": 65,
      "current_phase": "inventory_building",
      "estimated_remaining": "3.5 minutes"
    },
    "crew_cards": [
      {
        "crew_name": "FieldMappingCrew",
        "status": "completed",
        "manager": "Field Mapping Manager",
        "progress": 100,
        "agents": [
          {"name": "Schema Analysis Expert", "status": "completed"},
          {"name": "Attribute Mapping Specialist", "status": "completed"}
        ],
        "key_metrics": {
          "confidence": 0.93,
          "execution_time": "2 minutes"
        }
      },
      {
        "crew_name": "InventoryBuildingCrew",
        "status": "in_progress",
        "manager": "Inventory Manager",
        "progress": 75,
        "agents": [
          {"name": "Server Classification Expert", "status": "completed"},
          {"name": "Application Discovery Expert", "status": "in_progress"},
          {"name": "Device Classification Expert", "status": "pending"}
        ],
        "key_metrics": {
          "assets_classified": 5,
          "accuracy": 0.91
        }
      }
    ],
    "memory_visualization": {
      "insights_stored": 18,
      "memory_usage": "312 MB",
      "cross_crew_connections": 8,
      "knowledge_base_hits": 38
    },
    "collaboration_network": {
      "active_collaborations": 3,
      "total_insights_shared": 12,
      "collaboration_effectiveness": 0.91
    },
    "performance_charts": {
      "execution_timeline": [
        {"phase": "field_mapping", "start": "10:00:00", "end": "10:02:00", "duration": 120},
        {"phase": "data_cleansing", "start": "10:02:00", "end": "10:03:30", "duration": 90},
        {"phase": "inventory_building", "start": "10:03:30", "end": "ongoing", "duration": 150}
      ],
      "efficiency_trend": [
        {"phase": "field_mapping", "efficiency": 0.94},
        {"phase": "data_cleansing", "efficiency": 0.91},
        {"phase": "inventory_building", "efficiency": 0.89}
      ]
    }
  }
}
```

## 🔧 **Error Handling**

### **Standard Error Response Format**
```json
{
  "error": {
    "code": "CREW_EXECUTION_FAILED",
    "message": "Field Mapping Crew execution failed",
    "details": {
      "crew": "FieldMappingCrew",
      "failed_agent": "Schema Analysis Expert",
      "failure_reason": "insufficient_data_quality",
      "recovery_suggestions": [
        "improve_data_quality",
        "adjust_confidence_threshold",
        "enable_fallback_mapping"
      ]
    },
    "timestamp": "2025-01-27T10:30:00Z",
    "session_id": "disc_flow_123456789"
  }
}
```

### **Common Error Codes**

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `FLOW_INITIALIZATION_FAILED` | Flow initialization error | 400 |
| `CREW_EXECUTION_FAILED` | Crew execution error | 500 |
| `MEMORY_ACCESS_ERROR` | Shared memory access error | 500 |
| `KNOWLEDGE_BASE_ERROR` | Knowledge base loading error | 500 |
| `COLLABORATION_ERROR` | Agent collaboration failure | 500 |
| `PLANNING_ERROR` | Execution planning failure | 500 |
| `VALIDATION_ERROR` | Data validation failure | 422 |
| `AUTHENTICATION_ERROR` | Authentication failure | 401 |
| `AUTHORIZATION_ERROR` | Authorization failure | 403 |
| `RESOURCE_NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded | 429 |

## 📊 **Rate Limits**

| Endpoint Category | Rate Limit | Window |
|------------------|------------|---------|
| Flow Initialization | 10 requests | 1 hour |
| Crew Execution | 50 requests | 1 hour |
| Status Monitoring | 100 requests | 1 minute |
| Analytics | 200 requests | 1 hour |

## 🔍 **WebSocket Events**

### **Real-Time Flow Updates**

Connect to: `ws://localhost:8000/ws/discovery-flow/{session_id}`

**Event Types:**
```json
{
  "event_type": "crew_status_update",
  "session_id": "disc_flow_123456789",
  "data": {
    "crew": "InventoryBuildingCrew",
    "status": "in_progress",
    "progress": 75,
    "agent_updates": [
      {
        "agent": "Application Discovery Expert",
        "status": "processing",
        "current_task": "application_classification"
      }
    ]
  },
  "timestamp": "2025-01-27T10:35:00Z"
}
```

**Other Event Types:**
- `agent_collaboration_event`
- `memory_insight_stored`
- `knowledge_base_query`
- `planning_adjustment`
- `phase_completion`
- `error_occurrence`
- `performance_alert`

## 📋 **Best Practices**

### **1. Flow Execution**
- Always initialize flow before crew execution
- Monitor shared memory usage for large datasets
- Enable collaboration for better results
- Use appropriate confidence thresholds

### **2. Error Handling**
- Implement retry logic with exponential backoff
- Monitor crew execution status regularly
- Handle partial failures gracefully
- Use fallback mechanisms for critical flows

### **3. Performance Optimization**
- Use parallel execution when possible
- Monitor memory usage and optimize as needed
- Implement caching for repeated operations
- Monitor collaboration effectiveness

### **4. Security**
- Always include authentication headers
- Validate client account access
- Implement proper rate limiting
- Monitor for unusual activity patterns

---

This API documentation provides comprehensive coverage of the new Discovery Flow architecture with CrewAI best practices, hierarchical crew management, shared memory, and cross-crew collaboration capabilities. 