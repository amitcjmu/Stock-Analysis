/**
 * AuthContext Index
 * Central export file for AuthContext
 */

// Components
// eslint-disable-next-line react-refresh/only-export-components
export { AuthProvider } from './AuthContext/provider';

// Hooks
export { useAuth } from './AuthContext/useAuth';

// Types
export type { AuthContextType, User, Client, Engagement, Session, Flow } from './AuthContext/types';
