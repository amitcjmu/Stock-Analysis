/**
 * Agent Metadata Helper Functions
 * Extracted from AgentDetailPage.tsx for modularization
 */

import type { AgentMetadataHelpers } from '../types/AgentDetailTypes';

export const getAgentMetadataHelpers = (): AgentMetadataHelpers => {
  const getAgentRole = (name: string): string => {
    const roles: Record<string, string> = {
      'DataImportValidationAgent': 'Data Validation Specialist',
      'AttributeMappingAgent': 'Field Mapping Expert',
      'DataCleansingAgent': 'Data Quality Engineer',
      'AssetInventoryAgent': 'Asset Classification Specialist',
      'DependencyAnalysisAgent': 'Dependency Mapping Expert',
      'TechDebtAnalysisAgent': 'Technical Debt Assessor'
    };
    return roles[name] || 'Specialized Agent';
  };

  const getAgentSpecialization = (name: string): string => {
    const specializations: Record<string, string> = {
      'DataImportValidationAgent': 'Security scanning, PII detection, and data validation',
      'AttributeMappingAgent': 'Field mapping with confidence scoring and validation',
      'DataCleansingAgent': 'Data standardization and bulk processing operations',
      'AssetInventoryAgent': 'Asset classification and inventory management',
      'DependencyAnalysisAgent': 'System dependency mapping and analysis',
      'TechDebtAnalysisAgent': 'Technical debt assessment and recommendation'
    };
    return specializations[name] || 'General purpose agent operations';
  };

  const getAgentCapabilities = (name: string): string[] => {
    const capabilities: Record<string, string[]> = {
      'DataImportValidationAgent': ['PII Detection', 'Security Scanning', 'Data Validation', 'Compliance Checking'],
      'AttributeMappingAgent': ['Field Mapping', 'Confidence Scoring', 'Schema Analysis', 'Data Type Inference'],
      'DataCleansingAgent': ['Data Standardization', 'Bulk Processing', 'Quality Assessment', 'Format Conversion'],
      'AssetInventoryAgent': ['Asset Classification', 'Inventory Tracking', 'Categorization', 'Metadata Extraction'],
      'DependencyAnalysisAgent': ['Dependency Mapping', 'Impact Analysis', 'Relationship Discovery', 'Flow Analysis'],
      'TechDebtAnalysisAgent': ['Debt Assessment', 'Risk Analysis', 'Recommendation Generation', 'Priority Scoring']
    };
    return capabilities[name] || ['General Operations', 'Task Execution'];
  };

  const getAgentEndpoints = (name: string): string[] => {
    return [
      `/api/v1/agents/${name.toLowerCase()}/validate`,
      `/api/v1/agents/${name.toLowerCase()}/process`,
      `/api/v1/agents/${name.toLowerCase()}/status`
    ];
  };

  return {
    getAgentRole,
    getAgentSpecialization,
    getAgentCapabilities,
    getAgentEndpoints
  };
};