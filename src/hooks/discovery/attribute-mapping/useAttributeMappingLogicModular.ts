import { useAttributeMappingComposition } from './useAttributeMappingComposition';
import { AttributeMappingLogicResult } from './types';

/**
 * Main attribute mapping logic hook - refactored with modular architecture
 * This hook maintains the same API as the original useAttributeMappingLogic
 * but uses a clean, modular structure internally
 */
export const useAttributeMappingLogicModular = (): AttributeMappingLogicResult => {
  return useAttributeMappingComposition();
};

// Export for backward compatibility
export { useAttributeMappingLogicModular as useAttributeMappingLogic };