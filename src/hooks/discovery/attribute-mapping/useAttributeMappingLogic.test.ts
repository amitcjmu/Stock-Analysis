// Simple smoke test to verify the modular hooks can be imported and used
import type { useImportData, useAttributeMappingState, type AttributeMappingLogicResult, type FieldMapping, type CriticalAttribute } from './index'
import { useAttributeMappingLogic, useFlowDetection, useFieldMappings, useCriticalAttributes, useAttributeMappingActions } from './index'

// Test that all exports are available
describe('Attribute Mapping Hooks - Modular Architecture', () => {
  it('should export all required hooks', () => {
    expect(useAttributeMappingLogic).toBeDefined();
    expect(useFlowDetection).toBeDefined();
    expect(useFieldMappings).toBeDefined();
    expect(useImportData).toBeDefined();
    expect(useCriticalAttributes).toBeDefined();
    expect(useAttributeMappingActions).toBeDefined();
    expect(useAttributeMappingState).toBeDefined();
  });
  
  it('should export all required types', () => {
    // These should not throw TypeScript errors
    const exampleResult: AttributeMappingLogicResult = {} as AttributeMappingLogicResult;
    const exampleMapping: FieldMapping = {} as FieldMapping;
    const exampleAttribute: CriticalAttribute = {} as CriticalAttribute;
    
    expect(exampleResult).toBeDefined();
    expect(exampleMapping).toBeDefined();
    expect(exampleAttribute).toBeDefined();
  });
});