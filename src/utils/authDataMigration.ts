/**
 * Auth Data Migration Utility
 * Migrates old numeric IDs to demo UUIDs
 */

const DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111";
const DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222";
const DEMO_USER_ID = "33333333-3333-3333-3333-333333333333";

export const migrateAuthData = () => {
  console.log('🔄 Running auth data migration...');
  
  // Check and migrate auth_client
  const authClient = localStorage.getItem('auth_client');
  if (authClient) {
    try {
      const client = JSON.parse(authClient);
      if (client.id && typeof client.id === 'number') {
        console.log('🔄 Migrating numeric client ID to demo UUID');
        client.id = DEMO_CLIENT_ID;
        localStorage.setItem('auth_client', JSON.stringify(client));
        localStorage.setItem('auth_client_id', DEMO_CLIENT_ID);
      }
    } catch (e) {
      console.error('Failed to migrate auth_client:', e);
    }
  }
  
  // Check and migrate auth_engagement
  const authEngagement = localStorage.getItem('auth_engagement');
  if (authEngagement) {
    try {
      const engagement = JSON.parse(authEngagement);
      if (engagement.id && typeof engagement.id === 'number') {
        console.log('🔄 Migrating numeric engagement ID to demo UUID');
        engagement.id = DEMO_ENGAGEMENT_ID;
        if (engagement.client_id && typeof engagement.client_id === 'number') {
          engagement.client_id = DEMO_CLIENT_ID;
        }
        localStorage.setItem('auth_engagement', JSON.stringify(engagement));
      }
    } catch (e) {
      console.error('Failed to migrate auth_engagement:', e);
    }
  }
  
  // Check and migrate auth_client_id
  const clientId = localStorage.getItem('auth_client_id');
  if (clientId && !clientId.includes('-')) {
    console.log('🔄 Migrating numeric auth_client_id to demo UUID');
    localStorage.setItem('auth_client_id', DEMO_CLIENT_ID);
  }
  
  // Check and migrate user_data
  const userData = localStorage.getItem('user_data');
  if (userData) {
    try {
      const user = JSON.parse(userData);
      if (user.id && typeof user.id === 'number') {
        console.log('🔄 Migrating numeric user ID to demo UUID');
        user.id = DEMO_USER_ID;
        localStorage.setItem('user_data', JSON.stringify(user));
      }
    } catch (e) {
      console.error('Failed to migrate user_data:', e);
    }
  }
  
  console.log('✅ Auth data migration complete');
};

/**
 * Clear all auth data to force re-fetch
 */
export const clearAuthData = () => {
  console.log('🧹 Clearing all auth data...');
  localStorage.removeItem('auth_client');
  localStorage.removeItem('auth_engagement');
  localStorage.removeItem('auth_session');
  localStorage.removeItem('auth_client_id');
  console.log('✅ Auth data cleared');
};