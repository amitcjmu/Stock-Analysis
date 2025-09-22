/**
 * Form Data Transformation Utilities
 *
 * Utilities for converting between different data formats in collection workflows.
 * Extracted from AdaptiveForms.tsx for reusability across collection components.
 */

import type { AdaptiveFormData, FormSection, FormField, FieldOption } from '@/components/collection/types';
import type { ConfigurationValue, ConfigurationObject } from '@/types/shared/config-types';

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
  field_type?: string;
  question_type?: string;
  category?: string;
  critical_attribute?: string;
  required?: boolean;
  validation?: ConfigurationObject;
  business_impact_score?: number;
  options?: FieldOption[] | string[]; // can be FieldOption[] or string[] from backend
  help_text?: string;
  description?: string;
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

  // Use field_id if available, otherwise generate a default
  const fieldId = question.field_id || `question_${index + 1}`;

  const fieldOptions = normalizeOptions(question.options) || (defaultKey ? getDefaultFieldOptions(defaultKey) : undefined);

  return {
    id: fieldId,
    label: question.question_text || question.label || 'Field',
    fieldType: mapQuestionTypeToFieldType(question.field_type || question.question_type || 'text'),
    criticalAttribute: question.critical_attribute || 'unknown',
    validation: {
      required: question.required !== false,
      ...(question.validation || {})
    },
    section: sectionId,
    order: index + 1,
    businessImpactScore: question.business_impact_score || 0.7,
    options: fieldOptions,
    helpText: question.help_text || question.description
  };
};

/**
 * Groups questions into logical sections based on category
 */
export const groupQuestionsIntoSections = (questions: QuestionData[]): FormSection[] => {
  const sections: FormSection[] = [];

  // Group questions by category
  const basicQuestions = questions.filter((q: QuestionData) =>
    q.category === 'basic' ||
    q.category === 'business' ||
    q.field_id === 'application_name' ||
    q.field_id === 'application_type' ||
    q.field_id === 'business_criticality' ||
    q.field_id === 'primary_users' ||
    q.field_id === 'user_count'
  );

  const technicalQuestions = questions.filter((q: QuestionData) =>
    q.category === 'technical' ||
    q.field_id === 'technology_stack' ||
    q.field_id === 'database_type' ||
    q.field_id === 'architecture_pattern' ||
    q.field_id === 'api_interfaces' ||
    q.field_id === 'authentication_method'
  );

  const infrastructureQuestions = questions.filter((q: QuestionData) =>
    q.category === 'infrastructure' ||
    q.field_id === 'deployment_environment' ||
    q.field_id === 'cloud_provider' ||
    q.field_id === 'containerized' ||
    q.field_id === 'scalability_requirements'
  );

  const complianceQuestions = questions.filter((q: QuestionData) =>
    q.category === 'compliance' ||
    q.field_id === 'data_classification' ||
    q.field_id === 'compliance_requirements' ||
    q.field_id === 'disaster_recovery'
  );

  // Create basic information section
  if (basicQuestions.length > 0) {
    sections.push({
      id: 'agent-basic-info',
      title: 'Basic Information',
      description: 'Core application details identified by CrewAI gap analysis',
      fields: basicQuestions.map((q, index) =>
        convertQuestionToFormField(q, index, 'agent-basic-info')
      ),
      order: 1,
      requiredFieldsCount: basicQuestions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: 0.4
    });
  }

  // Create technical details section
  if (technicalQuestions.length > 0) {
    sections.push({
      id: 'agent-technical-details',
      title: 'Technical Details',
      description: 'Technical architecture and dependencies',
      fields: technicalQuestions.map((q, index) =>
        convertQuestionToFormField(q, index, 'agent-technical-details')
      ),
      order: 2,
      requiredFieldsCount: technicalQuestions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: 0.25
    });
  }

  // Create infrastructure section
  if (infrastructureQuestions.length > 0) {
    sections.push({
      id: 'agent-infrastructure',
      title: 'Infrastructure & Deployment',
      description: 'Deployment environment and infrastructure details',
      fields: infrastructureQuestions.map((q, index) =>
        convertQuestionToFormField(q, index, 'agent-infrastructure')
      ),
      order: 3,
      requiredFieldsCount: infrastructureQuestions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: 0.2
    });
  }

  // Create compliance section
  if (complianceQuestions.length > 0) {
    sections.push({
      id: 'agent-compliance',
      title: 'Compliance & Security',
      description: 'Data classification and compliance requirements',
      fields: complianceQuestions.map((q, index) =>
        convertQuestionToFormField(q, index, 'agent-compliance')
      ),
      order: 4,
      requiredFieldsCount: complianceQuestions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: 0.15
    });
  }

  // Fallback: If no sections were created, put all questions into a general section
  if (sections.length === 0 && questions.length > 0) {
    sections.push({
      id: 'agent-general',
      title: 'Adaptive Questionnaire',
      description: 'General questions generated from gap analysis',
      fields: questions.map((q, index) => convertQuestionToFormField(q, index, 'agent-general')),
      order: 1,
      requiredFieldsCount: questions.filter((q: QuestionData) => q.required !== false).length,
      completionWeight: 1.0
    });
  }

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
  applicationId?: string | null
): AdaptiveFormData => {
  return convertQuestionnairesToFormData(questionnaire, applicationId || null);
};

export const convertQuestionnairesToFormData = (
  questionnaire: QuestionnaireData,
  applicationId: string | null
): AdaptiveFormData => {
  try {
    const questions = questionnaire.questions || [];
    console.log('🔍 Converting questionnaire with questions:', questions.map(q => ({
      field_id: q.field_id,
      question_text: q.question_text
    })));
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

    return {
      formId: questionnaire.id || 'agent-form-001',
      applicationId: applicationId || 'app-new',
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
