export interface TokenStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  getUser: () => User | null;
  setUser: (user: User) => void;
  getRedirectPath: () => string | null;
  setRedirectPath: (path: string) => void;
  clearRedirectPath: () => void;
  removeToken: () => void;
}

export interface Client {
  id: string;
  name: string;
  status: string;
}

export interface Engagement {
  id: string;
  name: string;
  status: string;
  client_id?: string;
}

export interface Session {
  id: string;
  name: string;
  status: string;
  session_display_name?: string;
  session_name?: string;
  engagement_id?: string;
  is_default?: boolean;
  session_type?: string;
  auto_created?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Flow {
  id: string;
  name: string;
  status: string;
  session_id?: string; // For backward compatibility
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface AuthContextType {
  user: User | null;
  client: Client | null;
  engagement: Engagement | null;
  session: Session | null;
  flow: Flow | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (userData: any) => Promise<any>;
  logout: () => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  switchEngagement: (engagementId: string, engagementData?: Engagement) => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  switchFlow: (flowId: string, flowData?: Flow) => Promise<void>;
  setCurrentSession: (session: Session | null) => void;
  setCurrentFlow: (flow: Flow | null) => void;
  currentEngagementId: string | null;
  currentSessionId: string | null;
  currentFlowId: string | null;
  getAuthHeaders: () => Record<string, string>;
}

export interface ContextData {
  user?: User;
  client?: Client;
  engagement?: Engagement;
  session?: Session;
  timestamp?: number;
  source?: string;
}