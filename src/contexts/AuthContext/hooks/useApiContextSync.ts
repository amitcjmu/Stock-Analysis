import { useEffect } from 'react';
import { updateApiContext } from '@/config/api';
import { User, Client, Engagement, Flow } from '../types';

export const useApiContextSync = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  flow: Flow | null
) => {
  useEffect(() => {
    updateApiContext({ 
      user, 
      client, 
      engagement, 
      flow
    });
  }, [user, client, engagement, flow]);
};