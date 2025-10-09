/**
 * Local type definitions for AdaptiveForms component
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import type { ProgressMilestone } from "@/components/collection/types";

export interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

export interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

export interface QuestionnaireData {
  questions: Array<{
    id: string;
    text: string;
    type: string;
    options?: string[];
  }>;
  metadata?: Record<string, unknown>;
}

export interface AssetGroup {
  asset_id: string;
  asset_name: string;
  questions: Array<{
    field_id: string;
    question_text: string;
    field_type: string;
    required?: boolean;
    options?: string[];
    metadata?: Record<string, unknown>;
  }>;
  completion_percentage?: number;
}

// Re-export ProgressMilestone for convenience
export type { ProgressMilestone };
