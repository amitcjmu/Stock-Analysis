/**
 * Critical Attributes Component Types
 * 
 * Types for critical attribute management, editing, and configuration.
 */

import { ReactNode } from 'react';
import { BaseDiscoveryProps, CriticalAttribute, ValidationError, BusinessRule } from './base-types';

// Critical Attributes component types
export interface CriticalAttributesTabProps extends BaseDiscoveryProps {
  attributes: CriticalAttribute[];
  onAttributeUpdate: (attributeId: string, updates: Partial<CriticalAttribute>) => void;
  flowId: string;
  readonly?: boolean;
  enableBulkOperations?: boolean;
  enableFiltering?: boolean;
  enableSorting?: boolean;
  enableGrouping?: boolean;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  enableExport?: boolean;
  customActions?: AttributeAction[];
  onCustomAction?: (action: AttributeAction, attributes: CriticalAttribute[]) => void;
  validationEnabled?: boolean;
  onValidationChange?: (isValid: boolean, errors: ValidationError[]) => void;
  categories?: AttributeCategory[];
  onCategoryFilter?: (categories: string[]) => void;
  priorities?: AttributePriority[];
  onPriorityFilter?: (priorities: string[]) => void;
  layout?: 'table' | 'card' | 'grid' | 'kanban';
  cardLayout?: CardLayoutConfig;
  gridLayout?: GridLayoutConfig;
  kanbanLayout?: KanbanLayoutConfig;
}

export interface AttributeEditorProps extends BaseDiscoveryProps {
  attribute: CriticalAttribute;
  onUpdate: (updates: Partial<CriticalAttribute>) => void;
  onSave: () => void;
  onCancel: () => void;
  readonly?: boolean;
  validationEnabled?: boolean;
  validationErrors?: ValidationError[];
  businessRules?: BusinessRule[];
  onBusinessRuleAdd?: (rule: BusinessRule) => void;
  onBusinessRuleUpdate?: (ruleId: string, updates: Partial<BusinessRule>) => void;
  onBusinessRuleDelete?: (ruleId: string) => void;
  availableDataTypes?: DataTypeOption[];
  availableCategories?: string[];
  availableTags?: string[];
  onTagAdd?: (tag: string) => void;
  onTagRemove?: (tag: string) => void;
  customFields?: CustomField[];
  onCustomFieldUpdate?: (fieldId: string, value: any) => void;
  tabs?: AttributeEditorTab[];
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

// Supporting types
export interface AttributeAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (attributes: CriticalAttribute[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface AttributeCategory {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string | ReactNode;
}

export interface AttributePriority {
  id: string;
  name: string;
  level: number;
  color?: string;
  icon?: string | ReactNode;
}

export interface CardLayoutConfig {
  columns: number;
  spacing: number;
  showHeaders: boolean;
  showMetadata: boolean;
  compactMode: boolean;
}

export interface GridLayoutConfig {
  columns: number;
  rowHeight: number;
  spacing: number;
  responsive: boolean;
  breakpoints: Record<string, number>;
}

export interface KanbanLayoutConfig {
  swimlanes: string[];
  cardHeight: number;
  spacing: number;
  dragAndDrop: boolean;
  collapsible: boolean;
}

export interface DataTypeOption {
  value: string;
  label: string;
  description?: string;
  validator?: (value: any) => boolean;
  formatter?: (value: any) => string;
  parser?: (value: string) => any;
}

export interface CustomField {
  id: string;
  name: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'select' | 'multiselect' | 'textarea';
  label: string;
  placeholder?: string;
  required?: boolean;
  options?: { value: any; label: string }[];
  validation?: ValidationRule[];
  value?: any;
  metadata?: Record<string, any>;
}

export interface AttributeEditorTab {
  id: string;
  label: string;
  icon?: string | ReactNode;
  content: ReactNode;
  disabled?: boolean;
  badge?: string | number;
}