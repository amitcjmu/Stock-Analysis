import React from 'react';
import { ChevronRight, Home, Building2, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useClients } from '../../hooks/useClients';
import { useEngagements } from '../../hooks/useEngagements';
import { useSessions } from '@/contexts/SessionContext';
import { SessionSelector } from '../session/SessionSelector';

// Simple breadcrumb component that shows the current engagement and session
// when available in the auth context

interface ContextBreadcrumbsProps {
  className?: string;
}

export const ContextBreadcrumbs: React.FC<ContextBreadcrumbsProps> = ({ className = '' }) => {
  const { 
    currentEngagementId, 
    setCurrentEngagementId,
    currentSessionId,
  } = useAuth();
  
  const { data: clients } = useClients();
  const { data: engagements } = useEngagements();
  const { data: sessions } = useSessions();

  // Find the full objects based on current IDs
  const currentEngagement = engagements?.find(e => e.id === currentEngagementId);
  const currentClient = clients?.find(c => c.id === currentEngagement?.client_id);

  const breadcrumbs = [];
  if (currentClient) {
    breadcrumbs.push({ type: 'Client', label: currentClient.name, id: currentClient.id });
  }
  if (currentEngagement) {
    breadcrumbs.push({ type: 'Engagement', label: currentEngagement.name, id: currentEngagement.id });
  }

  const handleHomeClick = () => {
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
      
      {breadcrumbs.map((crumb) => (
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

// Export as default for backward compatibility
export default ContextBreadcrumbs;