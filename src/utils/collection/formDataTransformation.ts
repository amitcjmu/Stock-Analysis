/**
 * Form Data Transformation Utilities
 *
 * Utilities for converting between different data formats in collection workflows.
 * Extracted from AdaptiveForms.tsx for reusability across collection components.
 */

import type { AdaptiveFormData, FormSection, FormField, FieldOption } from '@/components/collection/types';
import type { ConfigurationValue, ConfigurationObject } from '@/types/shared/config-types';
import type { AdaptiveQuestionnaireResponse } from '@/services/api/collection-flow';

export interface QuestionnaireData {
  id?: string;
  questions?: QuestionData[];
  estimated_completion_time?: number;
  confidence_impact_score?: number;
}

export interface QuestionData {
  field_id?: string;
  question_text?: string;
  label?: string;
  input_type?: string;  // Backend SectionQuestionGenerator sends this
  field_type?: string;
  question_type?: string;
  type?: string;  // Alternative field name
  category?: string;
  critical_attribute?: string;
  required?: boolean;
  validation?: ConfigurationObject;
  business_impact_score?: number;
  options?: FieldOption[] | string[]; // can be FieldOption[] or string[] from backend
  help_text?: string;
  description?: string;
  metadata?: Record<string, unknown>;  // For asset_id and other metadata
  question?: string;  // Alternative to question_text
  placeholder?: string;  // Placeholder text for inputs
  multiple?: boolean;  // For multiselect fields
}

/**
 * Maps CrewAI question types to form field types
 */
export const mapQuestionTypeToFieldType = (questionType: string): string => {
  const mappings: Record<string, string> = {
    // Core types
    'text': 'text',
    'textarea': 'textarea',
    'select': 'select',
    'multiselect': 'multiselect',
    'checkbox': 'checkbox',
    'radio': 'radio',
    'number': 'number',
    'email': 'email',
    'url': 'url',
    'date': 'date',
    'file': 'file',
    // Asset-aware collection types
    'asset_selector': 'asset_selector',
    // Backend generator CrewAI types
    'single_select': 'select',
    'multi_select': 'multiselect',
    'boolean': 'checkbox',
    // Domain-specific shortcuts
    'application_name': 'text',
    'application_type': 'select',
    'technology_stack': 'multiselect',
    'database': 'select'
  };
  return mappings[questionType] || 'text';
};

/**
 * Gets default options for certain field types
 */
export const getDefaultFieldOptions = (fieldType: string): FieldOption[] => {
  const defaultOptions: Record<string, FieldOption[]> = {
    'application_type': [
      { value: 'web', label: 'Web Application' },
      { value: 'desktop', label: 'Desktop Application' },
      { value: 'mobile', label: 'Mobile Application' },
      { value: 'service', label: 'Web Service/API' },
      { value: 'batch', label: 'Batch Processing' }
    ],
    'database': [
      { value: 'mysql', label: 'MySQL' },
      { value: 'postgresql', label: 'PostgreSQL' },
      { value: 'oracle', label: 'Oracle' },
      { value: 'sqlserver', label: 'SQL Server' },
      { value: 'mongodb', label: 'MongoDB' }
    ]
  };
  return defaultOptions[fieldType] || [];
};

/**
 * Converts a question from CrewAI format to FormField format
 */
export const convertQuestionToFormField = (
  question: QuestionData,
  index: number,
  sectionId: string
): FormField => {
  const toTitle = (s: string): string => s
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());

  const normalizeOptions = (opts: FieldOption[] | string[] | undefined): FieldOption[] | undefined => {
    if (!opts) return undefined;
    if (opts.length === 0) return [];
    if (typeof opts[0] === 'string') {
      // Keep the original value as-is from the backend
      return (opts as string[]).map(v => ({ value: v, label: toTitle(String(v)) }));
    }
    return opts as FieldOption[];
  };

  // Determine a domain key to fetch defaults (e.g., 'application_type', 'database')
  const defaultKey = ((): string | undefined => {
    if (question.field_id && getDefaultFieldOptions(question.field_id).length > 0) return question.field_id;
    if (question.critical_attribute && getDefaultFieldOptions(question.critical_attribute).length > 0) return question.critical_attribute;
    if (question.field_type && getDefaultFieldOptions(question.field_type).length > 0) return question.field_type;
    return undefined;
  })();

  // CRITICAL: Generate unique field ID for multi-asset questions
  // If question has asset_id in metadata, prepend it to make the ID unique
  const assetId = question.metadata?.asset_id;
  const baseFieldId = question.field_id || `question_${index + 1}`;
  const fieldId = assetId ? `${assetId}__${baseFieldId}` : baseFieldId;

  const fieldOptions = normalizeOptions(question.options) || (defaultKey ? getDefaultFieldOptions(defaultKey) : undefined);

  // Ensure multiselect questions have proper field type mapping
  // CRITICAL FIX: Backend sends 'input_type' (from SectionQuestionGenerator), not 'field_type'
  // Must check input_type first to properly render MCQ questions as select/radio instead of text
  const questionType = question.input_type || question.field_type || question.question_type || question.type || 'text';
  const mappedFieldType = mapQuestionTypeToFieldType(questionType);

  // DEBUG: Log field type determination for MCQ debugging
  console.log(`🔍 Field type for "${question.field_id}": input_type=${question.input_type}, field_type=${question.field_type}, questionType=${questionType}, mappedFieldType=${mappedFieldType}, hasOptions=${!!question.options}`);
  if (question.options && question.options.length > 0) {
    console.log(`   Options[0]:`, question.options[0]);
  }

  return {
    id: fieldId,
    label: question.question_text || question.question || question.label || 'Field',
    fieldType: mappedFieldType,
    criticalAttribute: question.critical_attribute || 'unknown',
    validation: {
      required: question.required !== false,
      ...(question.validation || {})
    },
    section: sectionId,
    order: index + 1,
    businessImpactScore: question.business_impact_score || 0.7,
    options: fieldOptions,
    helpText: question.help_text || question.description,
    metadata: {
      ...question.metadata,
      asset_id: assetId,  // Ensure asset_id is in metadata for grouping
      original_field_id: baseFieldId  // Store original field_id for backend submission
    },
    multiple: question.multiple || mappedFieldType === 'multiselect',  // Ensure multiselect is flagged
    placeholder: question.placeholder  // Pass through placeholder text
  };
};

/**
 * Groups questions into logical sections based on category
 */
export const groupQuestionsIntoSections = (questions: QuestionData[]): FormSection[] => {
  // CRITICAL FIX (Bug #768): Use backend-provided categories dynamically
  // Instead of hardcoded frontend categories, group ALL questions by their actual category
  // This ensures no questions are filtered out when backend generates new category types

  if (!questions || questions.length === 0) {
    return [];
  }

  // Helper: Convert category to human-readable title
  const categoryToTitle = (category: string): string => {
    const titleMap: Record<string, string> = {
      'asset_selection': 'Asset Selection',
      'basic': 'Basic Information',
      'business': 'Business Information',
      'technical': 'Technical Details',
      'technical_details': 'Technical Details',
      'technical_debt': 'Technical Debt & Modernization',
      'infrastructure': 'Infrastructure & Deployment',
      'compliance': 'Compliance & Security',
      'data_validation': 'Data Quality & Validation',
      'metadata': 'Metadata & Configuration',
      'application': 'Application Details',
    };
    return titleMap[category] || category
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Helper: Get description for category
  const categoryToDescription = (category: string): string => {
    const descMap: Record<string, string> = {
      'asset_selection': 'Select assets to enhance with additional data',
      'basic': 'Core application details',
      'business': 'Business context and ownership information',
      'technical': 'Technical architecture and dependencies',
      'technical_details': 'Technical architecture and implementation details',
      'technical_debt': 'Technical debt assessment and modernization needs',
      'infrastructure': 'Deployment environment and infrastructure details',
      'compliance': 'Data classification and compliance requirements',
      'data_validation': 'Data quality checks and validation rules',
      'metadata': 'System metadata and configuration',
      'application': 'Application-specific details and properties',
    };
    return descMap[category] || `Questions related to ${categoryToTitle(category).toLowerCase()}`;
  };

  // Helper: Get order priority for category
  const categoryOrder = (category: string): number => {
    const orderMap: Record<string, number> = {
      'asset_selection': 0,
      'basic': 1,
      'business': 2,
      'application': 3,
      'technical_details': 4,
      'technical': 4,
      'infrastructure': 5,
      'data_validation': 6,
      'technical_debt': 7,
      'metadata': 8,
      'compliance': 9,
    };
    return orderMap[category] ?? 50; // Unknown categories go last
  };

  // Group questions by category
  const categoryMap = new Map<string, QuestionData[]>();

  for (const question of questions) {
    const category = question.category || 'uncategorized';
    if (!categoryMap.has(category)) {
      categoryMap.set(category, []);
    }
    categoryMap.get(category).push(question);
  }

  console.log(`📊 Grouped ${questions.length} questions into ${categoryMap.size} categories:`,
    Array.from(categoryMap.entries()).map(([cat, qs]) => `${cat} (${qs.length})`).join(', ')
  );

  // Create sections from categories
  const sections: FormSection[] = [];

  for (const [category, categoryQuestions] of categoryMap.entries()) {
    const sectionId = `agent-${category.replace(/_/g, '-')}`;
    const order = categoryOrder(category);

    sections.push({
      id: sectionId,
      title: categoryToTitle(category),
      description: categoryToDescription(category),
      fields: categoryQuestions.map((q, index) =>
        convertQuestionToFormField(q, index, sectionId)
      ),
      order,
      requiredFieldsCount: categoryQuestions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: categoryQuestions.length / questions.length, // Proportional to question count
    });
  }

  // Sort sections by order
  sections.sort((a, b) => a.order - b.order);

  console.log(`✅ Created ${sections.length} sections with ${sections.reduce((sum, s) => sum + s.fields.length, 0)} total fields`);

  return sections;
};

/**
 * Converts CrewAI questionnaires to AdaptiveFormData format
 */
/**
 * Convert a single questionnaire to form data format
 */
export const convertQuestionnaireToFormData = (
  questionnaire: QuestionnaireData,
  applicationId?: string | null,
  applications?: Array<{ asset_id: string; application_name: string }>
): AdaptiveFormData => {
  return convertQuestionnairesToFormData(questionnaire, applicationId || null, applications);
};

export const convertQuestionnairesToFormData = (
  questionnaire: QuestionnaireData | AdaptiveQuestionnaireResponse,
  applicationId: string | null,
  applications?: Array<{ asset_id: string; application_name: string }>
): AdaptiveFormData => {
  try {
    const questions = questionnaire.questions || [];
    console.log('🔍 Converting questionnaire with questions:', questions.map(q => ({
      field_id: q.field_id,
      question_text: q.question_text,
      id: q.id || q.field_id,
      input_type: q.input_type,  // DEBUG: Check if input_type is present
      field_type: q.field_type,  // DEBUG: Check legacy field_type
      options_count: q.options?.length || 0  // DEBUG: Check if options exist
    })));

    // Special handling for bootstrap_asset_selection questionnaire
    const questionnaireId = questionnaire.id || 'agent-form-001';
    const isAssetSelectionBootstrap = questionnaireId === 'bootstrap_asset_selection';

    if (isAssetSelectionBootstrap) {
      console.log('🎯 Converting bootstrap_asset_selection questionnaire (ID:', questionnaireId, ')');

      // For bootstrap asset selection, ensure we have the correct structure
      const assetSelectionQuestions = questions.map(q => ({
        ...q,
        field_id: q.id || q.field_id || 'selected_assets',
        field_type: q.type || q.field_type || 'multiselect',
        category: 'asset_selection',
        required: q.required !== false
      }));

      const sections = groupQuestionsIntoSections(assetSelectionQuestions);

      return {
        formId: 'bootstrap_asset_selection', // Always use this ID for asset selection forms
        applicationId: applicationId || 'app-new',
        applicationName: 'Asset Selection', // Bootstrap forms don't have specific asset names yet
        sections,
        totalFields: questions.length,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
        requiredFields: questions.filter((q: any) => q.required !== false).length,
        estimatedCompletionTime: 5, // Asset selection should be quick
        confidenceImpactScore: 1.0 // High confidence for asset selection
      };
    }

    // Regular questionnaire processing
    const sections = groupQuestionsIntoSections(questions);
    console.log('🔍 Generated sections with fields:');
    sections.forEach(s => {
      console.log(`  Section: ${s.id}`);
      s.fields.forEach(f => {
        console.log(`    Field ID: "${f.id}", Label: "${f.label}"`);
      });
    });

    const totalFields = questions.length;
    const requiredFields = questions.filter((q: QuestionData) => q.required !== false).length;

    // Issue #762: UUID-based asset name lookup using applications array
    // This ensures correct name resolution even with duplicate asset names
    const extractAssetName = (): string | undefined => {
      // PREFERRED: Look up by asset_id from question metadata (UUID-based, handles duplicates)
      if (applications && applications.length > 0) {
        for (const question of questions) {
          const assetId = question.metadata?.asset_id || question.metadata?.asset_ids?.[0];
          if (assetId) {
            const app = applications.find(a => a.asset_id === assetId);
            if (app) {
              // CRITICAL FIX (Bug #768): Use app.name instead of app.application_name
              // The Asset model has 'name' field, not 'application_name' field
              const assetName = app.name || app.application_name || app.asset_name;
              console.log('✅ Found asset name via UUID lookup:', assetName, 'for asset_id:', assetId);
              return assetName;
            }
          }
        }
      }

      // FALLBACK 1: Try to extract from question text patterns like "for Admin Dashboard"
      for (const question of questions) {
        const text = question.question_text || question.label || '';
        // Pattern: "for Asset_Name" or similar
        const match = text.match(/for ([^?.,]+)/);
        if (match && match[1]) {
          const assetName = match[1].trim();
          // Filter out generic terms to avoid false positives
          if (!assetName.match(/^(the|this|that|which|your|Asset [a-f0-9]{8})$/i)) {
            return assetName;
          }
        }
      }

      // FALLBACK 2: Try metadata asset_name field
      for (const question of questions) {
        if (question.metadata?.asset_name) {
          return question.metadata.asset_name as string;
        }
      }

      return undefined;
    };

    // Extract asset_id from question metadata for proper backend linkage
    // This ensures questionnaire responses get linked to the correct asset in the database
    const extractAssetId = (): string | null => {
      for (const question of questions) {
        const assetId = question.metadata?.asset_id || question.metadata?.asset_ids?.[0];
        if (assetId) {
          console.log('✅ Extracted asset_id from question metadata:', assetId);
          return assetId;
        }
      }
      return null;
    };

    const applicationName = extractAssetName();
    const extractedAssetId = extractAssetId();

    return {
      formId: questionnaireId,
      applicationId: extractedAssetId || applicationId || 'app-new',
      applicationName, // CRITICAL FIX: Actual asset name extracted from questions
      sections,
      totalFields,
      requiredFields,
      estimatedCompletionTime: questionnaire.estimated_completion_time || Math.max(20, totalFields * 2),
      confidenceImpactScore: questionnaire.confidence_impact_score || 0.85
    };

  } catch (error) {
    console.error('Error converting questionnaire to form data:', error);
    throw new Error('Failed to convert questionnaire data');
  }
};

/**
 * Creates a fallback form when CrewAI agents are not available
 */
export const createFallbackFormData = (applicationId: string | null): AdaptiveFormData => {
  return {
    formId: 'fallback-form-001',
    applicationId: applicationId || 'app-new',
    applicationName: undefined, // Will be extracted if available
    sections: [
      {
        id: 'basic-info',
        title: 'Basic Information',
        description: 'Core application details (fallback form)',
        fields: [
          {
            id: 'app-name',
            label: 'Application Name',
            fieldType: 'text',
            criticalAttribute: 'name',
            validation: { required: true, minLength: 2 },
            section: 'basic-info',
            order: 1,
            businessImpactScore: 0.9
          },
          {
            id: 'app-type',
            label: 'Application Type',
            fieldType: 'select',
            criticalAttribute: 'type',
            options: getDefaultFieldOptions('application_type'),
            validation: { required: true },
            section: 'basic-info',
            order: 2,
            businessImpactScore: 0.8
          }
        ],
        order: 1,
        requiredFieldsCount: 2,
        completionWeight: 0.5
      }
    ],
    totalFields: 2,
    requiredFields: 2,
    estimatedCompletionTime: 10,
    confidenceImpactScore: 0.6
  };
};

/**
 * Validates form data structure
 */
export const validateFormDataStructure = (formData: AdaptiveFormData): boolean => {
  if (!formData.formId || !formData.sections || !Array.isArray(formData.sections)) {
    return false;
  }

  return formData.sections.every(section =>
    section.id &&
    section.title &&
    Array.isArray(section.fields) &&
    section.fields.every(field =>
      field.id &&
      field.label &&
      field.fieldType &&
      field.section === section.id
    )
  );
};
