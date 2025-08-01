/**
 * Engagement Context Types
 * Type definitions for the Engagement context
 */

export interface Engagement {
  id: string;
  name: string;
  client_id: string;
  status: 'planning' | 'active' | 'completed' | 'on_hold';
  type: 'migration' | 'assessment' | 'modernization';
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface EngagementContextType {
  currentEngagement: Engagement | null;
  isLoading: boolean;
  error: Error | null;
  selectEngagement: (id: string) => Promise<void>;
  clearEngagement: () => void;
  getEngagementId: () => string | null;
  setDemoEngagement: (engagement: Engagement) => void;
}

export const ENGAGEMENT_KEY = 'current_engagement';
