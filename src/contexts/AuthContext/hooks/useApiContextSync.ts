import { useEffect } from 'react';
import { updateApiContext } from '@/config/api';
import { User, Client, Engagement, Session } from '../types';

export const useApiContextSync = (
  user: User | null,
  client: Client | null,
  engagement: Engagement | null,
  session: Session | null
) => {
  useEffect(() => {
    updateApiContext({ user, client, engagement, session });
  }, [user, client, engagement, session]);
};