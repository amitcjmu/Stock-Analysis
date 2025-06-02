import React from 'react';
import { ChevronRight, Building2, Calendar, Database, Home, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useContext } from '@/hooks/useContext';

interface ContextBreadcrumbsProps {
  className?: string;
  showHome?: boolean;
  maxLength?: number;
}

const ContextBreadcrumbs: React.FC<ContextBreadcrumbsProps> = ({ 
  className = '', 
  showHome = true,
  maxLength = 60
}) => {
  const { context, getBreadcrumbs, setClient, setEngagement, setSession, setViewMode } = useContext();
  const breadcrumbs = getBreadcrumbs();

  const getIcon = (type: string) => {
    switch (type) {
      case 'client':
        return <Building2 className="h-3 w-3" />;
      case 'engagement':
        return <Calendar className="h-3 w-3" />;
      case 'session':
        return <Database className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const truncateText = (text: string, maxLen: number) => {
    if (text.length <= maxLen) return text;
    return text.substring(0, maxLen - 3) + '...';
  };

  const handleBreadcrumbClick = (type: string, index: number) => {
    switch (type) {
      case 'client':
        // Clear engagement and session to go back to client level
        setEngagement(null);
        setSession(null);
        break;
      case 'engagement':
        // Clear session to go back to engagement level
        setSession(null);
        setViewMode('engagement_view');
        break;
      case 'session':
        // Already at session level, just ensure session view
        setViewMode('session_view');
        break;
    }
  };

  if (breadcrumbs.length === 0) {
    return (
      <div className={`flex items-center text-sm text-gray-500 ${className}`}>
        {showHome && (
          <>
            <Home className="h-4 w-4 mr-1" />
            <span>No Context Selected</span>
          </>
        )}
      </div>
    );
  }

  return (
    <nav className={`flex items-center text-sm ${className}`} aria-label="Context breadcrumb">
      {showHome && (
        <>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-gray-500 hover:text-gray-700"
            onClick={() => {
              setClient(null);
              setEngagement(null);
              setSession(null);
            }}
          >
            <Home className="h-3 w-3" />
          </Button>
          <ChevronRight className="h-3 w-3 text-gray-400 mx-1" />
        </>
      )}
      
      {breadcrumbs.map((breadcrumb, index) => (
        <React.Fragment key={index}>
          <Button
            variant="ghost"
            size="sm"
            className={`h-6 px-2 flex items-center space-x-1 ${
              breadcrumb.active 
                ? 'text-blue-600 font-medium cursor-default' 
                : 'text-gray-600 hover:text-gray-800 cursor-pointer'
            }`}
            onClick={() => !breadcrumb.active && handleBreadcrumbClick(breadcrumb.type, index)}
            disabled={breadcrumb.active}
            title={breadcrumb.label}
          >
            {getIcon(breadcrumb.type)}
            <span>{truncateText(breadcrumb.label, maxLength)}</span>
            {breadcrumb.type === 'client' && context.client?.id === 'cc92315a-4bae-469d-9550-46d1c6e5ab68' && (
              <Badge variant="secondary" className="ml-1 text-xs px-1 py-0">Demo</Badge>
            )}
          </Button>
          
          {index < breadcrumbs.length - 1 && (
            <ChevronRight className="h-3 w-3 text-gray-400 mx-1" />
          )}
        </React.Fragment>
      ))}
      
      {/* View Mode Indicator */}
      {context.engagement && (
        <>
          <ChevronRight className="h-3 w-3 text-gray-400 mx-1" />
          <div className="flex items-center space-x-1">
            <Eye className="h-3 w-3 text-gray-400" />
            <Badge 
              variant={context.viewMode === 'session_view' ? 'default' : 'secondary'}
              className="text-xs px-2 py-0"
            >
              {context.viewMode === 'session_view' ? 'Session View' : 'Engagement View'}
            </Badge>
          </div>
        </>
      )}
    </nav>
  );
};

export default ContextBreadcrumbs; 