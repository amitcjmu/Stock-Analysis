import { useContext } from 'react';
import { AuthContext } from '@/contexts/AuthContext';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  clientAccountId?: string;
  engagementId?: string;
}

interface Client {
  id: string;
  name: string;
  slug: string;
}

interface Engagement {
  id: string;
  name: string;
  status: string;
}

interface Session {
  id: string;
  name: string;
  status: string;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  const { 
    user, 
    client, 
    engagement, 
    session, 
    isLoading, 
    error, 
    login, 
    logout, 
    switchClient, 
    switchEngagement, 
    switchSession 
  } = context;

  return {
    // User data
    user,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    
    // Client context
    client,
    clientAccountId: client?.id,
    
    // Engagement context
    engagement,
    engagementId: engagement?.id,
    
    // Session context
    session,
    sessionId: session?.id,
    
    // Loading and error states
    isLoading,
    error,
    
    // Methods
    login,
    logout,
    switchClient,
    switchEngagement,
    switchSession,
  };
};

export type { User, Client, Engagement, Session };
