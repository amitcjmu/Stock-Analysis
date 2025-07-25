// Debug script to test discovery flow endpoints
// Run this in the browser console when logged in to the application

async function testDiscoveryFlowEndpoints() {
  console.log('🔍 Testing Discovery Flow Endpoints...\n');

  // Get auth headers
  const getAuthHeaders = () => {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
    };

    // Add context headers if available
    const context = JSON.parse(localStorage.getItem('appContext') || '{}');
    if (context.client?.id) headers['X-Client-Account-ID'] = context.client.id;
    if (context.engagement?.id) headers['X-Engagement-ID'] = context.engagement.id;
    if (context.user?.id) headers['X-User-ID'] = context.user.id;

    return headers;
  };

  // Test endpoint 1: /api/v1/discovery/flows/active
  console.log('📍 Testing: /api/v1/discovery/flows/active');
  try {
    const response1 = await fetch('/api/v1/discovery/flows/active', {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    const data1 = await response1.json();
    console.log('✅ Response:', data1);
    console.log(`   - Status: ${response1.status}`);
    console.log(`   - Number of flows: ${Array.isArray(data1) ? data1.length : (data1.flows?.length || 0)}`);
    console.log('   - Structure:', Object.keys(data1));
    if (data1.flows?.length > 0 || (Array.isArray(data1) && data1.length > 0)) {
      const firstFlow = data1.flows?.[0] || data1[0];
      console.log('   - First flow keys:', Object.keys(firstFlow));
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Test endpoint 2: /api/v1/unified-discovery/flow/active
  console.log('📍 Testing: /api/v1/unified-discovery/flow/active');
  try {
    const response2 = await fetch('/api/v1/unified-discovery/flow/active', {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    const data2 = await response2.json();
    console.log('✅ Response:', data2);
    console.log(`   - Status: ${response2.status}`);
    console.log(`   - Number of flows: ${data2.flows?.length || 0}`);
    console.log('   - Structure:', Object.keys(data2));
    if (data2.flows?.length > 0) {
      console.log('   - First flow keys:', Object.keys(data2.flows[0]));
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n');

  // Test endpoint 3: /api/v1/data-import/latest-import
  console.log('📍 Testing: /api/v1/data-import/latest-import');
  try {
    const response3 = await fetch('/api/v1/data-import/latest-import', {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include'
    });
    const data3 = await response3.json();
    console.log('✅ Response:', data3);
    console.log(`   - Status: ${response3.status}`);
    console.log('   - Structure:', Object.keys(data3));
  } catch (error) {
    console.error('❌ Error:', error);
  }

  console.log('\n🎯 Test complete! Check the responses above to identify the issue.');
}

// Run the test
testDiscoveryFlowEndpoints();
