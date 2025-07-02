import { useEffect } from 'react';
import { updateApiContext } from '@/config/api';
import { User, Client, Engagement, Session, Flow } from '../types';

export const useApiContextSync = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  session: Session | null,
  flow?: Flow | null
) => {
  useEffect(() => {
    updateApiContext({ 
      user, 
      client, 
      engagement, 
      flow: flow || null  // API expects 'flow' not 'session'
    });
  }, [user, client, engagement, flow]);
};