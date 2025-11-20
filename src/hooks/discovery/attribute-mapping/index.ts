// Main hooks
export {
  useAttributeMappingLogicModular,
  useAttributeMappingLogic,
} from './useAttributeMappingLogicModular';
export { useAttributeMappingComposition } from './useAttributeMappingComposition';

// Specialized hooks
export { useFlowDetection } from './useFlowDetection';
export { useFieldMappings } from './useFieldMappings';
export { useImportData } from './useImportData';
export { useCriticalAttributes } from './useCriticalAttributes';
export { useAttributeMappingActions } from './useAttributeMappingActions';
export { useAttributeMappingState } from './useAttributeMappingState';

// Smart flow resolver (replaces useImportFlowResolver and useRecentFlowResolver)
export { useSmartFlowResolver } from './useSmartFlowResolver';
export { usePhaseAwareFlowResolver } from './usePhaseAwareFlowResolver';

// Types (re-export from centralized types file)
export type {
  FlowDetectionResult,
  FieldMapping,
  FieldMappingsResult,
  ImportDataResult,
  CriticalAttribute,
  CriticalAttributesResult,
  AttributeMappingActionsResult,
  MappingProgress,
  AttributeMappingStateResult,
  AttributeMappingLogicResult,
} from './types';
