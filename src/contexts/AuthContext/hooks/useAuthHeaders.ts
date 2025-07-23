import { useCallback } from 'react';
import type { Client, Engagement } from '../types'
import type { User } from '../types'
import { tokenStorage } from '../storage';

export const useAuthHeaders = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  flowId: string | null
) => {
  return useCallback((): Record<string, string> => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser();
    const headers: Record<string, string> = {};
    
    const effectiveUser = user || storedUser;
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (effectiveUser && effectiveUser.id) {
      headers['X-User-ID'] = effectiveUser.id;
      headers['X-User-Role'] = effectiveUser.role || 'user';
    } else if (token) {
      const tokenMatch = token.match(/db-token-([a-f0-9-]{36})/);
      if (tokenMatch) {
        const extractedUserId = tokenMatch[1];
        headers['X-User-ID'] = extractedUserId;
        headers['X-User-Role'] = 'user';
      }
    }

    if (client && client.id) {
      headers['X-Client-Account-ID'] = client.id;
    }

    if (engagement && engagement.id) {
      headers['X-Engagement-ID'] = engagement.id;
    }
    
    if (flowId) {
      headers['X-Flow-ID'] = flowId;
    }

    return headers;
  }, [user, client, engagement, flowId]);
};