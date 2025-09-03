// Mock API responses for testing collection flow and assessment transition
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

  // Collection flows with different statuses for testing
  '/api/v1/collection/flows': {
    items: [
      {
        id: 'completed-flow-456',
        flow_id: 'completed-flow-456',
        status: 'completed',
        assessment_ready: true,
        progress_percentage: 100,
        application_count: 3,
        completed_applications: 3,
        created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        updated_at: new Date().toISOString()
      },
      {
        id: 'incomplete-flow-789',
        flow_id: 'incomplete-flow-789',
        status: 'in_progress',
        assessment_ready: false,
        progress_percentage: 60,
        application_count: 5,
        completed_applications: 3,
        created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        updated_at: new Date().toISOString()
      }
    ]
  },

  // Collection status endpoint
  '/api/v1/collection/status': {
    active_flows: 2,
    completed_flows: 1,
    total_applications: 8,
    completed_applications: 3
  },

  // Collection incomplete flows
  '/api/v1/collection/incomplete': {
    items: [
      {
        id: 'incomplete-flow-789',
        flow_id: 'incomplete-flow-789',
        status: 'in_progress',
        progress_percentage: 60,
        application_count: 5,
        completed_applications: 3
      }
    ]
  },

  // Individual flow detail endpoints - these are called by getFlowDetails()
  '/api/v1/collection/flows/completed-flow-456': {
    id: 'completed-flow-456',
    flow_id: 'completed-flow-456',
    status: 'completed',
    progress_percentage: 100,
    assessment_ready: true,
    automation_tier: 'tier_1',
    application_count: 3,
    completed_applications: 3,
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    completed_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    collection_metrics: {
      platforms_detected: 3,
      data_collected: 3,
      gaps_resolved: 0
    }
  },

  '/api/v1/collection/flows/incomplete-flow-789': {
    id: 'incomplete-flow-789',
    flow_id: 'incomplete-flow-789',
    status: 'running',
    progress_percentage: 60,
    assessment_ready: false,
    automation_tier: 'tier_1',
    application_count: 5,
    completed_applications: 3,
    created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    updated_at: new Date().toISOString(),
    collection_metrics: {
      platforms_detected: 5,
      data_collected: 3,
      gaps_resolved: 1
    }
  },

  // Flow readiness endpoints - called by getFlowReadiness()
  '/api/v1/collection/flows/completed-flow-456/readiness': {
    flow_id: 'completed-flow-456',
    engagement_id: 'engagement-123',
    apps_ready_for_assessment: 3,
    quality: {
      collection_quality_score: 95,
      confidence_score: 90
    },
    phase_scores: {
      collection: 100,
      discovery: 0
    },
    issues: {
      total: 0,
      critical: 0,
      warning: 0,
      info: 0
    },
    updated_at: new Date().toISOString()
  },

  '/api/v1/collection/flows/incomplete-flow-789/readiness': {
    flow_id: 'incomplete-flow-789',
    engagement_id: 'engagement-123',
    apps_ready_for_assessment: 1,
    quality: {
      collection_quality_score: 60,
      confidence_score: 70
    },
    phase_scores: {
      collection: 60,
      discovery: 0
    },
    issues: {
      total: 2,
      critical: 0,
      warning: 2,
      info: 0
    },
    updated_at: new Date().toISOString()
  },

  '/api/v1/collection/questionnaires/completed-flow-456': {
    id: 'quest-456',
    flow_id: 'completed-flow-456',
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

  '/api/v1/collection/questionnaires/incomplete-flow-789': {
    id: 'quest-789',
    flow_id: 'incomplete-flow-789',
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
      }
    ]
  },

  // Response data for completed flow
  '/api/v1/collection/responses/completed-flow-456': {
    flow_id: 'completed-flow-456',
    responses: {
      application_name: 'Enterprise CRM System',
      application_type: 'web_application',
      business_criticality: 'mission_critical',
      hosting_environment: 'aws'
    },
    updated_at: new Date().toISOString()
  },

  // Response data for incomplete flow (missing some required fields)
  '/api/v1/collection/responses/incomplete-flow-789': {
    flow_id: 'incomplete-flow-789',
    responses: {
      application_name: 'Marketing Portal',
      application_type: 'web_application'
      // Missing business_criticality and hosting_environment
    },
    updated_at: new Date().toISOString()
  },

  // Assessment transition endpoint - success case
  '/api/v1/collection/flows/completed-flow-456/transition-to-assessment': {
    status: 'success',
    assessment_flow_id: 'assessment-flow-abc123',
    collection_flow_id: 'completed-flow-456',
    message: 'Assessment flow created successfully',
    created_at: new Date().toISOString()
  },

  // Assessment transition endpoint - failure case (incomplete flow)
  '/api/v1/collection/flows/incomplete-flow-789/transition-to-assessment': {
    error: 'not_ready',
    reason: 'Collection flow is not complete. Missing required data for applications: Marketing Portal, Legacy Database',
    missing_requirements: ['business_criticality', 'hosting_environment'],
    collection_flow_id: 'incomplete-flow-789'
  }
};

// Intercept fetch requests
const originalFetch = window.fetch;
window.fetch = async function(url, options) {
  const pathname = new URL(url, window.location.origin).pathname;
  const method = options?.method || 'GET';

  console.log(`[MOCK API] Intercepting ${method} ${pathname}`);

  // Special handling for POST requests to transition endpoint
  if (method === 'POST' && pathname.includes('/transition-to-assessment')) {
    const flowId = pathname.split('/')[4]; // Extract flow ID from path
    const mockKey = `/api/v1/collection/flows/${flowId}/transition-to-assessment`;

    if (window.mockApiResponses[mockKey]) {
      const mockResponse = window.mockApiResponses[mockKey];

      // Simulate error response for incomplete flows
      if (mockResponse.error === 'not_ready') {
        console.log(`[MOCK API] Returning error response for ${pathname}`);
        return Promise.resolve({
          ok: false,
          status: 400,
          json: async () => mockResponse,
          text: async () => JSON.stringify(mockResponse),
          headers: new Headers({
            'content-type': 'application/json'
          })
        });
      } else {
        console.log(`[MOCK API] Returning success response for ${pathname}`);
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
  }

  // Check if we have a mock response for this endpoint
  for (const [mockPath, mockResponse] of Object.entries(window.mockApiResponses)) {
    // Exact match first
    if (pathname === mockPath) {
      console.log(`[MOCK API] Exact match for ${pathname}, returning mock data`);
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
    // Then check for contains match (for backwards compatibility)
    if (pathname.includes(mockPath)) {
      console.log(`[MOCK API] Contains match for ${pathname} -> ${mockPath}, returning mock data`);
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

  // Fall back to original fetch for non-mocked endpoints
  console.log(`[MOCK API] No mock found for ${pathname}, using real API`);
  return originalFetch.apply(this, arguments);
};

console.log('[MOCK API] Mock API interceptor loaded successfully');
