// Mock API responses for testing collection flow
window.mockApiResponses = {
  '/api/v1/auth/login': {
    access_token: 'mock-token-123',
    token_type: 'bearer',
    user: {
      email: 'demo@demo-corp.com',
      name: 'Demo User',
      role: 'admin'
    }
  },

  '/api/v1/collection/flows': {
    items: [{
      id: 'test-flow-123',
      flow_id: 'test-flow-123',
      status: 'in_progress',
      created_at: new Date().toISOString()
    }]
  },

  '/api/v1/collection/questionnaires/test-flow-123': {
    id: 'quest-123',
    flow_id: 'test-flow-123',
    questions: [
      {
        field_id: 'application_name',
        question_text: 'What is the application name?',
        field_type: 'text',
        required: true,
        category: 'identity'
      },
      {
        field_id: 'application_type',
        question_text: 'What type of application is this?',
        field_type: 'select',
        required: true,
        category: 'identity',
        options: [
          'web_application',
          'mobile_application',
          'desktop_application',
          'api_service',
          'database',
          'middleware'
        ]
      },
      {
        field_id: 'business_criticality',
        question_text: 'What is the business criticality level?',
        field_type: 'select',
        required: true,
        category: 'business',
        options: [
          'mission_critical',
          'business_important',
          'operational',
          'development_test',
          'low_priority'
        ]
      },
      {
        field_id: 'hosting_environment',
        question_text: 'Where is the application currently hosted?',
        field_type: 'select',
        required: true,
        category: 'infrastructure',
        options: [
          'on_premises',
          'aws',
          'azure',
          'gcp',
          'hybrid_cloud'
        ]
      }
    ]
  },

  '/api/v1/collection/responses/test-flow-123': {
    flow_id: 'test-flow-123',
    responses: {
      application_name: 'Enterprise CRM System',
      application_type: 'web_application',
      business_criticality: 'mission_critical',
      hosting_environment: 'aws'
    },
    updated_at: new Date().toISOString()
  }
};

// Intercept fetch requests
const originalFetch = window.fetch;
window.fetch = async function(url, options) {
  const pathname = new URL(url, window.location.origin).pathname;

  // Check if we have a mock response for this endpoint
  for (const [mockPath, mockResponse] of Object.entries(window.mockApiResponses)) {
    if (pathname.includes(mockPath) || pathname === mockPath) {
      console.log(`[MOCK API] Intercepted ${pathname}, returning mock data`);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        text: async () => JSON.stringify(mockResponse),
        headers: new Headers({
          'content-type': 'application/json'
        })
      });
    }
  }

  // Fall back to original fetch
  return originalFetch.apply(this, arguments);
};
