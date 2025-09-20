import { renderHook, act, waitFor } from '@testing-library/react';
import type { MockedFunction } from 'vitest'
import { vi, describe, it, expect, beforeEach, Mock } from 'vitest'
import { useAttributeMappingActions } from '../discovery/attribute-mapping/useAttributeMappingActions';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { useAttributeMappingFlowDetection } from '../discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '../../config/api';
import { useNavigate } from 'react-router-dom';

// Mock dependencies
vi.mock('../useUnifiedDiscoveryFlow', () => ({
  useUnifiedDiscoveryFlow: vi.fn(),
  useDiscoveryFlowList: vi.fn()
}));

vi.mock('../discovery/useDiscoveryFlowAutoDetection', () => ({
  useAttributeMappingFlowDetection: vi.fn()
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: vi.fn()
}));

vi.mock('../../config/api', () => ({
  API_CONFIG: {
    ENDPOINTS: {
      DISCOVERY: {
        CONTEXT_FIELD_MAPPINGS: '/api/v1/unified-discovery/field-mappings',
        AGENT_CLARIFICATIONS: '/api/v1/unified-discovery/clarifications'
      }
    }
  },
  apiCall: vi.fn()
}));

vi.mock('react-router-dom', () => ({
  useLocation: vi.fn(() => ({ pathname: '/discovery/attribute-mapping' })),
  useNavigate: vi.fn(() => vi.fn())
}));

// Test fixtures
const mockFlow = {
  flow_id: 'test-flow-123',
  data_import_id: 'import-123',
  status: 'attribute_mapping',
  next_phase: 'data_cleansing',
  progress_percentage: 45,
  phases: {
    attribute_mapping: false
  },
  field_mapping: {
    mappings: {
      'hostname': {
        source_column: 'hostname',
        asset_field: 'device_name',
        confidence: 85,
        match_type: 'semantic_match',
        pattern_matched: true
      },
      'ip_address': {
        source_column: 'ip_address',
        asset_field: 'primary_ip',
        confidence: 95,
        match_type: 'exact_match',
        pattern_matched: true
      }
    },
    attributes: ['hostname', 'ip_address', 'os_type'],
    critical_attributes: {
      'hostname': {
        source_column: 'hostname',
        asset_field: 'device_name',
        confidence: 85
      }
    },
    progress: {
      total: 10,
      mapped: 7,
      critical_mapped: 5
    }
  }
};

const mockFieldMappings = [
  {
    id: 'mapping-1',
    sourceField: 'hostname',
    targetAttribute: 'device_name',
    confidence: 0.85,
    mapping_type: 'ai_suggested',
    sample_values: ['server01', 'server02'],
    status: 'pending',
    ai_reasoning: 'AI mapped hostname to device_name with 85% confidence',
    is_user_defined: false,
    user_feedback: null,
    validation_method: 'semantic_analysis',
    is_validated: false
  },
  {
    id: 'mapping-2',
    sourceField: 'ip_address',
    targetAttribute: 'primary_ip',
    confidence: 0.95,
    mapping_type: 'ai_suggested',
    sample_values: ['192.168.1.1', '192.168.1.2'],
    status: 'approved',
    ai_reasoning: 'AI mapped ip_address to primary_ip with 95% confidence',
    is_user_defined: false,
    user_feedback: null,
    validation_method: 'pattern_match',
    is_validated: true
  }
];

const mockFlowList = [
  { flow_id: 'test-flow-123', name: 'Test Flow', status: 'attribute_mapping' },
  { flow_id: 'test-flow-456', name: 'Another Flow', status: 'completed' }
];

describe('useAttributeMappingLogic', () => {
  let mockUseUnifiedDiscoveryFlow: MockedFunction<typeof useUnifiedDiscoveryFlow>;
  let mockUseAttributeMappingFlowDetection: MockedFunction<typeof useAttributeMappingFlowDetection>;
  let mockUseAuth: MockedFunction<typeof useAuth>;
  let mockApiCall: MockedFunction<typeof apiCall>;
  let mockNavigate: MockedFunction<typeof useNavigate>;

  beforeEach(() => {
    vi.clearAllMocks();

    // Use imported mocked modules
    mockUseUnifiedDiscoveryFlow = useUnifiedDiscoveryFlow;
    mockUseAttributeMappingFlowDetection = useAttributeMappingFlowDetection;
    mockUseAuth = useAuth as MockedFunction<typeof useAuth>;
    mockApiCall = apiCall as MockedFunction<typeof apiCall>;
    mockNavigate = useNavigate as MockedFunction<typeof useNavigate>;

    // Setup default mocks
    mockUseAttributeMappingFlowDetection.mockReturnValue({
      urlFlowId: null,
      autoDetectedFlowId: 'test-flow-123',
      effectiveFlowId: 'test-flow-123',
      flowList: mockFlowList,
      isFlowListLoading: false,
      flowListError: null,
      hasEffectiveFlow: true
    });

    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      flowState: mockFlow,
      isLoading: false,
      error: null,
      refreshFlow: vi.fn()
    });

    mockUseAuth.mockReturnValue({
      user: { id: 'user-123' },
      getAuthHeaders: vi.fn(() => ({ Authorization: 'Bearer token' }))
    });

    mockApiCall.mockResolvedValue({
      success: true,
      mappings: mockFieldMappings,
      status: 'success',
      page_data: { pending_questions: [] }
    });

    mockNavigate.mockReturnValue(vi.fn());
  });

  it('should load field mappings on mount', async () => {
    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.isAgenticLoading).toBe(false);

    await waitFor(() => {
      expect(result.current.fieldMappings).toHaveLength(2);
    });

    expect(result.current.fieldMappings[0].sourceField).toBe('hostname');
    expect(result.current.fieldMappings[1].sourceField).toBe('ip_address');
  });

  it('should handle approve mapping correctly', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      message: 'Mapping approved successfully'
    });

    const mockRefresh = vi.fn();
    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      ...mockUseUnifiedDiscoveryFlow(),
      refreshFlow: mockRefresh
    });

    const { result } = renderHook(() => useAttributeMappingLogic());

    await waitFor(() => {
      expect(result.current.fieldMappings).toHaveLength(2);
    });

    await act(async () => {
      await result.current.handleApproveMapping('mapping-1');
    });

    expect(mockApiCall).toHaveBeenCalledWith(
      '/data-import/mappings/approve-by-field',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'Authorization': 'Bearer token'
        }),
        body: JSON.stringify({
          source_field: 'hostname',
          target_field: 'device_name',
          import_id: 'import-123'
        })
      })
    );

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('should handle reject mapping correctly', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      message: 'Mapping rejected successfully'
    });

    const mockRefresh = vi.fn();
    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      ...mockUseUnifiedDiscoveryFlow(),
      refreshFlow: mockRefresh
    });

    const { result } = renderHook(() => useAttributeMappingLogic());

    await waitFor(() => {
      expect(result.current.fieldMappings).toHaveLength(2);
    });

    await act(async () => {
      await result.current.handleRejectMapping('mapping-1', 'Incorrect mapping');
    });

    expect(mockApiCall).toHaveBeenCalledWith(
      '/data-import/mappings/reject-by-field',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'Authorization': 'Bearer token'
        }),
        body: JSON.stringify({
          source_field: 'hostname',
          target_field: 'device_name',
          rejection_reason: 'Incorrect mapping',
          import_id: 'import-123'
        })
      })
    );

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('should use data_import_id not flow_id', () => {
    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.flowId).toBe('test-flow-123'); // flow_id for identification
    expect(result.current.flow?.data_import_id).toBe('import-123'); // data_import_id for API calls
    expect(result.current.selectedDataImportId).toBe('test-flow-123'); // effective flow ID
  });

  it('should calculate mapping progress correctly', () => {
    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.mappingProgress).toEqual({
      total: 10,
      mapped: 7,
      critical_mapped: 5,
      pending: 3
    });
  });

  it('should extract critical attributes correctly', () => {
    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.criticalAttributes).toHaveLength(1);
    expect(result.current.criticalAttributes[0]).toMatchObject({
      name: 'hostname',
      status: 'mapped',
      mapped_to: 'hostname',
      source_field: 'hostname',
      confidence: 0.85,
      migration_critical: true
    });
  });

  it('should handle loading states correctly', () => {
    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      flowState: null,
      isLoading: true,
      error: null,
      refreshFlow: vi.fn()
    });

    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.isAgenticLoading).toBe(true);
    expect(result.current.isFlowStateLoading).toBe(true);
    expect(result.current.isAnalyzing).toBe(true);
  });

  it('should handle error states correctly', () => {
    const testError = new Error('API Error');
    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      flowState: null,
      isLoading: false,
      error: testError,
      refreshFlow: vi.fn()
    });

    const { result } = renderHook(() => useAttributeMappingLogic());

    expect(result.current.agenticError).toBe(testError);
    expect(result.current.flowStateError).toBe(testError);
  });

  it('should determine continuation eligibility correctly', () => {
    const { result } = renderHook(() => useAttributeMappingLogic());

    // With 50% completion (1 approved out of 2 mappings), should not allow continuation
    // because we don't have required name and type fields
    expect(result.current.canContinueToDataCleansing()).toBe(false);

    // Mock mappings with required name and type fields approved
    const requiredFieldsMappings = [
      {
        id: 'mapping-1',
        sourceField: 'server_name',
        targetAttribute: 'asset_name', // Has 'name' in target
        confidence: 0.85,
        mapping_type: 'ai_suggested',
        status: 'approved',
        ai_reasoning: 'Mapped to asset name'
      },
      {
        id: 'mapping-2',
        sourceField: 'device_type',
        targetAttribute: 'asset_type', // Has 'type' in target
        confidence: 0.90,
        mapping_type: 'ai_suggested',
        status: 'approved',
        ai_reasoning: 'Mapped to asset type'
      },
      {
        id: 'mapping-3',
        sourceField: 'cpu_cores',
        targetAttribute: 'cpu_cores',
        confidence: 0.95,
        mapping_type: 'ai_suggested',
        status: 'pending',
        ai_reasoning: 'CPU mapping'
      }
    ];

    mockApiCall.mockResolvedValue({
      success: true,
      mappings: requiredFieldsMappings
    });

    // Should allow continuation with required fields (67% approval > 30% threshold)
    expect(result.current.canContinueToDataCleansing()).toBe(true);
  });

  it('should handle navigation to data import selection', async () => {
    const mockNavigateFn = vi.fn();
    mockNavigate.mockReturnValue(mockNavigateFn);

    const { result } = renderHook(() => useAttributeMappingLogic());

    await act(async () => {
      await result.current.handleDataImportSelection('new-flow-456');
    });

    expect(mockNavigateFn).toHaveBeenCalledWith('/discovery/attribute-mapping/new-flow-456');
  });

  it('should trigger field mapping crew correctly', async () => {
    const mockRefresh = vi.fn();
    mockUseUnifiedDiscoveryFlow.mockReturnValue({
      ...mockUseUnifiedDiscoveryFlow(),
      refreshFlow: mockRefresh
    });

    // Mock the masterFlowService import
    vi.doMock('../../services/api/masterFlowService', () => ({
      default: {
        resumeFlowAtPhase: vi.fn().mockResolvedValue({ success: true })
      }
    }));

    const { result } = renderHook(() => useAttributeMappingLogic());

    await act(async () => {
      await result.current.handleTriggerFieldMappingCrew();
    });

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('should handle API errors gracefully', async () => {
    mockApiCall.mockRejectedValueOnce(new Error('Network error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useAttributeMappingLogic());

    await act(async () => {
      await result.current.handleApproveMapping('mapping-1');
    });

    expect(consoleSpy).toHaveBeenCalledWith('❌ Failed to approve mapping:', expect.any(Error));

    consoleSpy.mockRestore();
  });

  it('should validate mapping IDs before approval', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useAttributeMappingLogic());

    await waitFor(() => {
      expect(result.current.fieldMappings).toHaveLength(2);
    });

    // Try to approve a temporary mapping ID (should fail)
    await act(async () => {
      await result.current.handleApproveMapping('mapping-temp-123');
    });

    expect(consoleSpy).toHaveBeenCalledWith('❌ Cannot approve temporary mapping ID:', 'mapping-temp-123');
    expect(mockApiCall).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
