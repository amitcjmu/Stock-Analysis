/**
 * Collection Page Layout Component
 *
 * Shared layout component for collection pages to reduce code duplication
 * and provide consistent layout structure across collection workflow pages.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import { Button } from '@/components/ui/button';

export interface CollectionPageLayoutProps {
  title: string;
  description?: string;
  backUrl?: string;
  backLabel?: string;
  isLoading?: boolean;
  loadingMessage?: string;
  loadingSubMessage?: string;
  headerActions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

/**
 * Shared loading state component
 */
interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
  subMessage
}) => (
  <div className="flex items-center justify-center min-h-64">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
      <p className="text-muted-foreground">{message}</p>
      {subMessage && (
        <p className="text-xs text-muted-foreground mt-2">{subMessage}</p>
      )}
    </div>
  </div>
);

/**
 * Collection page header component
 */
interface CollectionPageHeaderProps {
  title: string;
  description?: string;
  backUrl?: string;
  backLabel?: string;
  headerActions?: React.ReactNode;
}

const CollectionPageHeader: React.FC<CollectionPageHeaderProps> = ({
  title,
  description,
  backUrl = '/collection',
  backLabel = 'Back to Collection',
  headerActions
}) => {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(backUrl)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          {backLabel}
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {description && (
            <p className="text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
      {headerActions && (
        <div className="flex items-center space-x-2">
          {headerActions}
        </div>
      )}
    </div>
  );
};

/**
 * Main collection page layout component
 */
export const CollectionPageLayout: React.FC<CollectionPageLayoutProps> = ({
  title,
  description,
  backUrl,
  backLabel,
  isLoading = false,
  loadingMessage,
  loadingSubMessage,
  headerActions,
  children,
  className = ''
}) => {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className={`container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl ${className}`}>
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {isLoading ? (
            <LoadingState
              message={loadingMessage}
              subMessage={loadingSubMessage}
            />
          ) : (
            <div className="space-y-6">
              <CollectionPageHeader
                title={title}
                description={description}
                backUrl={backUrl}
                backLabel={backLabel}
                headerActions={headerActions}
              />
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CollectionPageLayout;
