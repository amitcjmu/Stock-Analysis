// Demo data constants - These can be overridden by environment variables
export const DEMO_USER_ID = process.env.REACT_APP_DEMO_USER_ID || '33333333-3333-3333-3333-333333333333';
export const DEMO_ENGAGEMENT_ID = process.env.REACT_APP_DEMO_ENGAGEMENT_ID || '22222222-2222-2222-2222-222222222222';
export const DEMO_CLIENT_ID = process.env.REACT_APP_DEMO_CLIENT_ID || '11111111-1111-1111-1111-111111111111';
export const DEMO_ENGAGEMENT_NAME = process.env.REACT_APP_DEMO_ENGAGEMENT_NAME || 'Demo Cloud Migration Project';

export const DEMO_ENGAGEMENT_DATA = {
  id: DEMO_ENGAGEMENT_ID,
  name: DEMO_ENGAGEMENT_NAME,
  client_id: DEMO_CLIENT_ID,
  status: 'active' as const,
  type: 'migration' as const,
  start_date: '2024-01-01T00:00:00Z',
  end_date: '2024-12-31T23:59:59Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  metadata: {
    project_manager: 'Demo PM',
    budget: 1000000
  }
};
