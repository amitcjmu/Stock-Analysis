/**
 * Page Context Registry - Maps routes to rich context metadata for the AI Chat Assistant
 *
 * This registry provides structured context about each page including:
 * - Page name and description
 * - Flow type and workflow phase
 * - Available features and actions
 * - Help topics and FAQ
 * - Related documentation links
 *
 * Issue: #1219 - [Frontend] Page Context Registry
 * Milestone: Contextual AI Chat Assistant
 */

export type FlowType =
  | 'discovery'
  | 'collection'
  | 'assessment'
  | 'planning'
  | 'execute'
  | 'modernize'
  | 'decommission'
  | 'finops'
  | 'observability'
  | 'admin'
  | 'general';

export interface WorkflowInfo {
  phase: string;
  step: number;
  totalSteps: number;
  nextStep?: string;
  previousStep?: string;
}

export interface FAQ {
  question: string;
  answer: string;
}

export interface PageContext {
  page_name: string;
  route: string;
  route_pattern: string; // Pattern with wildcards for matching
  flow_type: FlowType;
  description: string;
  features: string[];
  actions: string[];
  help_topics: string[];
  workflow?: WorkflowInfo;
  faq: FAQ[];
  related_docs?: string[];
  tips?: string[];
}

// Helper to create route patterns for dynamic routes
const createRoutePattern = (route: string): string => {
  return route.replace(/:[\w]+/g, '*');
};

/**
 * Complete Page Context Registry
 * Organized by flow type for easy maintenance
 */
export const PAGE_CONTEXT_REGISTRY: Record<string, PageContext> = {
  // ============================================
  // DISCOVERY FLOW PAGES
  // ============================================

  '/discovery': {
    page_name: 'Discovery Overview',
    route: '/discovery',
    route_pattern: '/discovery',
    flow_type: 'discovery',
    description: 'The Discovery phase helps you import, analyze, and understand your IT infrastructure before migration.',
    features: [
      'Start new discovery flow',
      'View existing discovery flows',
      'Track discovery progress',
      'Access discovery phases',
    ],
    actions: [
      'Create new discovery flow',
      'Resume existing flow',
      'View flow status',
    ],
    help_topics: ['discovery flow', 'CMDB import', 'infrastructure analysis'],
    workflow: {
      phase: 'Overview',
      step: 0,
      totalSteps: 7,
      nextStep: 'Data Import',
    },
    faq: [
      {
        question: 'What is the Discovery phase?',
        answer: 'Discovery is the first phase where you import your CMDB data, map attributes to the target schema, cleanse data quality issues, and build an inventory of assets for migration planning.',
      },
      {
        question: 'How do I start a new discovery?',
        answer: 'Click "Start Discovery" to create a new flow. You\'ll begin by importing your CMDB data in CSV or Excel format.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/00_Discovery_Flow_Complete_Guide.md'],
    tips: [
      'Prepare your CMDB export in CSV or Excel format before starting',
      'Ensure your data includes application names, servers, and dependencies',
    ],
  },

  '/discovery/dashboard': {
    page_name: 'Discovery Dashboard',
    route: '/discovery/dashboard',
    route_pattern: '/discovery/dashboard',
    flow_type: 'discovery',
    description: 'Monitor all your discovery flows and track their progress through the pipeline.',
    features: [
      'View all discovery flows',
      'Track flow progress',
      'See completion statistics',
      'Access individual flow details',
    ],
    actions: [
      'Filter flows by status',
      'Sort by date or progress',
      'Navigate to specific flow',
    ],
    help_topics: ['flow management', 'progress tracking', 'flow status'],
    faq: [
      {
        question: 'What do the different flow statuses mean?',
        answer: 'Running = actively processing, Paused = waiting for user action, Completed = all phases done, Failed = encountered an error.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/01_Overview.md'],
  },

  '/discovery/data-import': {
    page_name: 'Data Import',
    route: '/discovery/data-import',
    route_pattern: '/discovery/data-import',
    flow_type: 'discovery',
    description: 'Import your CMDB or asset inventory data from CSV, Excel, or other formats.',
    features: [
      'Drag-and-drop file upload',
      'Support for CSV and Excel formats',
      'AI-powered data analysis',
      'Preview imported data',
      'Automatic column detection',
    ],
    actions: [
      'Upload CMDB file',
      'Preview data',
      'Start AI analysis',
      'Proceed to attribute mapping',
    ],
    help_topics: ['CMDB import', 'file upload', 'data formats', 'column mapping'],
    workflow: {
      phase: 'Data Import',
      step: 1,
      totalSteps: 7,
      nextStep: 'Attribute Mapping',
      previousStep: 'Overview',
    },
    faq: [
      {
        question: 'What file formats are supported?',
        answer: 'We support CSV (.csv) and Excel (.xlsx, .xls) files. The file should have column headers in the first row.',
      },
      {
        question: 'How large can my file be?',
        answer: 'Files up to 50MB are supported. For larger datasets, consider splitting into multiple files or using the API integration.',
      },
      {
        question: 'What columns should my file have?',
        answer: 'At minimum, include application name and server name. Recommended: environment, OS, IP address, dependencies, business criticality.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/02_Data_Import.md'],
    tips: [
      'Remove any empty rows or columns before uploading',
      'Use consistent naming conventions for applications',
      'Include dependency information if available',
    ],
  },

  // Alias for cmdb-import route (actual URL used by the application)
  '/discovery/cmdb-import': {
    page_name: 'Secure Data Import',
    route: '/discovery/cmdb-import',
    route_pattern: '/discovery/cmdb-import',
    flow_type: 'discovery',
    description: 'Upload migration data files for AI-powered validation and security analysis. Our specialized agents ensure data quality, security, and privacy compliance before processing.',
    features: [
      'Drag-and-drop file upload',
      'Support for CSV and Excel formats',
      'AI-powered data analysis',
      'Security and privacy validation',
      'Enterprise data validation agents',
      'Sensitive data detection',
    ],
    actions: [
      'Upload CMDB file',
      'Upload application discovery data',
      'Upload sensitive data assets',
      'Preview data',
      'Start AI analysis',
      'Proceed to attribute mapping',
    ],
    help_topics: ['CMDB import', 'file upload', 'data formats', 'security validation', 'data privacy'],
    workflow: {
      phase: 'Data Import',
      step: 1,
      totalSteps: 7,
      nextStep: 'Attribute Mapping',
      previousStep: 'Overview',
    },
    faq: [
      {
        question: 'What file formats are supported?',
        answer: 'We support CSV (.csv) and Excel (.xlsx, .xls) files. The file should have column headers in the first row.',
      },
      {
        question: 'How large can my file be?',
        answer: 'Files up to 50MB are supported. For larger datasets, consider splitting into multiple files or using the API integration.',
      },
      {
        question: 'What columns should my file have?',
        answer: 'At minimum, include application name and server name. Recommended: environment, OS, IP address, dependencies, business criticality.',
      },
      {
        question: 'How is my data secured?',
        answer: 'All uploaded data is encrypted in transit and at rest. Our AI agents scan for sensitive information like PII, credentials, and confidential data to ensure compliance.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/02_Data_Import.md'],
    tips: [
      'Remove any empty rows or columns before uploading',
      'Use consistent naming conventions for applications',
      'Include dependency information if available',
      'Avoid uploading files containing passwords or API keys',
    ],
  },

  '/discovery/attribute-mapping': {
    page_name: 'Attribute Mapping',
    route: '/discovery/attribute-mapping',
    route_pattern: '/discovery/attribute-mapping*',
    flow_type: 'discovery',
    description: 'Map your source columns to the target schema using AI-assisted suggestions.',
    features: [
      'AI-suggested field mappings',
      'Confidence scores for suggestions',
      'Manual mapping override',
      'Bulk approval of mappings',
      'Three-column mapper view',
    ],
    actions: [
      'Review AI suggestions',
      'Override incorrect mappings',
      'Approve field mappings',
      'Skip unmapped fields',
      'Proceed to data cleansing',
    ],
    help_topics: ['field mapping', 'attribute mapping', 'schema mapping', 'AI suggestions'],
    workflow: {
      phase: 'Attribute Mapping',
      step: 2,
      totalSteps: 7,
      nextStep: 'Data Cleansing',
      previousStep: 'Data Import',
    },
    faq: [
      {
        question: 'What do the confidence scores mean?',
        answer: 'Green (>80%) = high confidence, likely correct. Yellow (50-80%) = medium confidence, review recommended. Red (<50%) = low confidence, needs manual review.',
      },
      {
        question: 'How do I override a mapping?',
        answer: 'Click on any mapping row, then use the dropdown to select a different target field, or click "No mapping" to skip the field.',
      },
      {
        question: 'What if my field isn\'t in the target schema?',
        answer: 'You can mark it as "Custom Field" to preserve the data, or skip it if not needed for migration planning.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/03_Attribute_Mapping.md'],
    tips: [
      'Review low-confidence mappings first',
      'Use bulk approval for high-confidence mappings',
      'Consider business context when overriding suggestions',
    ],
  },

  '/discovery/data-cleansing': {
    page_name: 'Data Cleansing',
    route: '/discovery/data-cleansing',
    route_pattern: '/discovery/data-cleansing*',
    flow_type: 'discovery',
    description: 'Review and resolve data quality issues identified by AI analysis.',
    features: [
      'Data quality score',
      'Issue categorization',
      'AI recommendations',
      'Bulk resolution',
      'Manual data editing',
    ],
    actions: [
      'Review quality issues',
      'Accept AI recommendations',
      'Edit data manually',
      'Dismiss false positives',
      'Proceed to validation',
    ],
    help_topics: ['data quality', 'data cleansing', 'duplicate detection', 'missing values'],
    workflow: {
      phase: 'Data Cleansing',
      step: 3,
      totalSteps: 7,
      nextStep: 'Data Validation',
      previousStep: 'Attribute Mapping',
    },
    faq: [
      {
        question: 'What types of issues does it detect?',
        answer: 'Duplicates, missing required fields, invalid formats, inconsistent naming, orphan records, and data anomalies.',
      },
      {
        question: 'Can I skip data cleansing?',
        answer: 'Yes, but we recommend addressing critical issues as they can affect migration planning accuracy.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/04_Data_Cleansing.md'],
  },

  '/discovery/data-validation': {
    page_name: 'Data Validation',
    route: '/discovery/data-validation',
    route_pattern: '/discovery/data-validation*',
    flow_type: 'discovery',
    description: 'Validate cleansed data against business rules and migration requirements.',
    features: [
      'Business rule validation',
      'Completeness checks',
      'Consistency verification',
      'Validation report',
    ],
    actions: [
      'Run validation checks',
      'Review validation results',
      'Address validation failures',
      'Proceed to inventory',
    ],
    help_topics: ['data validation', 'business rules', 'data completeness'],
    workflow: {
      phase: 'Data Validation',
      step: 4,
      totalSteps: 7,
      nextStep: 'Asset Inventory',
      previousStep: 'Data Cleansing',
    },
    faq: [
      {
        question: 'What does validation check for?',
        answer: 'Required fields are populated, data formats are correct, relationships are valid, and business rules are satisfied.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/05_Data_Validation.md'],
  },

  '/discovery/inventory': {
    page_name: 'Asset Inventory',
    route: '/discovery/inventory',
    route_pattern: '/discovery/inventory*',
    flow_type: 'discovery',
    description: 'View and manage your complete asset inventory with filtering and export capabilities.',
    features: [
      'Full asset grid view',
      'Advanced filtering',
      'Column customization',
      'Export to Excel/CSV',
      'Inline editing',
    ],
    actions: [
      'Filter assets',
      'Sort by column',
      'Export inventory',
      'Edit asset details',
      'Proceed to dependencies',
    ],
    help_topics: ['asset inventory', 'asset management', 'filtering', 'export'],
    workflow: {
      phase: 'Asset Inventory',
      step: 5,
      totalSteps: 7,
      nextStep: 'Dependencies',
      previousStep: 'Data Validation',
    },
    faq: [
      {
        question: 'How do I export my inventory?',
        answer: 'Click the "Export" button in the toolbar. Choose Excel or CSV format. You can export all assets or only filtered results.',
      },
      {
        question: 'Can I edit assets directly?',
        answer: 'Yes, click on any cell to edit inline. Changes are saved automatically.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/05_Inventory.md'],
  },

  '/discovery/dependencies': {
    page_name: 'Dependency Analysis',
    route: '/discovery/dependencies',
    route_pattern: '/discovery/dependencies*',
    flow_type: 'discovery',
    description: 'Visualize and analyze application dependencies and relationships.',
    features: [
      'Dependency graph visualization',
      'Impact analysis',
      'Dependency matrix',
      'Export dependency report',
    ],
    actions: [
      'View dependency graph',
      'Analyze impact',
      'Export report',
      'Complete discovery',
    ],
    help_topics: ['dependencies', 'application dependencies', 'impact analysis', 'dependency graph'],
    workflow: {
      phase: 'Dependency Analysis',
      step: 6,
      totalSteps: 7,
      nextStep: 'Complete Discovery',
      previousStep: 'Asset Inventory',
    },
    faq: [
      {
        question: 'How are dependencies detected?',
        answer: 'From your imported data (if included), network discovery scans, and AI-inferred relationships based on naming patterns.',
      },
    ],
    related_docs: ['/docs/e2e-flows/01_Discovery/06_Dependencies.md'],
  },

  // ============================================
  // COLLECTION FLOW PAGES
  // ============================================

  '/collection': {
    page_name: 'Collection Overview',
    route: '/collection',
    route_pattern: '/collection',
    flow_type: 'collection',
    description: 'Collect additional information about applications through questionnaires and forms.',
    features: [
      'Start collection flow',
      'View collection progress',
      'Track questionnaire completion',
      'Manage collection flows',
    ],
    actions: [
      'Create new collection flow',
      'Resume existing flow',
      'View completed collections',
    ],
    help_topics: ['collection flow', 'questionnaires', 'data collection'],
    workflow: {
      phase: 'Overview',
      step: 0,
      totalSteps: 5,
      nextStep: 'Application Selection',
    },
    faq: [
      {
        question: 'What is the Collection phase?',
        answer: 'Collection gathers additional business and technical details about applications that aren\'t in your CMDB, using adaptive questionnaires.',
      },
      {
        question: 'Who fills out the questionnaires?',
        answer: 'Application owners, technical leads, or SMEs who have detailed knowledge of each application.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/00_Collection_Flow_Complete_Guide.md'],
  },

  '/collection/overview': {
    page_name: 'Data Collection',
    route: '/collection/overview',
    route_pattern: '/collection/overview',
    flow_type: 'collection',
    description: 'Overview of data collection activities. Collect additional application details through questionnaires and forms.',
    features: [
      'Collection flow dashboard',
      'View collection progress',
      'Track questionnaire completion',
      'Manage collection flows',
      'Start new collection',
    ],
    actions: [
      'Create new collection flow',
      'Resume existing flow',
      'View completed collections',
      'Export collection data',
    ],
    help_topics: ['collection flow', 'questionnaires', 'data collection', 'adaptive forms'],
    workflow: {
      phase: 'Overview',
      step: 0,
      totalSteps: 5,
      nextStep: 'Application Selection',
    },
    faq: [
      {
        question: 'What is the Collection phase?',
        answer: 'Collection gathers additional business and technical details about applications that aren\'t in your CMDB, using adaptive questionnaires.',
      },
      {
        question: 'How do I start a collection?',
        answer: 'Click "New Collection" to select applications from your inventory that need additional data collection.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/00_Collection_Flow_Complete_Guide.md'],
  },

  '/collection/adaptive-forms': {
    page_name: 'Adaptive Forms',
    route: '/collection/adaptive-forms',
    route_pattern: '/collection/adaptive-forms*',
    flow_type: 'collection',
    description: 'Fill out intelligent questionnaires that adapt based on your answers.',
    features: [
      'Adaptive question flow',
      'Progress tracking',
      'Save and resume',
      'AI-powered suggestions',
      'Section-by-section completion',
    ],
    actions: [
      'Answer questions',
      'Save progress',
      'Skip optional sections',
      'Submit questionnaire',
    ],
    help_topics: ['adaptive forms', 'questionnaires', 'application details'],
    workflow: {
      phase: 'Adaptive Forms',
      step: 2,
      totalSteps: 5,
      nextStep: 'Gap Analysis',
      previousStep: 'Application Selection',
    },
    faq: [
      {
        question: 'Why do questions change based on my answers?',
        answer: 'The system shows only relevant follow-up questions to save time and collect the most pertinent information.',
      },
      {
        question: 'Can I save and come back later?',
        answer: 'Yes, your progress is automatically saved. Click "Save & Exit" to return later.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/02_Adaptive_Forms.md'],
  },

  '/collection/select-applications': {
    page_name: 'Application Selection',
    route: '/collection/select-applications',
    route_pattern: '/collection/select-applications',
    flow_type: 'collection',
    description: 'Select which applications need additional information collection.',
    features: [
      'Application list from inventory',
      'Bulk selection',
      'Filter by criteria',
      'Data completeness indicator',
    ],
    actions: [
      'Select applications',
      'View current data',
      'Start collection',
    ],
    help_topics: ['application selection', 'collection scope'],
    workflow: {
      phase: 'Application Selection',
      step: 1,
      totalSteps: 5,
      nextStep: 'Adaptive Forms',
      previousStep: 'Overview',
    },
    faq: [
      {
        question: 'How do I know which apps need collection?',
        answer: 'Look for the data completeness indicator - applications with gaps in critical fields should be prioritized.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/01_Overview_Page.md'],
  },

  '/collection/bulk-upload': {
    page_name: 'Bulk Upload',
    route: '/collection/bulk-upload',
    route_pattern: '/collection/bulk-upload',
    flow_type: 'collection',
    description: 'Upload collection data in bulk using spreadsheet templates.',
    features: [
      'Download template',
      'Bulk data upload',
      'Validation report',
      'Error handling',
    ],
    actions: [
      'Download template',
      'Upload filled template',
      'Review validation',
      'Submit data',
    ],
    help_topics: ['bulk upload', 'templates', 'mass data entry'],
    workflow: {
      phase: 'Bulk Upload',
      step: 3,
      totalSteps: 5,
      nextStep: 'Review',
      previousStep: 'Adaptive Forms',
    },
    faq: [
      {
        question: 'What format should the bulk upload be in?',
        answer: 'Download our Excel template first - it contains all required fields with validation and instructions.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/03_Bulk_Upload.md'],
  },

  '/collection/progress': {
    page_name: 'Collection Progress',
    route: '/collection/progress',
    route_pattern: '/collection/progress*',
    flow_type: 'collection',
    description: 'Track progress of all collection activities across applications.',
    features: [
      'Progress dashboard',
      'Completion metrics',
      'Outstanding items',
      'Reminder notifications',
    ],
    actions: [
      'View progress',
      'Send reminders',
      'Review completed',
      'Export status report',
    ],
    help_topics: ['progress tracking', 'collection status'],
    faq: [
      {
        question: 'How do I see who hasn\'t completed their questionnaires?',
        answer: 'Filter by "Incomplete" status to see pending items and their assigned owners.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/01_Overview_Page.md'],
  },

  '/collection/data-integration': {
    page_name: 'Data Integration',
    route: '/collection/data-integration',
    route_pattern: '/collection/data-integration',
    flow_type: 'collection',
    description: 'Configure and manage data integrations for automated data collection from external systems.',
    features: [
      'Configure integrations',
      'Connect to external systems',
      'Automated data sync',
      'Integration health monitoring',
    ],
    actions: [
      'Add new integration',
      'Configure connection settings',
      'Test integration',
      'View sync status',
    ],
    help_topics: ['data integration', 'automated collection', 'external systems', 'API connections'],
    faq: [
      {
        question: 'What data sources can I integrate?',
        answer: 'You can integrate with various CMDBs, cloud providers, and enterprise tools to automatically collect infrastructure data.',
      },
      {
        question: 'How do I test an integration?',
        answer: 'Use the "Test Connection" button to verify the integration settings before enabling automated sync.',
      },
    ],
    related_docs: ['/docs/e2e-flows/02_Collection/01_Overview_Page.md'],
  },

  // ============================================
  // ASSESSMENT FLOW PAGES
  // ============================================

  '/assessment': {
    page_name: 'Assessment Overview',
    route: '/assessment',
    route_pattern: '/assessment',
    flow_type: 'assessment',
    description: 'Run AI-powered assessments to determine migration readiness and 6R recommendations.',
    features: [
      'Start assessment flow',
      'View assessment results',
      'Track assessment progress',
      '6R strategy overview',
    ],
    actions: [
      'Create new assessment',
      'View existing assessments',
      'Export assessment report',
    ],
    help_topics: ['assessment flow', '6R strategy', 'migration readiness'],
    workflow: {
      phase: 'Overview',
      step: 0,
      totalSteps: 8,
      nextStep: 'Architecture Standards',
    },
    faq: [
      {
        question: 'What is the 6R strategy?',
        answer: 'The 6Rs are: Rehost (lift-and-shift), Replatform (lift-tinker-and-shift), Refactor, Rearchitect, Rebuild, and Retire. Each app gets a recommendation.',
      },
      {
        question: 'How long does assessment take?',
        answer: 'AI assessment runs in 2-5 minutes per application. You can review and adjust results afterward.',
      },
    ],
    related_docs: ['/docs/e2e-flows/03_Assess/00_Assessment_Flow_Complete_Guide.md'],
  },

  '/assessment/overview': {
    page_name: 'Assessment Flow Overview',
    route: '/assessment/overview',
    route_pattern: '/assessment/overview',
    flow_type: 'assessment',
    description: 'Dashboard showing all assessment flows and their status.',
    features: [
      'Assessment flow list',
      'Status tracking',
      'Quick actions',
      'Summary metrics',
    ],
    actions: [
      'Start new assessment',
      'Continue existing',
      'View results',
      'Export reports',
    ],
    help_topics: ['assessment management', 'flow status'],
    related_docs: ['/docs/e2e-flows/03_Assess/01_Overview.md'],
  },

  '/assessment/initialize': {
    page_name: 'Initialize Assessment',
    route: '/assessment/initialize',
    route_pattern: '/assessment/initialize',
    flow_type: 'assessment',
    description: 'Select applications and configure the assessment flow.',
    features: [
      'Application selection',
      'Assessment configuration',
      'Scope definition',
      'Phase selection',
    ],
    actions: [
      'Select apps to assess',
      'Configure phases',
      'Start assessment',
    ],
    help_topics: ['assessment setup', 'scope selection'],
    workflow: {
      phase: 'Initialize',
      step: 1,
      totalSteps: 8,
      nextStep: 'Architecture Standards',
      previousStep: 'Overview',
    },
    faq: [
      {
        question: 'Which applications should I assess?',
        answer: 'Start with business-critical applications or those with upcoming renewal deadlines. You can always add more later.',
      },
    ],
    related_docs: ['/docs/e2e-flows/03_Assess/06_Assessment_Flow.md'],
  },

  // Aliases for /assess/* routes (actual URLs used by the application)
  '/assess': {
    page_name: 'Assessment Flows',
    route: '/assess',
    route_pattern: '/assess',
    flow_type: 'assessment',
    description: 'Start AI-powered assessment when data readiness is confirmed. Analyze applications for cloud migration readiness and get 6R recommendations.',
    features: [
      'Assessment flow management',
      'Application selection',
      '6R recommendation engine',
      'Risk assessment',
      'Migration readiness scoring',
    ],
    actions: [
      'Start new assessment',
      'Continue existing assessment',
      'View assessment results',
      'Export recommendations',
    ],
    help_topics: ['assessment', '6R strategy', 'migration readiness', 'risk analysis'],
    related_docs: ['/docs/e2e-flows/03_Assess/01_Overview.md'],
  },

  '/assess/overview': {
    page_name: 'Assessment Flows',
    route: '/assess/overview',
    route_pattern: '/assess/overview',
    flow_type: 'assessment',
    description: 'Dashboard showing all assessment flows and their status. Start AI-powered assessments when data readiness is confirmed.',
    features: [
      'Assessment flow list',
      'Status tracking',
      'Quick actions',
      'Summary metrics',
      'Application readiness',
      'Critical issues overview',
    ],
    actions: [
      'Start new assessment',
      'Continue existing assessment',
      'View results',
      'Export reports',
      'Filter by status',
    ],
    help_topics: ['assessment management', 'flow status', '6R strategy'],
    faq: [
      {
        question: 'What is a 6R assessment?',
        answer: 'The 6R framework evaluates each application for: Rehost (lift-and-shift), Replatform (lift-tinker-shift), Refactor (re-architect), Rearchitect (redesign), Rebuild (rewrite), or Retire (decommission).',
      },
      {
        question: 'When can I start an assessment?',
        answer: 'Assessments can begin once your data is ready (imported, mapped, and validated in Discovery). Click "New Assessment" or "From Collection" to start.',
      },
    ],
    related_docs: ['/docs/e2e-flows/03_Assess/01_Overview.md'],
  },

  '/assess/treatment': {
    page_name: 'Assessment Treatment',
    route: '/assess/treatment',
    route_pattern: '/assess/treatment',
    flow_type: 'assessment',
    description: 'Review and apply 6R recommendations to applications. Accept, modify, or override AI-generated migration strategies.',
    features: [
      '6R recommendation review',
      'Application treatment grid',
      'Strategy override',
      'Bulk treatment updates',
      'Risk assessment details',
      'Migration complexity scores',
    ],
    actions: [
      'Accept 6R recommendation',
      'Override strategy',
      'Apply bulk changes',
      'Export treatment plan',
      'View risk details',
    ],
    help_topics: ['6R treatment', 'migration strategy', 'application assessment', 'risk analysis'],
    workflow: {
      phase: '6R Treatment',
      step: 6,
      totalSteps: 8,
      nextStep: 'Export',
      previousStep: '6R Decision',
    },
    faq: [
      {
        question: 'What is treatment in assessment?',
        answer: 'Treatment is where you review AI-generated 6R recommendations and decide the migration strategy for each application - accepting, modifying, or overriding the suggestions.',
      },
      {
        question: 'Can I change the AI recommendation?',
        answer: 'Yes, you can override any 6R recommendation. Select the application and choose a different strategy from the dropdown. Document the reason for audit purposes.',
      },
      {
        question: 'What factors influence 6R recommendations?',
        answer: 'The AI considers application complexity, dependencies, technical debt, business criticality, and cloud readiness when suggesting Rehost, Replatform, Refactor, Rearchitect, Rebuild, or Retire.',
      },
    ],
    related_docs: ['/docs/e2e-flows/03_Assess/05_Treatment.md'],
    tips: [
      'Review high-risk applications first',
      'Consider business impact when overriding recommendations',
      'Document override reasons for compliance',
    ],
  },

  '/assess/editor': {
    page_name: 'Assessment Editor',
    route: '/assess/editor',
    route_pattern: '/assess/editor',
    flow_type: 'assessment',
    description: 'Edit and customize assessment parameters, criteria, and scoring models.',
    features: [
      'Assessment criteria editor',
      'Scoring model configuration',
      'Custom rule creation',
      'Weight adjustment',
    ],
    actions: [
      'Edit assessment criteria',
      'Adjust scoring weights',
      'Create custom rules',
      'Save configuration',
    ],
    help_topics: ['assessment editor', 'scoring configuration', 'custom criteria'],
    faq: [
      {
        question: 'Can I customize the assessment criteria?',
        answer: 'Yes, you can modify scoring weights, add custom criteria, and adjust how the AI evaluates applications for migration.',
      },
    ],
  },

  '/assess/roadmap': {
    page_name: 'Assessment Roadmap',
    route: '/assess/roadmap',
    route_pattern: '/assess/roadmap',
    flow_type: 'assessment',
    description: 'View the migration roadmap generated from assessment results with timeline and dependencies.',
    features: [
      'Migration roadmap visualization',
      'Timeline view',
      'Dependency mapping',
      'Phase planning',
    ],
    actions: [
      'View roadmap',
      'Adjust timeline',
      'Export roadmap',
      'Proceed to planning',
    ],
    help_topics: ['migration roadmap', 'timeline', 'phase planning'],
    faq: [
      {
        question: 'How is the roadmap generated?',
        answer: 'The roadmap is created based on 6R recommendations, application dependencies, risk levels, and business priorities from the assessment.',
      },
    ],
  },

  '/assess/migration-readiness': {
    page_name: 'Migration Readiness',
    route: '/assess/migration-readiness',
    route_pattern: '/assess/migration-readiness*',
    flow_type: 'assessment',
    description: 'Evaluate application readiness for cloud migration with detailed scoring and gap analysis.',
    features: [
      'Readiness scoring',
      'Gap analysis',
      'Blocker identification',
      'Remediation recommendations',
    ],
    actions: [
      'View readiness scores',
      'Analyze gaps',
      'Address blockers',
      'Export readiness report',
    ],
    help_topics: ['migration readiness', 'cloud readiness', 'gap analysis'],
    faq: [
      {
        question: 'What does the readiness score measure?',
        answer: 'The readiness score evaluates technical compatibility, dependency complexity, data migration requirements, and operational considerations for cloud migration.',
      },
    ],
  },

  '/assess/tech-debt': {
    page_name: 'Technical Debt Analysis',
    route: '/assess/tech-debt',
    route_pattern: '/assess/tech-debt*',
    flow_type: 'assessment',
    description: 'Analyze technical debt in applications to inform migration strategy decisions.',
    features: [
      'Technical debt scoring',
      'Code quality metrics',
      'Modernization recommendations',
      'Effort estimation',
    ],
    actions: [
      'View tech debt analysis',
      'Review recommendations',
      'Estimate remediation effort',
      'Export tech debt report',
    ],
    help_topics: ['technical debt', 'code quality', 'modernization'],
    faq: [
      {
        question: 'How does technical debt affect migration?',
        answer: 'High technical debt may indicate the need for refactoring or rearchitecting rather than simple rehosting, affecting time and cost estimates.',
      },
    ],
  },

  '/assess/summary': {
    page_name: 'Assessment Summary',
    route: '/assess/summary',
    route_pattern: '/assess/summary*',
    flow_type: 'assessment',
    description: 'View comprehensive summary of assessment results across all applications.',
    features: [
      'Executive summary',
      '6R distribution charts',
      'Risk overview',
      'Export capabilities',
    ],
    actions: [
      'View summary',
      'Export executive report',
      'Share with stakeholders',
      'Proceed to planning',
    ],
    help_topics: ['assessment summary', 'executive report', '6R results'],
    faq: [
      {
        question: 'What does the summary include?',
        answer: 'The summary shows 6R recommendations distribution, overall risk levels, estimated effort, and key findings from the assessment.',
      },
    ],
  },

  // ============================================
  // PLAN FLOW PAGES
  // ============================================

  '/plan': {
    page_name: 'Planning Overview',
    route: '/plan',
    route_pattern: '/plan',
    flow_type: 'planning',
    description: 'Create migration plans including wave planning, timelines, and resource allocation.',
    features: [
      'Wave planning',
      'Timeline generation',
      'Resource allocation',
      'Export plans',
    ],
    actions: [
      'Create wave plan',
      'Adjust timelines',
      'Allocate resources',
      'Export migration plan',
    ],
    help_topics: ['wave planning', 'migration timeline', 'resource planning'],
    faq: [
      {
        question: 'What is wave planning?',
        answer: 'Wave planning groups applications into migration waves based on dependencies, risk, and resource availability.',
      },
    ],
    related_docs: ['/docs/e2e-flows/04_Plan/00_Planning_Flow_Complete_Guide.md'],
  },

  '/plan/waveplanning': {
    page_name: 'Wave Planning',
    route: '/plan/waveplanning',
    route_pattern: '/plan/waveplanning',
    flow_type: 'planning',
    description: 'Organize applications into migration waves with dependency-aware grouping.',
    features: [
      'Drag-and-drop wave assignment',
      'Dependency visualization',
      'Conflict detection',
      'Wave timeline view',
    ],
    actions: [
      'Create waves',
      'Assign applications',
      'Validate dependencies',
      'Optimize wave order',
    ],
    help_topics: ['wave planning', 'migration waves', 'dependencies'],
    workflow: {
      phase: 'Wave Planning',
      step: 1,
      totalSteps: 4,
      nextStep: 'Timeline',
      previousStep: 'Overview',
    },
    faq: [
      {
        question: 'How do I create a new wave?',
        answer: 'Click "Add Wave" and set the name, target date, and description. Then drag applications into the wave.',
      },
      {
        question: 'What if I have dependency conflicts?',
        answer: 'The system highlights conflicts when a dependency would run in a later wave. Move the dependency to an earlier wave.',
      },
    ],
    related_docs: ['/docs/e2e-flows/03_Assess/03_Wave_Planning.md'],
  },

  '/plan/timeline': {
    page_name: 'Migration Timeline',
    route: '/plan/timeline',
    route_pattern: '/plan/timeline',
    flow_type: 'planning',
    description: 'View and adjust the overall migration timeline with Gantt chart visualization.',
    features: [
      'Gantt chart view',
      'Milestone tracking',
      'Date adjustments',
      'Critical path highlighting',
    ],
    actions: [
      'Adjust dates',
      'Add milestones',
      'View critical path',
      'Export timeline',
    ],
    help_topics: ['timeline', 'Gantt chart', 'milestones'],
    workflow: {
      phase: 'Timeline',
      step: 2,
      totalSteps: 4,
      nextStep: 'Resources',
      previousStep: 'Wave Planning',
    },
    related_docs: ['/docs/e2e-flows/04_Plan/02_Timeline.md'],
  },

  '/plan/resource': {
    page_name: 'Resource Allocation',
    route: '/plan/resource',
    route_pattern: '/plan/resource',
    flow_type: 'planning',
    description: 'Plan and allocate resources for migration activities.',
    features: [
      'Resource capacity planning',
      'Skill matching',
      'Utilization forecasting',
      'Resource conflicts',
    ],
    actions: [
      'Assign resources',
      'Balance workload',
      'Identify gaps',
      'Export resource plan',
    ],
    help_topics: ['resource planning', 'capacity planning', 'team allocation'],
    workflow: {
      phase: 'Resources',
      step: 3,
      totalSteps: 4,
      nextStep: 'Target',
      previousStep: 'Timeline',
    },
    related_docs: ['/docs/e2e-flows/04_Plan/03_Resource.md'],
  },

  '/plan/target': {
    page_name: 'Target Environment',
    route: '/plan/target',
    route_pattern: '/plan/target',
    flow_type: 'planning',
    description: 'Define and configure target cloud environments for migration.',
    features: [
      'Cloud provider selection',
      'Environment configuration',
      'Cost estimation',
      'Architecture templates',
    ],
    actions: [
      'Select cloud provider',
      'Configure target',
      'Estimate costs',
      'Apply templates',
    ],
    help_topics: ['target environment', 'cloud configuration', 'cost estimation'],
    workflow: {
      phase: 'Target',
      step: 4,
      totalSteps: 4,
      previousStep: 'Resources',
    },
    related_docs: ['/docs/e2e-flows/04_Plan/04_Target.md'],
  },

  // ============================================
  // DECOMMISSION FLOW PAGES
  // ============================================

  '/decommission': {
    page_name: 'Decommission Overview',
    route: '/decommission',
    route_pattern: '/decommission',
    flow_type: 'decommission',
    description: 'Manage the decommissioning of legacy systems after migration.',
    features: [
      'Decommission planning',
      'Data migration tracking',
      'System shutdown checklist',
      'Compliance verification',
    ],
    actions: [
      'Create decommission plan',
      'Track data migration',
      'Schedule shutdown',
      'Export reports',
    ],
    help_topics: ['decommission', 'legacy system', 'data retention'],
    faq: [
      {
        question: 'When should I decommission?',
        answer: 'After successful migration validation, when the new system is stable and all data has been migrated and verified.',
      },
    ],
    related_docs: ['/docs/e2e-flows/05_Decommission/00_Decommission_Flow_Complete_Guide.md'],
  },

  '/decommission/planning': {
    page_name: 'Decommission Planning',
    route: '/decommission/planning',
    route_pattern: '/decommission/planning',
    flow_type: 'decommission',
    description: 'Plan the decommissioning process including dependencies and compliance.',
    features: [
      'Dependency analysis',
      'Compliance checklist',
      'Stakeholder approval',
      'Risk assessment',
    ],
    actions: [
      'Review dependencies',
      'Complete checklist',
      'Get approvals',
      'Schedule decommission',
    ],
    help_topics: ['decommission planning', 'compliance', 'approvals'],
    workflow: {
      phase: 'Planning',
      step: 1,
      totalSteps: 4,
      nextStep: 'Data Migration',
      previousStep: 'Overview',
    },
    related_docs: ['/docs/e2e-flows/05_Decommission/02_Decommission_Planning.md'],
  },

  '/decommission/data-migration': {
    page_name: 'Data Migration',
    route: '/decommission/data-migration',
    route_pattern: '/decommission/data-migration',
    flow_type: 'decommission',
    description: 'Track data migration from legacy systems before decommissioning.',
    features: [
      'Data inventory',
      'Migration status',
      'Validation reports',
      'Archival tracking',
    ],
    actions: [
      'Track migration',
      'Validate data',
      'Archive records',
      'Generate report',
    ],
    help_topics: ['data migration', 'data validation', 'archival'],
    workflow: {
      phase: 'Data Migration',
      step: 2,
      totalSteps: 4,
      nextStep: 'System Shutdown',
      previousStep: 'Planning',
    },
    related_docs: ['/docs/e2e-flows/05_Decommission/03_Data_Migration.md'],
  },

  '/decommission/shutdown': {
    page_name: 'System Shutdown',
    route: '/decommission/shutdown',
    route_pattern: '/decommission/shutdown',
    flow_type: 'decommission',
    description: 'Execute and track system shutdown activities.',
    features: [
      'Shutdown checklist',
      'Service disconnection',
      'Verification steps',
      'Rollback procedures',
    ],
    actions: [
      'Execute checklist',
      'Disconnect services',
      'Verify shutdown',
      'Document completion',
    ],
    help_topics: ['system shutdown', 'service disconnection'],
    workflow: {
      phase: 'System Shutdown',
      step: 3,
      totalSteps: 4,
      nextStep: 'Export',
      previousStep: 'Data Migration',
    },
    related_docs: ['/docs/e2e-flows/05_Decommission/04_System_Shutdown.md'],
  },

  // ============================================
  // FINOPS PAGES
  // ============================================

  '/finops': {
    page_name: 'FinOps Overview',
    route: '/finops',
    route_pattern: '/finops',
    flow_type: 'finops',
    description: 'Financial operations and cloud cost management dashboard.',
    features: [
      'Cost overview',
      'Cloud comparison',
      'Savings analysis',
      'Budget tracking',
    ],
    actions: [
      'View costs',
      'Compare providers',
      'Analyze savings',
      'Set budgets',
    ],
    help_topics: ['FinOps', 'cloud costs', 'cost optimization'],
    faq: [
      {
        question: 'What is FinOps?',
        answer: 'FinOps (Financial Operations) is the practice of bringing financial accountability to the variable spending model of cloud.',
      },
    ],
  },

  '/finops/cloud-comparison': {
    page_name: 'Cloud Comparison',
    route: '/finops/cloud-comparison',
    route_pattern: '/finops/cloud-comparison',
    flow_type: 'finops',
    description: 'Compare costs across different cloud providers.',
    features: [
      'Multi-cloud comparison',
      'Price calculator',
      'Feature comparison',
      'TCO analysis',
    ],
    actions: [
      'Compare providers',
      'Calculate costs',
      'Export comparison',
    ],
    help_topics: ['cloud comparison', 'AWS vs Azure vs GCP'],
  },

  '/finops/llm-costs': {
    page_name: 'LLM Costs',
    route: '/finops/llm-costs',
    route_pattern: '/finops/llm-costs',
    flow_type: 'finops',
    description: 'Track and analyze AI/LLM usage costs across the platform.',
    features: [
      'Token usage tracking',
      'Cost breakdown by model',
      'Usage trends',
      'Cost optimization tips',
    ],
    actions: [
      'View LLM costs',
      'Analyze usage',
      'Export reports',
    ],
    help_topics: ['LLM costs', 'AI costs', 'token usage'],
    faq: [
      {
        question: 'What LLM models are used?',
        answer: 'We use Gemma 3 4B for chat interactions and Llama 4 Maverick for agentic tasks like analysis and assessment.',
      },
    ],
  },

  // ============================================
  // OBSERVABILITY PAGES
  // ============================================

  '/observability': {
    page_name: 'Observability Dashboard',
    route: '/observability',
    route_pattern: '/observability',
    flow_type: 'observability',
    description: 'Monitor AI agents, workflows, and system health.',
    features: [
      'Agent monitoring',
      'Workflow tracking',
      'Performance metrics',
      'Health status',
    ],
    actions: [
      'View agents',
      'Check workflows',
      'Analyze metrics',
      'Review health',
    ],
    help_topics: ['observability', 'monitoring', 'agents'],
  },

  '/observability/enhanced': {
    page_name: 'Enhanced Observability',
    route: '/observability/enhanced',
    route_pattern: '/observability/enhanced',
    flow_type: 'observability',
    description: 'Advanced observability dashboard with detailed metrics and visualizations.',
    features: [
      'Detailed metrics',
      'Custom dashboards',
      'Alerting',
      'Historical data',
    ],
    actions: [
      'Create dashboard',
      'Set alerts',
      'Export data',
    ],
    help_topics: ['metrics', 'dashboards', 'alerting'],
  },

  // ============================================
  // ADMIN PAGES
  // ============================================

  '/admin': {
    page_name: 'Admin Dashboard',
    route: '/admin',
    route_pattern: '/admin',
    flow_type: 'admin',
    description: 'Platform administration dashboard for managing clients, users, and engagements.',
    features: [
      'Client management',
      'User management',
      'Engagement tracking',
      'Platform settings',
    ],
    actions: [
      'Manage clients',
      'Manage users',
      'Create engagements',
      'Configure platform',
    ],
    help_topics: ['admin', 'platform management'],
    faq: [
      {
        question: 'Who can access admin features?',
        answer: 'Only users with Admin or Platform Admin roles can access the admin dashboard.',
      },
    ],
  },

  '/admin/clients': {
    page_name: 'Client Management',
    route: '/admin/clients',
    route_pattern: '/admin/clients*',
    flow_type: 'admin',
    description: 'Manage client accounts and their settings.',
    features: [
      'Client list',
      'Create client',
      'Edit details',
      'View engagements',
    ],
    actions: [
      'Add client',
      'Edit client',
      'View client details',
      'Manage engagements',
    ],
    help_topics: ['client management', 'accounts'],
  },

  '/admin/engagements': {
    page_name: 'Engagement Management',
    route: '/admin/engagements',
    route_pattern: '/admin/engagements*',
    flow_type: 'admin',
    description: 'Manage migration engagements for clients.',
    features: [
      'Engagement list',
      'Create engagement',
      'Track progress',
      'Manage team',
    ],
    actions: [
      'Create engagement',
      'Edit engagement',
      'Assign team',
      'Track status',
    ],
    help_topics: ['engagement management', 'projects'],
  },

  '/admin/users': {
    page_name: 'User Management',
    route: '/admin/users',
    route_pattern: '/admin/users*',
    flow_type: 'admin',
    description: 'Manage platform users, roles, and permissions.',
    features: [
      'User list',
      'Role assignment',
      'Permission management',
      'User approvals',
    ],
    actions: [
      'Add user',
      'Edit permissions',
      'Approve access',
      'Deactivate user',
    ],
    help_topics: ['user management', 'roles', 'permissions'],
  },

  // ============================================
  // GENERAL / HOME PAGES
  // ============================================

  '/': {
    page_name: 'Home',
    route: '/',
    route_pattern: '/',
    flow_type: 'general',
    description: 'Welcome to the AI Stock Assess platform - your intelligent stock analysis assistant.',
    features: [
      'Quick navigation',
      'Recent activity',
      'Getting started guide',
      'Platform overview',
    ],
    actions: [
      'Start discovery',
      'Continue flow',
      'View dashboard',
    ],
    help_topics: ['getting started', 'navigation', 'overview'],
    faq: [
      {
        question: 'Where do I start?',
        answer: 'Begin with Discovery to import your CMDB data, then proceed through Collection, Assessment, and Planning phases.',
      },
      {
        question: 'What are the main phases?',
        answer: 'Discovery (import & analyze), Collection (gather details), Assessment (6R recommendations), Planning (wave planning), Execute (migration), Decommission (retire legacy).',
      },
    ],
  },

  '/profile': {
    page_name: 'User Profile',
    route: '/profile',
    route_pattern: '/profile',
    flow_type: 'general',
    description: 'Manage your user profile and preferences.',
    features: [
      'Profile settings',
      'Notification preferences',
      'Security settings',
      'Activity log',
    ],
    actions: [
      'Edit profile',
      'Change password',
      'Update preferences',
    ],
    help_topics: ['profile', 'settings', 'preferences'],
  },
};

/**
 * Get page context by route
 * Supports both exact matches and pattern matching for dynamic routes
 */
// Route aliases to handle URL mismatches (actual URL → registry route)
const ROUTE_ALIASES: Record<string, string> = {
  // Discovery aliases
  '/discovery/cmdb-import': '/discovery/data-import',  // Keep for backwards compatibility
  // Assessment aliases
  '/assess': '/assessment',
  '/assess/overview': '/assessment/overview',
  '/assess/initialize': '/assessment/initialize',
};

/**
 * Normalize a route by applying common transformations
 */
function normalizeRoute(route: string): string[] {
  const variants: string[] = [route];

  // Try aliased route
  if (ROUTE_ALIASES[route]) {
    variants.push(ROUTE_ALIASES[route]);
  }

  // Handle /assess → /assessment transformation
  if (route.startsWith('/assess/')) {
    variants.push(route.replace('/assess/', '/assessment/'));
  }

  // Handle /assessment → /assess transformation
  if (route.startsWith('/assessment/')) {
    variants.push(route.replace('/assessment/', '/assess/'));
  }

  // Strip trailing UUID for flow-specific pages
  const uuidPattern = /\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (uuidPattern.test(route)) {
    const baseRoute = route.replace(uuidPattern, '');
    variants.push(baseRoute);
  }

  return variants;
}

export function getPageContext(route: string): PageContext | null {
  // Try exact match first
  if (PAGE_CONTEXT_REGISTRY[route]) {
    return PAGE_CONTEXT_REGISTRY[route];
  }

  // Try route variants (aliases, normalizations)
  const variants = normalizeRoute(route);
  for (const variant of variants) {
    if (variant !== route && PAGE_CONTEXT_REGISTRY[variant]) {
      return PAGE_CONTEXT_REGISTRY[variant];
    }
  }

  // Try pattern matching for dynamic routes
  for (const [registryRoute, context] of Object.entries(PAGE_CONTEXT_REGISTRY)) {
    const pattern = context.route_pattern;

    // Convert route pattern to regex
    const regexPattern = pattern
      .replace(/\*/g, '[^/]*') // * matches anything except /
      .replace(/\//g, '\\/');  // Escape forward slashes

    const regex = new RegExp(`^${regexPattern}$`);

    // Test against route and all variants
    for (const variant of variants) {
      if (regex.test(variant)) {
        return context;
      }
    }
  }

  // Return a generic context for unknown pages
  return {
    page_name: 'Unknown Page',
    route: route,
    route_pattern: route,
    flow_type: 'general',
    description: 'This page is part of the AI Stock Assess platform.',
    features: [],
    actions: [],
    help_topics: ['migration', 'platform'],
    faq: [],
  };
}

/**
 * Get all pages for a specific flow type
 */
export function getPagesByFlowType(flowType: FlowType): PageContext[] {
  return Object.values(PAGE_CONTEXT_REGISTRY).filter(
    (context) => context.flow_type === flowType
  );
}

/**
 * Get suggested help topics based on current page
 */
export function getSuggestedHelpTopics(route: string): string[] {
  const context = getPageContext(route);
  if (!context) return [];

  return [...context.help_topics, ...context.features.slice(0, 3)];
}

/**
 * Get workflow navigation info
 */
export function getWorkflowNavigation(route: string): {
  current: PageContext | null;
  next: PageContext | null;
  previous: PageContext | null;
} {
  const current = getPageContext(route);
  if (!current || !current.workflow) {
    return { current, next: null, previous: null };
  }

  const flowPages = getPagesByFlowType(current.flow_type);

  const next = current.workflow.nextStep
    ? flowPages.find((p) => p.page_name === current.workflow?.nextStep) || null
    : null;

  const previous = current.workflow.previousStep
    ? flowPages.find((p) => p.page_name === current.workflow?.previousStep) || null
    : null;

  return { current, next, previous };
}

export default PAGE_CONTEXT_REGISTRY;
