/**
 * Client Context Types
 */

export interface Client {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  type: 'enterprise' | 'mid-market' | 'startup';
  created_at: string;
  updated_at: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface ClientContextType {
  currentClient: Client | null;
  availableClients: Client[];
  isLoading: boolean;
  error: Error | null;
  selectClient: (id: string) => Promise<void>;
  switchClient: (id: string) => Promise<void>;
  clearClient: () => void;
  getClientId: () => string | null;
  setDemoClient: (client: Client) => void;
}