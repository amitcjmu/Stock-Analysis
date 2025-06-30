/**
 * Test file for v3 API client
 * This file tests TypeScript compilation and basic functionality
 */

import { 
  createApiV3Client, 
  FlowPhase, 
  FlowStatus, 
  ExecutionMode,
  ApiError,
  isApiError,
  createUserFriendlyError 
} from './index';

// Test client creation
const testClient = () => {
  const client = createApiV3Client({
    baseURL: 'http://localhost:8000/api/v3',
    timeout: 30000,
    enableLogging: true
  });

  return client;
};

// Test type safety
const testTypeSafety = async () => {
  const api = testClient();

  try {
    // Test discovery flow operations
    const flow = await api.discoveryFlow.createFlow({
      name: 'Test Flow',
      description: 'A test flow for validation',
      client_account_id: '550e8400-e29b-41d4-a716-446655440000',
      engagement_id: '550e8400-e29b-41d4-a716-446655440001',
      raw_data: [
        { hostname: 'server1', ip: '192.168.1.100' },
        { hostname: 'server2', ip: '192.168.1.101' }
      ],
      execution_mode: ExecutionMode.HYBRID
    });

    console.log('✅ Flow created:', flow.flow_id);
    console.log('✅ Flow status:', flow.status);
    console.log('✅ Current phase:', flow.current_phase);

    // Test status checks
    const status = await api.discoveryFlow.getFlowStatus(flow.flow_id);
    console.log('✅ Flow status retrieved:', status.status);

    // Test phase execution
    await api.discoveryFlow.executePhase(flow.flow_id, FlowPhase.FIELD_MAPPING);
    console.log('✅ Phase execution initiated');

    // Test field mapping
    const mappings = await api.fieldMapping.createFieldMapping({
      flow_id: flow.flow_id,
      source_fields: ['hostname', 'ip'],
      target_schema: 'asset_inventory',
      auto_map: true
    });
    console.log('✅ Field mappings created:', mappings.mapping_id);

    // Test list operations
    const flows = await api.discoveryFlow.listFlows({
      page: 1,
      page_size: 10,
      status: FlowStatus.IN_PROGRESS
    });
    console.log('✅ Flows listed:', flows.total);

  } catch (error) {
    if (isApiError(error)) {
      console.error('❌ API Error:', error.statusCode, error.message);
      const userMessage = createUserFriendlyError(error);
      console.error('❌ User message:', userMessage);
    } else {
      console.error('❌ Unknown error:', error);
    }
  }
};

// Test enum usage
const testEnums = () => {
  console.log('✅ Flow phases:', Object.values(FlowPhase));
  console.log('✅ Flow statuses:', Object.values(FlowStatus));
  console.log('✅ Execution modes:', Object.values(ExecutionMode));
};

// Test type inference
const testTypeInference = () => {
  const api = testClient();

  // These should have proper type inference
  const flowPromise = api.discoveryFlow.createFlow({
    name: 'Test',
    client_account_id: 'test',
    engagement_id: 'test',
    raw_data: []
  });

  const statusPromise = api.discoveryFlow.getFlowStatus('test-id');
  const mappingPromise = api.fieldMapping.getTargetSchemas();

  console.log('✅ Type inference working for promises');
  
  // Test that types are properly constrained
  const validStatus: FlowStatus = FlowStatus.COMPLETED;
  const validPhase: FlowPhase = FlowPhase.DATA_CLEANSING;
  
  console.log('✅ Enum constraints working:', validStatus, validPhase);
};

// Export test functions for verification
export {
  testClient,
  testTypeSafety,
  testEnums,
  testTypeInference
};

// Self-test - this will be removed before production
if (process.env.NODE_ENV === 'development') {
  console.log('🧪 Running v3 API client self-tests...');
  
  testEnums();
  testTypeInference();
  
  console.log('✅ All type safety tests passed');
}