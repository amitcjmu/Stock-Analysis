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
    const response = await apiCall('/api/v1/context/me/defaults', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return response;
  } catch (error) {
    console.error('Failed to update user defaults:', error);
    throw error;
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