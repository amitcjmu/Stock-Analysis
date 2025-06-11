import React from 'react';
import { ChevronRight, Home, Building2, Calendar, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useClients } from '@/contexts/ClientContext';
import { useEngagements } from '@/contexts/EngagementContext';
import { useSessions } from '@/contexts/SessionContext';
import { SessionSelector } from '../session/SessionSelector';

interface ContextBreadcrumbsProps {
  className?: string;
}

export const ContextBreadcrumbs: React.FC<ContextBreadcrumbsProps> = ({ className = '' }) => {
  const { 
    currentEngagementId, 
    setCurrentEngagementId,
    currentSessionId,
    // A function to reset all context would be useful here
    // For now, we'll clear engagement which also clears session
  } = useAuth();
  
  // In a real multi-client setup, this would come from a higher-level context or user profile
  const { data: clients, isLoading: isLoadingClients } = useClients();
  const { data: engagements, isLoading: isLoadingEngagements } = useEngagements();
  const { data: sessions, isLoading: isLoadingSessions } = useSessions();

  // Find the full objects based on current IDs
  // This assumes a single client for now as per useEngagements hook logic
  const currentClient = clients?.[0]; 
  const currentEngagement = engagements?.find(e => e.id === currentEngagementId);
  const currentSession = sessions?.find(s => s.id === currentSessionId);

  const breadcrumbs = [];
  if (currentClient) {
    breadcrumbs.push({ type: 'Client', label: currentClient.name, id: currentClient.id });
  }
  if (currentEngagement) {
    breadcrumbs.push({ type: 'Engagement', label: currentEngagement.name, id: currentEngagement.id });
  }

  const handleHomeClick = () => {
    // This should ideally be a single function in AuthContext to reset context
    setCurrentEngagementId(null);
  };

  return (
    <div className={`flex items-center text-sm text-gray-500 ${className}`}>
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2"
        onClick={handleHomeClick}
      >
        <Home className="h-4 w-4" />
      </Button>
      
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.id}>
          <ChevronRight className="h-4 w-4 text-gray-400 mx-1" />
          <div className="flex items-center space-x-1">
            {crumb.type === 'Client' && <Building2 className="h-4 w-4" />}
            {crumb.type === 'Engagement' && <Calendar className="h-4 w-4" />}
            <span className="font-medium text-gray-700">{crumb.label}</span>
          </div>
        </React.Fragment>
      ))}

      {currentEngagement && (
        <>
            <ChevronRight className="h-4 w-4 text-gray-400 mx-1" />
            <SessionSelector />
        </>
      )}
    </div>
  );
}; 