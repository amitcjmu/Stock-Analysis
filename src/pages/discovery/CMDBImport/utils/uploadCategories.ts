import { Database, Monitor, Activity, Lock } from 'lucide-react';
import type { UploadCategory } from '../CMDBImport.types';

export const uploadCategories: UploadCategory[] = [
  {
    id: 'cmdb',
    title: 'CMDB Export Data',
    description: 'Configuration Management Database exports with asset information',
    icon: Database,
    color: 'bg-blue-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files'],
    securityLevel: 'standard',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor']
  },
  {
    id: 'app-discovery',
    title: 'Application Discovery Data',
    description: 'Application portfolio and dependency scan results',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['Application scans', 'Dependency maps', 'Service inventories'],
    securityLevel: 'elevated',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'dependency_validator']
  },
  {
    id: 'infrastructure',
    title: 'Infrastructure Assessment',
    description: 'Server, network, and infrastructure discovery data',
    icon: Activity,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['Network scans', 'Server inventories', 'Performance data'],
    securityLevel: 'high',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'infrastructure_validator']
  },
  {
    id: 'sensitive',
    title: 'Sensitive Data Assets',
    description: 'Data containing PII, financial, or confidential information',
    icon: Lock,
    color: 'bg-red-500',
    acceptedTypes: ['.csv', '.xlsx'],
    examples: ['Customer data', 'Financial records', 'HR systems'],
    securityLevel: 'maximum',
    agents: ['format_validator', 'security_scanner', 'privacy_analyzer', 'data_quality_assessor', 'pii_detector', 'compliance_checker']
  }
];