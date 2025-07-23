import { useRef } from 'react'
import { useEffect } from 'react'
import { updateApiContext } from '@/config/api';
import type { User, Client, Engagement, Flow } from '../types';

export const useApiContextSync = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  flow: Flow | null
) => {
  const lastContextRef = useRef<string>('');
  
  useEffect(() => {
    // Create a hash of the current context to avoid unnecessary updates
    const contextHash = JSON.stringify({
      userId: user?.id,
      clientId: client?.id, 
      engagementId: engagement?.id,
      flowId: flow?.id
    });
    
    // Only update if context actually changed
    if (contextHash !== lastContextRef.current) {
      console.log('🔄 API Context sync - updating context:', {
        user: user?.id,
        client: client?.id,
        engagement: engagement?.id, 
        flow: flow?.id
      });
      
      updateApiContext({ 
        user, 
        client, 
        engagement, 
        flow
      });
      
      lastContextRef.current = contextHash;
    }
  }, [user, client, engagement, flow]);
};