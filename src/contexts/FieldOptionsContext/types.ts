/**
 * Field Options Context Types
 * Type definitions for the Field Options context
 */

export interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

export interface FieldOptionsContextType {
  availableFields: TargetField[];
  isLoading: boolean;
  error: string | null;
  refetchFields: () => Promise<void>;
  lastUpdated: Date | null;
}