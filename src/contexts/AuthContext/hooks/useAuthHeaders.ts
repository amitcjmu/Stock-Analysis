import { useCallback } from 'react';
import { User, Client, Engagement, Session } from '../types';
import { tokenStorage } from '../storage';

export const useAuthHeaders = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  session: Session | null
) => {
  return useCallback((): Record<string, string> => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser();
    const headers: Record<string, string> = {};
    
    const effectiveUser = user || storedUser;
    
    console.log('🔍 getAuthHeaders Debug:', {
      token: token ? `present (${token.substring(0, 20)}...)` : 'missing',
      user: user ? { 
        id: user.id, 
        role: user.role, 
        full_name: user.full_name,
        email: user.email 
      } : null,
      storedUser: storedUser ? {
        id: storedUser.id,
        role: storedUser.role,
        full_name: storedUser.full_name,
        email: storedUser.email
      } : null,
      effectiveUser: effectiveUser ? {
        id: effectiveUser.id,
        role: effectiveUser.role,
        full_name: effectiveUser.full_name,
        email: effectiveUser.email
      } : null,
      client: client ? { id: client.id, name: client.name } : null,
      engagement: engagement ? { id: engagement.id, name: engagement.name } : null,
      session: session ? { id: session.id, name: session.name } : null
    });
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (effectiveUser && effectiveUser.id) {
      headers['X-User-ID'] = effectiveUser.id;
      headers['X-User-Role'] = effectiveUser.role || 'user';
      console.log('✅ Added X-User-ID header:', effectiveUser.id);
    } else if (token) {
      const tokenMatch = token.match(/db-token-([a-f0-9-]{36})/);
      if (tokenMatch) {
        const extractedUserId = tokenMatch[1];
        headers['X-User-ID'] = extractedUserId;
        headers['X-User-Role'] = 'user';
        console.log('✅ Extracted X-User-ID from token:', extractedUserId);
      } else {
        console.warn('⚠️ No user or user.id available and could not extract from token:', { effectiveUser, token: token ? token.substring(0, 30) + '...' : null });
      }
    } else {
      console.warn('⚠️ No user or user.id available for X-User-ID header:', { effectiveUser });
    }

    if (client && client.id) {
      headers['X-Client-Account-ID'] = client.id;
      console.log('✅ Added X-Client-Account-ID header:', client.id);
    } else {
      console.warn('⚠️ No client or client.id available for X-Client-Account-ID header:', { client });
    }

    if (engagement && engagement.id) {
      headers['X-Engagement-ID'] = engagement.id;
      console.log('✅ Added X-Engagement-ID header:', engagement.id);
    } else {
      console.warn('⚠️ No engagement or engagement.id available for X-Engagement-ID header:', { engagement });
    }
    
    if (session && session.id) {
      headers['X-Session-ID'] = session.id;
      console.log('✅ Added X-Session-ID header:', session.id);
    } else {
      console.warn('⚠️ No session or session.id available for X-Session-ID header:', { session });
    }

    console.log('🔍 Final headers being sent:', headers);
    return headers;
  }, [user, client, engagement, session]);
};