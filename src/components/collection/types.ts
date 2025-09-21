/**
 * Type definitions for Collection Components
 *
 * Agent Team B3 - Frontend component types
 */

export interface AdaptiveFormData {
  formId: string;
  applicationId: string;
  sections: FormSection[];
  totalFields: number;
  requiredFields: number;
  estimatedCompletionTime: number;
  confidenceImpactScore: number;
}

export interface FormSection {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
  order: number;
  requiredFieldsCount: number;
  completionWeight: number;
}

export interface FormField {
  id: string;
  label: string;
  fieldType: FieldType;
  criticalAttribute: string;
  description?: string;
  placeholder?: string;
  options?: FieldOption[];
  validation?: ValidationRules;
  conditionalDisplay?: ConditionalRule;
  section: string;
  order: number;
  helpText?: string;
  businessImpactScore: number;
}

export interface FieldOption {
  value: string;
  label: string;
}

export interface ValidationRules {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  customRules?: string[];
}

export interface ConditionalRule {
  dependentField: string;
  condition: 'equals' | 'contains' | 'not_equals' | 'in' | 'not_in';
  values: string[];
  requiredWhenVisible?: boolean;
}

export type FieldType =
  | 'text'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'radio'
  | 'checkbox'
  | 'number'
  | 'date'
  | 'email'
  | 'url'
  | 'file'
  | 'date_input'
  | 'numeric_input'
  | 'multi_select'
  | 'technology_selection';

// CC: Form value type based on field types
type FieldValue = string | number | boolean | Date | File | string[];

export interface CollectionFormData {
  [fieldId: string]: FieldValue;
}

export interface ValidationError {
  fieldId: string;
  fieldLabel: string;
  errorCode: string;
  errorMessage: string;
  severity: 'error' | 'warning' | 'info';
  suggestedValue?: string;
}

export interface FieldValidationResult {
  fieldId: string;
  isValid: boolean;
  resultType: 'valid' | 'invalid' | 'warning' | 'conditional';
  errors: ValidationError[];
  warnings: ValidationError[];
  normalizedValue: FieldValue;
  confidenceScore: number;
}

export interface FormValidationResult {
  formId: string;
  isValid: boolean;
  overallConfidenceScore: number;
  completionPercentage: number;
  fieldResults: Record<string, FieldValidationResult>;
  crossFieldErrors: ValidationError[];
  businessRuleViolations: ValidationError[];
}

// Component Props Types
export interface AdaptiveFormProps {
  formData: AdaptiveFormData;
  initialValues?: CollectionFormData;
  onFieldChange: (fieldId: string, value: FieldValue) => void;
  onSubmit: (data: CollectionFormData) => Promise<void>;
  onSave?: () => void;
  onValidationChange?: (validation: FormValidationResult) => void;
  bulkMode?: boolean;
  onBulkToggle?: (enabled: boolean) => void;
  resetTrigger?: number; // Optional prop to trigger form reset (increment to reset)
  className?: string;
}

export interface BulkDataGridProps {
  applications: ApplicationSummary[];
  fields: FormField[];
  onDataChange: (applicationId: string, fieldId: string, value: FieldValue) => void;
  onBulkUpload?: (file: File) => Promise<void>;
  templateOptions?: TemplateOption[];
  className?: string;
}

export interface ApplicationSummary {
  id: string;
  name: string;
  technology?: string[];
  architecturePattern?: string;
  businessCriticality?: string;
}

export interface TemplateOption {
  id: string;
  name: string;
  description: string;
  applicableTypes: string[];
  fieldCount: number;
  effectivenessScore: number;
}

export interface ProgressTrackerProps {
  formId: string;
  totalSections: number;
  completedSections: number;
  overallCompletion: number;
  confidenceScore: number;
  milestones: ProgressMilestone[];
  timeSpent: number;
  estimatedTimeRemaining: number;
  className?: string;
}

export interface ProgressMilestone {
  id: string;
  title: string;
  description: string;
  achieved: boolean;
  achievedAt?: string;
  targetDate?: string;
  weight: number;
  required: boolean;
}

export interface ValidationDisplayProps {
  validation: FormValidationResult;
  onErrorClick?: (fieldId: string) => void;
  showWarnings?: boolean;
  className?: string;
}

export interface BulkUploadResult {
  uploadId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  totalRows: number;
  successfulRows: number;
  failedRows: number;
  validationIssues: ValidationError[];
  processingTime: number;
  dataQualityScore: number;
}

// Form field component props
export interface FormFieldProps {
  field: FormField;
  value: FieldValue;
  onChange: (value: FieldValue) => void;
  validation?: FieldValidationResult;
  disabled?: boolean;
  className?: string;
  questionNumber?: number;
}

export interface SectionCardProps {
  section: FormSection;
  isExpanded: boolean;
  onToggle: () => void;
  completionPercentage: number;
  validationStatus: 'valid' | 'invalid' | 'warning' | 'pending';
  children: React.ReactNode;
  className?: string;
}

export interface ConflictResolverProps {
  conflicts: DataConflict[];
  onResolve: (conflictId: string, resolution: ConflictResolution) => void;
  className?: string;
}

export interface DataConflict {
  id: string;
  attributeName: string;
  attributeLabel: string;
  conflictingValues: ConflictingValue[];
  recommendedResolution?: string;
  requiresUserReview: boolean;
}

export interface ConflictingValue {
  value: FieldValue;
  source: 'automated' | 'manual' | 'bulk' | 'template';
  sourceId: string;
  confidenceScore: number;
  collectedAt: string;
}

export interface ConflictResolution {
  selectedValue: FieldValue;
  selectedSource: string;
  userJustification?: string;
}

export interface TemplateMatchResult {
  templateId: string;
  templateName: string;
  matchScore: number;
  applicableReasons: string[];
  estimatedTimeSavings: number;
}

// Phase 1 Collection Gaps Types
export interface MaintenanceWindow {
  id?: string;
  name: string;
  description?: string;
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  start_time: string; // ISO date-time
  end_time: string; // ISO date-time
  recurrence_pattern?: 'none' | 'daily' | 'weekly' | 'monthly' | 'quarterly';
  timezone: string;
  impact_level: 'low' | 'medium' | 'high' | 'critical';
  approval_required: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface VendorProduct {
  id?: string;
  vendor_name: string;
  product_name: string;
  product_version?: string;
  category?: string;
  normalized_vendor?: string;
  normalized_product?: string;
  confidence_score?: number;
}

export interface TechnologySelectionOption {
  value: string;
  label: string;
  vendor?: string;
  product?: string;
  version?: string;
  category?: string;
  description?: string;
  confidence_score?: number;
}

export interface CompletenessCategory {
  id: string;
  name: string;
  description: string;
  completion_percentage: number;
  last_checked?: string;
  required_fields: string[];
  completed_fields: string[];
  status: 'complete' | 'partial' | 'missing' | 'error';
}

export interface CompletenessMetrics {
  overall_completion: number;
  categories: CompletenessCategory[];
  last_updated: string;
  total_fields: number;
  completed_fields: number;
}
