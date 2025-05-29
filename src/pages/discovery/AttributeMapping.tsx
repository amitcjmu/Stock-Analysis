import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import RawDataTable from '../../components/discovery/RawDataTable';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Settings, Brain, GraduationCap, CheckCircle, AlertTriangle, 
  ArrowRight, Lightbulb, Save, RefreshCw, Eye, MapPin,
  ThumbsUp, ThumbsDown, HelpCircle, Wand2, Database, Users, Target
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

// Critical attributes needed for 6R analysis and migration planning
const CRITICAL_ATTRIBUTES = {
  // Core Identity
  hostname: {
    field: 'hostname',
    description: 'Primary server/application identifier',
    importance: 'critical',
    usedFor: ['Asset identification', 'Dependency mapping', 'Migration tracking'],
    examples: ['srv-web-01', 'app-crm-prod', 'db-oracle-main'],
    category: 'identity',
    dataType: 'string'
  },
  asset_name: {
    field: 'asset_name', 
    description: 'Human-readable asset name',
    importance: 'critical',
    usedFor: ['User interface display', 'Reporting', 'Documentation'],
    examples: ['CRM Application', 'Web Server', 'Oracle Database'],
    category: 'identity',
    dataType: 'string'
  },
  application_name: {
    field: 'application_name',
    description: 'Specific application or service name',
    importance: 'critical',
    usedFor: ['Application portfolio mapping', 'Business service identification', 'Dependency analysis'],
    examples: ['Salesforce CRM', 'Payroll System', 'Customer Portal'],
    category: 'identity',
    dataType: 'string'
  },
  asset_type: {
    field: 'asset_type',
    description: 'Classification of asset (Application, Server, Database)',
    importance: 'critical',
    usedFor: ['6R strategy selection', 'Migration grouping', 'Resource planning'],
    examples: ['Application', 'Server', 'Database', 'Network Device'],
    category: 'classification',
    dataType: 'string'
  },
  
  // Enhanced Business Context
  department: {
    field: 'department',
    description: 'Business unit or department that owns the asset',
    importance: 'critical',
    usedFor: ['Wave planning', 'Business impact analysis', 'Stakeholder communication'],
    examples: ['Finance', 'HR', 'Sales', 'IT Operations', 'Marketing'],
    category: 'business',
    dataType: 'string'
  },
  business_criticality: {
    field: 'business_criticality',
    description: 'Business impact level of the asset',
    importance: 'critical',
    usedFor: ['6R prioritization', 'Risk assessment', 'Migration sequencing'],
    examples: ['Critical', 'High', 'Medium', 'Low'],
    category: 'business',
    dataType: 'string'
  },
  environment: {
    field: 'environment',
    description: 'Deployment environment (Production, Development, etc.)',
    importance: 'critical',
    usedFor: ['Migration wave planning', 'Risk assessment', 'Testing strategy'],
    examples: ['Production', 'Development', 'Staging', 'Test'],
    category: 'business',
    dataType: 'string'
  },
  
  // Dependencies (New Critical Category)
  dependencies: {
    field: 'dependencies',
    description: 'Applications or services this asset depends on',
    importance: 'critical',
    usedFor: ['Wave sequencing', 'Risk assessment', 'Migration planning'],
    examples: ['Database-01, Auth-Service', 'AD, Exchange', 'Oracle-DB, File-Server'],
    category: 'dependencies',
    dataType: 'array'
  },
  app_mapped_to: {
    field: 'app_mapped_to',
    description: 'Applications hosted or supported by this asset',
    importance: 'critical',
    usedFor: ['Server-application mapping', 'Impact analysis', 'Dependency planning'],
    examples: ['CRM-App, HR-Portal', 'E-commerce-Web', 'Analytics-Dashboard'],
    category: 'dependencies',
    dataType: 'array'
  },
  closely_coupled_apps: {
    field: 'closely_coupled_apps',
    description: 'Applications tightly coupled requiring joint migration',
    importance: 'high',
    usedFor: ['Migration grouping', 'Risk mitigation', 'Wave planning'],
    examples: ['Frontend-Backend pair', 'Microservices cluster', 'ERP modules'],
    category: 'dependencies',
    dataType: 'array'
  },
  upstream_dependencies: {
    field: 'upstream_dependencies',
    description: 'Services or systems this asset consumes from',
    importance: 'high',
    usedFor: ['Dependency sequencing', 'Prerequisites planning', 'Risk assessment'],
    examples: ['Identity-Service', 'Payment-Gateway', 'Data-Warehouse'],
    category: 'dependencies',
    dataType: 'array'
  },
  downstream_dependencies: {
    field: 'downstream_dependencies',
    description: 'Services or systems that consume from this asset',
    importance: 'high',
    usedFor: ['Impact analysis', 'Testing requirements', 'Rollback planning'],
    examples: ['Reporting-Service', 'Analytics-Engine', 'Mobile-Apps'],
    category: 'dependencies',
    dataType: 'array'
  },
  
  // Application Complexity Assessment
  application_complexity: {
    field: 'application_complexity',
    description: 'Technical complexity score of the application',
    importance: 'critical',
    usedFor: ['6R strategy selection', 'Timeline estimation', 'Resource planning'],
    examples: ['Low', 'Medium', 'High', 'Very High'],
    category: 'complexity',
    dataType: 'string'
  },
  cloud_readiness: {
    field: 'cloud_readiness',
    description: 'Assessment of cloud migration readiness',
    importance: 'critical',
    usedFor: ['6R strategy selection', 'Migration approach', 'Modernization planning'],
    examples: ['Ready', 'Needs Refactoring', 'Major Changes Required', 'Not Suitable'],
    category: 'complexity',
    dataType: 'string'
  },
  technical_debt: {
    field: 'technical_debt',
    description: 'Level of technical debt in the application',
    importance: 'high',
    usedFor: ['Modernization planning', 'Cost estimation', 'Risk assessment'],
    examples: ['Low', 'Medium', 'High', 'Critical'],
    category: 'complexity',
    dataType: 'string'
  },
  
  // Data Sources and Integration
  data_sources: {
    field: 'data_sources',
    description: 'External data sources or databases used',
    importance: 'high',
    usedFor: ['Data migration planning', 'Integration mapping', 'Dependency analysis'],
    examples: ['Oracle-DB, MySQL', 'SQL Server, MongoDB', 'File-shares, APIs'],
    category: 'integration',
    dataType: 'array'
  },
  integration_points: {
    field: 'integration_points',
    description: 'External system integration endpoints',
    importance: 'medium',
    usedFor: ['API migration', 'Integration testing', 'Connectivity planning'],
    examples: ['REST APIs, SOAP services', 'Message queues', 'File transfers'],
    category: 'integration',
    dataType: 'array'
  },
  
  // Technical Specifications (Enhanced)
  operating_system: {
    field: 'operating_system',
    description: 'Operating system family and version',
    importance: 'high',
    usedFor: ['6R Rehost/Replatform decisions', 'Compatibility analysis', 'License planning'],
    examples: ['Windows Server 2019', 'RHEL 8.4', 'Ubuntu 20.04'],
    category: 'technical',
    dataType: 'string'
  },
  cpu_cores: {
    field: 'cpu_cores',
    description: 'Number of CPU cores allocated',
    importance: 'high',
    usedFor: ['Right-sizing', 'Cost estimation', 'Performance planning'],
    examples: ['4', '8', '16', '32'],
    category: 'technical',
    dataType: 'number'
  },
  memory_gb: {
    field: 'memory_gb',
    description: 'RAM in gigabytes',
    importance: 'high',
    usedFor: ['Right-sizing', 'Cost estimation', 'Performance planning'],
    examples: ['8', '16', '32', '64'],
    category: 'technical',
    dataType: 'number'
  },
  storage_gb: {
    field: 'storage_gb',
    description: 'Storage capacity in gigabytes',
    importance: 'medium',
    usedFor: ['Cost estimation', 'Data migration planning'],
    examples: ['100', '500', '1000', '2000'],
    category: 'technical',
    dataType: 'number'
  },
  
  // Network & Location
  ip_address: {
    field: 'ip_address',
    description: 'Network IP address',
    importance: 'medium',
    usedFor: ['Network mapping', 'Security planning', 'Connectivity analysis'],
    examples: ['192.168.1.10', '10.0.1.50'],
    category: 'network',
    dataType: 'string'
  },
  location: {
    field: 'location',
    description: 'Physical or logical location',
    importance: 'medium',
    usedFor: ['Data residency', 'Compliance', 'Network latency planning'],
    examples: ['US-East', 'EU-West', 'On-Premises DC1'],
    category: 'network',
    dataType: 'string'
  },
  
  // Governance & Compliance
  application_owner: {
    field: 'application_owner',
    description: 'Person or team responsible for the application',
    importance: 'high',
    usedFor: ['Stakeholder engagement', 'Change management', 'Testing coordination'],
    examples: ['john.smith@company.com', 'CRM Team', 'Database Admin Team'],
    category: 'governance',
    dataType: 'string'
  },
  vendor: {
    field: 'vendor',
    description: 'Software vendor or manufacturer',
    importance: 'medium',
    usedFor: ['License migration', 'Support planning', 'Compatibility checks'],
    examples: ['Microsoft', 'Oracle', 'SAP', 'Custom'],
    category: 'governance',
    dataType: 'string'
  },
  version: {
    field: 'version',
    description: 'Software or application version',
    importance: 'medium',
    usedFor: ['Compatibility analysis', 'Upgrade planning', 'Support lifecycle'],
    examples: ['2019', '12.2', '8.1.4'],
    category: 'technical',
    dataType: 'string'
  },
  compliance_requirements: {
    field: 'compliance_requirements',
    description: 'Regulatory or compliance requirements',
    importance: 'high',
    usedFor: ['Cloud provider selection', 'Security planning', 'Audit preparation'],
    examples: ['SOX', 'HIPAA', 'GDPR', 'PCI-DSS'],
    category: 'governance',
    dataType: 'array'
  }
};

// Enhanced interfaces for attribute mapping
interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string;
  confidence: number;
  mapping_type: 'direct' | 'calculated' | 'manual';
  sample_values: string[];
  status: 'pending' | 'approved' | 'rejected' | 'ignored' | 'deleted';
  ai_reasoning: string;
  action?: 'ignore' | 'delete';
}

interface CustomAttribute {
  field: string;
  description: string;
  importance: 'critical' | 'high' | 'medium' | 'low';
  usedFor: string[];
  examples: string[];
  category: string;
  dataType: 'string' | 'number' | 'boolean' | 'array' | 'object';
  customField: boolean;
  createdBy?: string;
}

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
}

const AttributeMapping = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [importedData, setImportedData] = useState<any[]>([]);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);
  const [selectedMappings, setSelectedMappings] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState('data');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [crewAnalysis, setCrewAnalysis] = useState<CrewAnalysis[]>([]);
  const [mappingProgress, setMappingProgress] = useState({
    total: 0,
    mapped: 0,
    critical_mapped: 0,
    accuracy: 0
  });
  
  // Enhanced state for custom attributes and field actions
  const [customAttributes, setCustomAttributes] = useState<CustomAttribute[]>([]);
  const [showCustomAttributeDialog, setShowCustomAttributeDialog] = useState(false);
  const [newCustomAttribute, setNewCustomAttribute] = useState<Partial<CustomAttribute>>({
    category: 'custom',
    importance: 'medium',
    dataType: 'string',
    customField: true
  });
  const [fieldActions, setFieldActions] = useState<Record<string, 'ignore' | 'delete' | null>>({});
  const [showFieldActionDialog, setShowFieldActionDialog] = useState(false);
  const [selectedFieldForAction, setSelectedFieldForAction] = useState<string>('');
  const [actionReasoning, setActionReasoning] = useState<string>('');

  useEffect(() => {
    // Check if we came from Data Import with data
    const state = location.state as any;
    if (state?.importedData && state?.fromDataImport) {
      console.log('Received imported data from Data Import:', state.importedData);
      setImportedData(state.importedData);
      // Start AI crew analysis of the imported data
      analyzeImportedDataWithCrew(state.importedData);
    } else {
      // Try to fetch from previous steps or localStorage
      fetchImportedData();
    }
  }, [location.state]);

  const fetchImportedData = async () => {
    try {
      // Try multiple sources for data
      const assetsResponse = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=1&page_size=1000`);
      if (assetsResponse.assets && assetsResponse.assets.length > 0) {
        setImportedData(assetsResponse.assets);
        analyzeImportedDataWithCrew(assetsResponse.assets);
      } else {
        const storedData = localStorage.getItem('imported_assets');
        if (storedData) {
          const parsedData = JSON.parse(storedData);
          setImportedData(parsedData);
          analyzeImportedDataWithCrew(parsedData);
        }
      }
    } catch (error) {
      console.error('Failed to fetch imported data:', error);
    }
  };

  const analyzeImportedDataWithCrew = async (data: any[]) => {
    if (data.length === 0) return;
    
    setIsAnalyzing(true);
    
    try {
      // Analyze data structure with AI crew
      const columns = Object.keys(data[0] || {});
      const analysis = await generateFieldMappings(columns, data);
      
      setFieldMappings(analysis.mappings);
      setCrewAnalysis(analysis.crewAnalysis);
      setMappingProgress(analysis.progress);
      
    } catch (error) {
      console.error('Failed to analyze data with AI crew:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const generateFieldMappings = async (columns: string[], sampleData: any[]) => {
    // AI Crew Analysis: Field Mapping Specialist
    const mappings: FieldMapping[] = [];
    const crewAnalysis: CrewAnalysis[] = [];
    
    // Combine standard and custom attributes
    const allAttributes = { ...CRITICAL_ATTRIBUTES };
    customAttributes.forEach(attr => {
      allAttributes[attr.field] = attr;
    });
    
    // Field Mapping Agent Analysis
    crewAnalysis.push({
      agent: 'Field Mapping Specialist',
      task: 'Analyze imported columns and map to migration-critical attributes',
      findings: [
        `Detected ${columns.length} columns in imported dataset`,
        `Sample data contains ${sampleData.length} records for analysis`,
        `Using ${Object.keys(allAttributes).length} critical attributes (${customAttributes.length} custom)`,
        'Performing intelligent field matching using semantic analysis'
      ],
      recommendations: [
        'Review suggested mappings for accuracy',
        'Approve high-confidence mappings to train AI',
        'Create custom attributes for unique organizational fields',
        'Consider ignoring or deleting irrelevant fields'
      ],
      confidence: 0.85
    });
    
    // Map each column to critical attributes
    columns.forEach((column, index) => {
      // Check if field has been marked for action
      const fieldAction = fieldActions[column];
      if (fieldAction === 'ignore' || fieldAction === 'delete') {
        mappings.push({
          id: `mapping-${index}`,
          sourceField: column,
          targetAttribute: 'unmapped',
          confidence: 1.0,
          mapping_type: 'direct',
          sample_values: extractSampleValues(column, sampleData, 3),
          status: fieldAction === 'ignore' ? 'ignored' : 'deleted',
          ai_reasoning: `User marked field to ${fieldAction}`,
          action: fieldAction
        });
        return;
      }
      
      const bestMatch = findBestAttributeMatch(column, sampleData, allAttributes);
      const sampleValues = extractSampleValues(column, sampleData, 3);
      
      mappings.push({
        id: `mapping-${index}`,
        sourceField: column,
        targetAttribute: bestMatch.attribute,
        confidence: bestMatch.confidence,
        mapping_type: bestMatch.type,
        sample_values: sampleValues,
        status: bestMatch.confidence > 0.8 ? 'approved' : 'pending',
        ai_reasoning: bestMatch.reasoning
      });
    });
    
    // Suggest new custom attributes based on unmapped fields
    const unmappedFields = mappings.filter(m => m.targetAttribute === 'unmapped' && m.status === 'pending');
    if (unmappedFields.length > 0) {
      const customAttributeSuggestions = await suggestCustomAttributes(unmappedFields, sampleData);
      crewAnalysis.push({
        agent: 'Custom Attribute Specialist',
        task: 'Suggest new critical attributes for unmapped fields',
        findings: [
          `${unmappedFields.length} fields could not be mapped to existing attributes`,
          `Identified ${customAttributeSuggestions.length} potential custom attributes`,
          'Fields may represent organization-specific data elements'
        ],
        recommendations: [
          'Review suggested custom attributes for relevance',
          'Create custom attributes for important organizational fields',
          'Ignore fields that are not migration-relevant'
        ],
        confidence: 0.70
      });
    }
    
    // Enhanced Migration Planning Agent Analysis
    const criticalMapped = mappings.filter(m => 
      m.status === 'approved' && 
      allAttributes[m.targetAttribute]?.importance === 'critical'
    ).length;
    
    const totalCritical = Object.values(allAttributes)
      .filter(attr => attr.importance === 'critical').length;
    
    crewAnalysis.push({
      agent: 'Migration Planning Agent',
      task: 'Assess data readiness for 6R analysis and wave planning',
      findings: [
        `${criticalMapped}/${totalCritical} critical attributes mapped`,
        `${mappings.filter(m => m.confidence > 0.8).length} high-confidence mappings`,
        `${mappings.filter(m => m.status === 'ignored').length} fields marked to ignore`,
        `${mappings.filter(m => m.status === 'deleted').length} fields marked for deletion`,
        `Ready for ${criticalMapped >= 8 ? 'advanced' : 'basic'} migration analysis`
      ],
      recommendations: [
        criticalMapped < 8 ? 'Map remaining critical fields for complete analysis' : 'Proceed to data cleansing phase',
        'Review dependency mapping fields for application relationships',
        'Validate complexity and cloud readiness attribute mappings',
        'Consider creating custom attributes for unique business context'
      ],
      confidence: criticalMapped / totalCritical
    });
    
    // Enhanced 6R Strategy Agent Analysis
    const dependencyFieldsMapped = mappings.filter(m => 
      ['dependencies', 'app_mapped_to', 'closely_coupled_apps', 'upstream_dependencies', 'downstream_dependencies']
      .includes(m.targetAttribute) && m.status === 'approved'
    ).length;
    
    const complexityFieldsMapped = mappings.filter(m => 
      ['application_complexity', 'cloud_readiness', 'technical_debt']
      .includes(m.targetAttribute) && m.status === 'approved'
    ).length;
    
    crewAnalysis.push({
      agent: '6R Strategy Agent',
      task: 'Evaluate data completeness for 6R treatment recommendations',
      findings: [
        `Asset type mapping: ${mappings.find(m => m.targetAttribute === 'asset_type') ? 'Available' : 'Missing'}`,
        `Business context: ${mappings.find(m => m.targetAttribute === 'business_criticality') ? 'Available' : 'Missing'}`,
        `Dependency fields: ${dependencyFieldsMapped}/5 mapped`,
        `Complexity assessment: ${complexityFieldsMapped}/3 mapped`,
        `Technical specs: ${mappings.filter(m => ['cpu_cores', 'memory_gb', 'operating_system'].includes(m.targetAttribute)).length}/3 available`
      ],
      recommendations: [
        'Ensure asset_type is mapped for strategy classification',
        'Dependencies enable accurate wave sequencing',
        'Complexity fields enable informed 6R recommendations',
        'Technical specifications enable right-sizing analysis'
      ],
      confidence: 0.75
    });
    
    const progress = {
      total: mappings.length,
      mapped: mappings.filter(m => m.status === 'approved').length,
      critical_mapped: criticalMapped,
      accuracy: mappings.reduce((acc, m) => acc + m.confidence, 0) / mappings.length
    };
    
    return { mappings, crewAnalysis, progress };
  };

  const findBestAttributeMatch = (column: string, sampleData: any[], allAttributes: any) => {
    const columnLower = column.toLowerCase().replace(/[_\s-]/g, '');
    let bestMatch = { attribute: 'unmapped', confidence: 0, type: 'direct' as const, reasoning: '' };
    
    // Direct name matching
    for (const [key, attr] of Object.entries(allAttributes)) {
      const attrLower = key.toLowerCase().replace(/[_\s-]/g, '');
      if (columnLower === attrLower) {
        return {
          attribute: key,
          confidence: 0.95,
          type: 'direct' as const,
          reasoning: `Direct name match: '${column}' maps to '${key}'`
        };
      }
    }
    
    // Enhanced semantic matching with new critical attributes
    const semanticMappings = {
      // Core Identity
      hostname: ['host', 'server', 'machine', 'node', 'instance'],
      asset_name: ['name', 'title', 'label', 'asset'],
      application_name: ['app', 'application', 'service', 'system'],
      asset_type: ['type', 'category', 'class', 'kind'],
      
      // Business Context
      department: ['dept', 'division', 'unit', 'team', 'group', 'org'],
      business_criticality: ['criticality', 'priority', 'importance', 'critical', 'business'],
      environment: ['env', 'stage', 'tier'],
      
      // Dependencies
      dependencies: ['depends', 'dependency', 'requires', 'needs'],
      app_mapped_to: ['mapped', 'hosts', 'runs', 'supports'],
      closely_coupled_apps: ['coupled', 'linked', 'paired', 'connected'],
      upstream_dependencies: ['upstream', 'source', 'consumes'],
      downstream_dependencies: ['downstream', 'target', 'serves'],
      
      // Complexity
      application_complexity: ['complexity', 'complex', 'simple', 'difficulty'],
      cloud_readiness: ['ready', 'cloud', 'migration', 'suitable'],
      technical_debt: ['debt', 'legacy', 'outdated', 'modernization'],
      
      // Integration
      data_sources: ['datasource', 'database', 'source', 'data'],
      integration_points: ['integration', 'api', 'interface', 'endpoint'],
      
      // Technical
      operating_system: ['os', 'system', 'platform'],
      cpu_cores: ['cpu', 'cores', 'processors', 'vcpu'],
      memory_gb: ['memory', 'ram', 'gb'],
      storage_gb: ['storage', 'disk', 'space'],
      
      // Network
      ip_address: ['ip', 'address', 'network'],
      location: ['location', 'site', 'datacenter', 'region'],
      
      // Governance
      application_owner: ['owner', 'contact', 'responsible', 'manager'],
      vendor: ['vendor', 'manufacturer', 'supplier', 'provider'],
      version: ['version', 'release', 'build'],
      compliance_requirements: ['compliance', 'regulatory', 'sox', 'hipaa', 'gdpr']
    };
    
    for (const [attribute, keywords] of Object.entries(semanticMappings)) {
      for (const keyword of keywords) {
        if (columnLower.includes(keyword)) {
          const confidence = columnLower === keyword ? 0.9 : 0.7;
          if (confidence > bestMatch.confidence) {
            bestMatch = {
              attribute,
              confidence,
              type: 'direct' as const,
              reasoning: `Semantic match: '${column}' contains '${keyword}' → maps to '${attribute}'`
            };
          }
        }
      }
    }
    
    // Value-based inference with enhanced patterns
    if (bestMatch.confidence < 0.5) {
      const sampleValues = extractSampleValues(column, sampleData, 5);
      const inference = inferFromValues(sampleValues);
      if (inference.confidence > bestMatch.confidence) {
        bestMatch = {
          attribute: inference.attribute,
          confidence: inference.confidence,
          type: 'calculated' as const,
          reasoning: `Value pattern analysis: ${inference.reasoning}`
        };
      }
    }
    
    return bestMatch;
  };

  const extractSampleValues = (column: string, data: any[], count: number) => {
    return data
      .slice(0, count)
      .map(row => row[column])
      .filter(val => val !== null && val !== undefined && val !== '')
      .map(val => String(val));
  };

  const inferFromValues = (values: string[]) => {
    if (values.length === 0) return { attribute: 'unmapped', confidence: 0, reasoning: 'No sample values' };
    
    // IP address pattern
    if (values.some(v => /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(v))) {
      return { attribute: 'ip_address', confidence: 0.9, reasoning: 'IP address pattern detected' };
    }
    
    // Environment values
    const envValues = ['prod', 'production', 'dev', 'development', 'test', 'staging'];
    if (values.some(v => envValues.includes(v.toLowerCase()))) {
      return { attribute: 'environment', confidence: 0.8, reasoning: 'Environment values detected' };
    }
    
    // Asset type values
    const assetTypes = ['server', 'application', 'database', 'network'];
    if (values.some(v => assetTypes.includes(v.toLowerCase()))) {
      return { attribute: 'asset_type', confidence: 0.8, reasoning: 'Asset type values detected' };
    }
    
    // Numeric patterns
    if (values.every(v => /^\d+$/.test(v))) {
      const nums = values.map(Number);
      if (nums.every(n => n >= 1 && n <= 128)) {
        return { attribute: 'cpu_cores', confidence: 0.6, reasoning: 'Small integers suggest CPU cores' };
      }
      if (nums.every(n => n >= 1000 && n <= 100000)) {
        return { attribute: 'storage_gb', confidence: 0.6, reasoning: 'Large numbers suggest storage GB' };
      }
    }
    
    return { attribute: 'unmapped', confidence: 0, reasoning: 'No clear pattern detected' };
  };

  const handleApproveMapping = async (mappingId: string) => {
    setFieldMappings(prev => prev.map(mapping =>
      mapping.id === mappingId
        ? { ...mapping, status: 'approved' as const }
        : mapping
    ));
    
    // Update progress
    const approvedMappings = fieldMappings.filter(m => 
      m.status === 'approved' || m.id === mappingId
    );
    const criticalApproved = approvedMappings.filter(m =>
      CRITICAL_ATTRIBUTES[m.targetAttribute]?.importance === 'critical'
    );
    
    setMappingProgress(prev => ({
      ...prev,
      mapped: approvedMappings.length,
      critical_mapped: criticalApproved.length
    }));
  };

  const handleCustomMapping = (mappingId: string, newAttribute: string) => {
    setFieldMappings(prev => prev.map(mapping =>
      mapping.id === mappingId
        ? { 
          ...mapping, 
          targetAttribute: newAttribute,
          confidence: 1.0,
          mapping_type: 'transform' as const,
          status: 'approved' as const,
          ai_reasoning: 'User-defined mapping'
        }
        : mapping
    ));
  };

  const proceedToDataCleansing = () => {
    // Store attribute mappings and proceed
    const mappedData = {
      fieldMappings: fieldMappings.filter(m => m.status === 'approved'),
      importedData,
      mappingProgress,
      fromAttributeMapping: true
    };
    
    navigate('/discovery/data-cleansing', {
      state: mappedData
    });
  };

  const getAttributesByCategory = (category: string) => {
    return Object.entries(CRITICAL_ATTRIBUTES).filter(
      ([_, attr]) => attr.category === category
    );
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'text-green-600 bg-green-100';
    if (progress >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const suggestCustomAttributes = async (unmappedFields: FieldMapping[], sampleData: any[]) => {
    const suggestions: CustomAttribute[] = [];
    
    unmappedFields.forEach(field => {
      const sampleValues = field.sample_values;
      
      // Analyze sample values to suggest custom attribute properties
      let suggestedCategory = 'custom';
      let suggestedImportance = 'medium';
      let suggestedDataType = 'string';
      
      // Pattern analysis for category suggestion
      if (sampleValues.some(v => v.toLowerCase().includes('dept') || v.toLowerCase().includes('team'))) {
        suggestedCategory = 'business';
        suggestedImportance = 'high';
      } else if (sampleValues.some(v => /^\d+$/.test(v))) {
        suggestedDataType = 'number';
        suggestedCategory = 'technical';
      } else if (sampleValues.some(v => v.toLowerCase().includes('app') || v.toLowerCase().includes('service'))) {
        suggestedCategory = 'dependencies';
        suggestedImportance = 'high';
      }
      
      suggestions.push({
        field: field.sourceField,
        description: `Custom attribute for ${field.sourceField} (auto-suggested)`,
        importance: suggestedImportance as 'critical' | 'high' | 'medium' | 'low',
        usedFor: ['Migration analysis', 'Custom reporting'],
        examples: sampleValues.slice(0, 3),
        category: suggestedCategory,
        dataType: suggestedDataType as 'string' | 'number' | 'boolean' | 'array' | 'object',
        customField: true,
        createdBy: 'AI Suggestion'
      });
    });
    
    return suggestions;
  };

  const handleMappingAction = (mappingId: string, action: 'approve' | 'reject') => {
    setFieldMappings(mappings => 
      mappings.map(mapping => 
        mapping.id === mappingId 
          ? { ...mapping, status: action === 'approve' ? 'approved' : 'rejected' }
          : mapping
      )
    );
    
    // Update progress
    const updatedMappings = fieldMappings.map(mapping => 
      mapping.id === mappingId 
        ? { ...mapping, status: action === 'approve' ? 'approved' : 'rejected' }
        : mapping
    );
    
    updateMappingProgress(updatedMappings);
  };

  const updateMappingProgress = (mappings: FieldMapping[]) => {
    const allAttributes = { ...CRITICAL_ATTRIBUTES };
    customAttributes.forEach(attr => {
      allAttributes[attr.field] = attr;
    });
    
    const criticalMapped = mappings.filter(m => 
      m.status === 'approved' && 
      allAttributes[m.targetAttribute]?.importance === 'critical'
    ).length;
    
    setMappingProgress({
      total: mappings.length,
      mapped: mappings.filter(m => m.status === 'approved').length,
      critical_mapped: criticalMapped,
      accuracy: mappings.reduce((acc, m) => acc + m.confidence, 0) / mappings.length
    });
  };

  const handleContinueToDataCleansing = () => {
    // Prepare enhanced data with field mappings for Data Cleansing
    const approvedMappings = fieldMappings.filter(m => m.status === 'approved');
    
    navigate('/discovery/data-cleansing', {
      state: {
        fromAttributeMapping: true,
        fieldMappings: approvedMappings,
        customAttributes: customAttributes,
        importedData: importedData,
        mappingProgress: mappingProgress
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Attribute Mapping & AI Training
              </h1>
              <p className="text-lg text-gray-600">
                Train the AI crew to understand your data's attribute associations and field mappings
              </p>
            </div>

            {/* Progress Dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{mappingProgress.total}</h3>
                    <p className="text-xs text-gray-600">Total Fields</p>
                  </div>
                  <Database className="h-6 w-6 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-green-600">{mappingProgress.mapped}</h3>
                    <p className="text-xs text-gray-600">Mapped</p>
                  </div>
                  <CheckCircle className="h-6 w-6 text-green-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-purple-600">{mappingProgress.critical_mapped}</h3>
                    <p className="text-xs text-gray-600">Critical Mapped</p>
                  </div>
                  <Target className="h-6 w-6 text-purple-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-indigo-600">
                      {Math.round(mappingProgress.accuracy * 100)}%
                    </h3>
                    <p className="text-xs text-gray-600">Accuracy</p>
                  </div>
                  <Brain className="h-6 w-6 text-indigo-500" />
                </div>
              </div>
            </div>

            {/* AI Crew Analysis */}
            {crewAnalysis.length > 0 && (
              <div className="mb-8">
                <div className="bg-white rounded-lg shadow-md">
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center space-x-3">
                      <Users className="h-6 w-6 text-blue-500" />
                      <h2 className="text-xl font-semibold text-gray-900">AI Crew Analysis</h2>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {crewAnalysis.map((analysis, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-semibold text-gray-900">{analysis.agent}</h3>
                            <span className={`px-2 py-1 text-xs rounded-full ${getProgressColor(analysis.confidence * 100)}`}>
                              {Math.round(analysis.confidence * 100)}% confidence
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-3 font-medium">{analysis.task}</p>
                          
                          <div className="mb-3">
                            <h4 className="text-sm font-medium text-gray-700 mb-1">Findings:</h4>
                            <ul className="text-sm text-gray-600 space-y-1">
                              {analysis.findings.map((finding, idx) => (
                                <li key={idx}>• {finding}</li>
                              ))}
                            </ul>
                          </div>
                          
                          <div className="bg-blue-50 border-l-4 border-blue-400 p-3">
                            <h4 className="text-sm font-medium text-blue-800 mb-1">Recommendations:</h4>
                            <ul className="text-sm text-blue-700 space-y-1">
                              {analysis.recommendations.map((rec, idx) => (
                                <li key={idx}>• {rec}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Tabs */}
            <div className="mb-6">
              <nav className="flex space-x-8">
                {[
                  { id: 'data', label: 'Imported Data', icon: Database },
                  { id: 'mappings', label: 'Field Mappings', icon: MapPin },
                  { id: 'critical', label: 'Critical Attributes', icon: Target },
                  { id: 'progress', label: 'Training Progress', icon: Brain }
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                        activeTab === tab.id
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Imported Data Tab */}
            {activeTab === 'data' && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Imported Data Review</h2>
                    <p className="text-gray-600 mt-1">
                      Review your imported data before setting up attribute mappings
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <Database className="h-4 w-4" />
                    <span>{importedData.length} records imported</span>
                  </div>
                </div>
                
                {importedData.length > 0 ? (
                  <RawDataTable
                    data={importedData}
                    title="Imported Dataset for Attribute Mapping"
                    pageSize={10}
                    showLegend={false}
                  />
                ) : (
                  <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                    <Database className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                    <p className="text-gray-600 mb-4">
                      Import data first to begin attribute mapping.
                    </p>
                    <button
                      onClick={() => navigate('/discovery/data-import')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Go to Data Import
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Field Mappings Tab */}
            {activeTab === 'mappings' && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Field Mapping Suggestions</h2>
                  {isAnalyzing && (
                    <div className="flex items-center space-x-2 text-blue-600">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span className="text-sm">AI analyzing...</span>
                    </div>
                  )}
                </div>
                
                <div className="space-y-4">
                  {fieldMappings.map((mapping) => (
                    <div key={mapping.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <label className="text-sm font-medium text-gray-700">Source Field</label>
                              <div className="mt-1 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                                <div className="font-medium">{mapping.sourceField}</div>
                                <div className="text-sm text-gray-600">
                                  Sample: {mapping.sample_values.slice(0, 2).join(', ')}
                                  {mapping.sample_values.length > 2 && '...'}
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-center">
                              <ArrowRight className="h-6 w-6 text-gray-400" />
                            </div>
                            
                            <div>
                              <label className="text-sm font-medium text-gray-700">Target Attribute</label>
                              <div className="mt-1">
                                <select
                                  value={mapping.targetAttribute}
                                  onChange={(e) => handleCustomMapping(mapping.id, e.target.value)}
                                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                >
                                  <option value="unmapped">Select attribute...</option>
                                  {Object.entries(CRITICAL_ATTRIBUTES).map(([key, attr]) => (
                                    <option key={key} value={key}>
                                      {attr.field} ({attr.importance})
                                    </option>
                                  ))}
                                </select>
                              </div>
                            </div>
                          </div>
                          
                          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <div className="flex items-start space-x-2">
                              <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5" />
                              <p className="text-sm text-yellow-800">{mapping.ai_reasoning}</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="ml-4 flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${getProgressColor(mapping.confidence * 100)}`}>
                            {Math.round(mapping.confidence * 100)}%
                          </span>
                          {mapping.status === 'pending' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMappingAction(mapping.id, 'approve');
                              }}
                              className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                            >
                              Approve
                            </button>
                          )}
                          {mapping.status === 'approved' && (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Critical Attributes Tab */}
            {activeTab === 'critical' && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Critical Attributes for Migration</h2>
                
                {['identity', 'business', 'technical', 'network', 'governance'].map(category => (
                  <div key={category} className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4 capitalize">{category} Attributes</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {getAttributesByCategory(category).map(([key, attr]) => {
                        const isMapped = fieldMappings.some(m => m.targetAttribute === key && m.status === 'approved');
                        return (
                          <div key={key} className={`border rounded-lg p-4 ${isMapped ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900">{attr.field}</h4>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  attr.importance === 'critical' ? 'bg-red-100 text-red-800' :
                                  attr.importance === 'high' ? 'bg-orange-100 text-orange-800' :
                                  'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {attr.importance}
                                </span>
                                {isMapped && <CheckCircle className="h-4 w-4 text-green-600" />}
                              </div>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{attr.description}</p>
                            <div className="text-xs text-gray-500">
                              <strong>Used for:</strong> {attr.usedFor.join(', ')}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              <strong>Examples:</strong> {attr.examples.join(', ')}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Progress Tab */}
            {activeTab === 'progress' && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">AI Training Progress</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-4">Mapping Coverage</h3>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-600">Total Fields Mapped</span>
                          <span className="text-sm font-medium">{mappingProgress.mapped}/{mappingProgress.total}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${(mappingProgress.mapped / mappingProgress.total) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-600">Critical Attributes</span>
                          <span className="text-sm font-medium">{mappingProgress.critical_mapped}/7</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${(mappingProgress.critical_mapped / 7) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-600">AI Accuracy</span>
                          <span className="text-sm font-medium">{Math.round(mappingProgress.accuracy * 100)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-purple-600 h-2 rounded-full" 
                            style={{ width: `${mappingProgress.accuracy * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-4">Readiness Assessment</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">6R Analysis Ready</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${mappingProgress.critical_mapped >= 3 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {mappingProgress.critical_mapped >= 3 ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Wave Planning Ready</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${mappingProgress.critical_mapped >= 5 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {mappingProgress.critical_mapped >= 5 ? 'Yes' : 'Partial'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Cost Estimation Ready</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${fieldMappings.some(m => ['cpu_cores', 'memory_gb'].includes(m.targetAttribute) && m.status === 'approved') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {fieldMappings.some(m => ['cpu_cores', 'memory_gb'].includes(m.targetAttribute) && m.status === 'approved') ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Continue Button */}
            <div className="flex justify-center">
              <button
                onClick={handleContinueToDataCleansing}
                disabled={mappingProgress.critical_mapped < 3}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-lg font-medium transition-colors ${
                  mappingProgress.critical_mapped >= 3
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <span>Continue to Data Cleansing</span>
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
            
            {mappingProgress.critical_mapped < 3 && (
              <p className="text-center text-sm text-gray-600 mt-2">
                Map at least 3 critical attributes to proceed
              </p>
            )}
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default AttributeMapping; 