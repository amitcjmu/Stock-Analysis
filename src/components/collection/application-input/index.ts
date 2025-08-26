/**
 * Application Input Components
 *
 * Components for handling application identity and deduplication in the collection flow.
 * These components work together to provide a comprehensive solution for managing
 * application names with real-time duplicate detection and suggestion capabilities.
 */

export { ApplicationInputField } from './ApplicationInputField';
export { DuplicateDetectionModal } from './DuplicateDetectionModal';
export { CanonicalApplicationView } from './CanonicalApplicationView';
export { ApplicationDeduplicationManager } from './ApplicationDeduplicationManager';

// Re-export types for convenience
export type {
  CanonicalApplication,
  ApplicationVariant,
  ApplicationSuggestion,
  SimilarityMatch,
  CanonicalApplicationSelection,
  DuplicateDecision,
  ApplicationInputState,
  DuplicateDetectionState,
} from '@/types/collection/canonical-applications';
