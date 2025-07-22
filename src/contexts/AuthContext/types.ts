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

export interface Flow {
  id: string;
  name: string;
  status: string;
  engagement_id?: string;
  is_default?: boolean;
  flow_type?: string;
  auto_created?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

/**
 * User registration data for external integrations
 */
export interface UserRegistrationData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
  organization?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Registration response from external authentication providers
 */
export interface UserRegistrationResponse {
  user: User;
  token?: string;
  requiresVerification?: boolean;
  verificationUrl?: string;
  metadata?: Record<string, unknown>;
}

export interface AuthContextType {
  user: User | null;
  client: Client | null;
  engagement: Engagement | null;
  flow: Flow | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (userData: UserRegistrationData) => Promise<UserRegistrationResponse>;
  logout: () => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  switchEngagement: (engagementId: string, engagementData?: Engagement) => Promise<void>;
  switchFlow: (flowId: string, flowData?: Flow) => Promise<void>;
  setCurrentFlow: (flow: Flow | null) => void;
  currentEngagementId: string | null;
  currentFlowId: string | null;
  getAuthHeaders: () => Record<string, string>;
}

export interface ContextData {
  user?: User;
  client?: Client;
  engagement?: Engagement;
  flow?: Flow;
  timestamp?: number;
  source?: string;
}