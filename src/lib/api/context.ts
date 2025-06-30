/**
 * Context API - Functions for managing user context and defaults
 */

import { apiCall } from '@/config/api';

export interface UpdateUserDefaultsRequest {
  client_id?: string;
  engagement_id?: string;
}

export interface UpdateUserDefaultsResponse {
  success: boolean;
  message: string;
  updated_defaults: {
    default_client_id: string | null;
    default_engagement_id: string | null;
  };
}

/**
 * Update user's default client and engagement preferences
 * This ensures that when the user logs in or refreshes the page,
 * their previously selected context is restored.
 */
export const updateUserDefaults = async (
  request: UpdateUserDefaultsRequest
): Promise<UpdateUserDefaultsResponse> => {
  try {
    console.log('🔄 Updating user defaults:', request);
    
    const response = await apiCall('/api/v1/context/me/defaults', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    console.log('✅ User defaults updated successfully:', response);
    return response;
  } catch (error: any) {
    console.error('❌ Failed to update user defaults:', {
      error: error.message || error,
      status: error.status,
      request,
      endpoint: '/api/v1/context/me/defaults'
    });
    
    // Don't throw the error - make this non-blocking
    // The context switching should still work via localStorage
    console.warn('⚠️ Continuing with localStorage-only context persistence');
    
    // Return a fallback response
    return {
      success: false,
      message: `Failed to update user defaults: ${error.message || error}`,
      updated_defaults: {
        default_client_id: request.client_id || null,
        default_engagement_id: request.engagement_id || null,
      }
    };
  }
};

/**
 * Get current user context including client, engagement, and session
 */
export const getUserContext = async () => {
  try {
    const response = await apiCall('/api/v1/context/me', {
      method: 'GET',
    });

    return response;
  } catch (error) {
    console.error('Failed to get user context:', error);
    throw error;
  }
};

/**
 * Get list of clients accessible to the current user
 */
export const getUserClients = async () => {
  try {
    const response = await apiCall('/api/v1/context/clients', {
      method: 'GET',
    });

    return response;
  } catch (error) {
    console.error('Failed to get user clients:', error);
    throw error;
  }
};

/**
 * Get list of engagements for a specific client
 */
export const getClientEngagements = async (clientId: string) => {
  try {
    const response = await apiCall(`/api/v1/context/clients/${clientId}/engagements`, {
      method: 'GET',
    });

    return response;
  } catch (error) {
    console.error('Failed to get client engagements:', error);
    throw error;
  }
};