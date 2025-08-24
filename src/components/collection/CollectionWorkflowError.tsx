/**
 * Collection Workflow Error Component
 *
 * Provides comprehensive error handling and user feedback for collection workflow issues.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, ArrowLeft, Clock, Wifi, WifiOff } from 'lucide-react';

interface CollectionWorkflowErrorProps {
  error: Error;
  flowId?: string | null;
  isWebSocketActive?: boolean;
  onRetry?: () => void;
  onRefresh?: () => void;
  className?: string;
}

interface ErrorInfo {
  title: string;
  description: string;
  actions: Array<{
    label: string;
    variant: 'default' | 'outline' | 'destructive';
    onClick: () => void;
    icon?: React.ReactNode;
  }>;
  severity: 'warning' | 'error' | 'info';
  showDetails?: boolean;
}

export const CollectionWorkflowError: React.FC<CollectionWorkflowErrorProps> = ({
  error,
  flowId,
  isWebSocketActive = false,
  onRetry,
  onRefresh,
  className = ''
}) => {
  const navigate = useNavigate();

  // Categorize error and provide appropriate response
  const getErrorInfo = (): ErrorInfo => {
    const errorMessage = error.message?.toLowerCase() || '';

    // Timeout errors - allow retry with fallback
    if (errorMessage.includes('timeout') || errorMessage.includes('initialization timeout')) {
      return {
        title: 'Collection Initialization Timed Out',
        description: 'The collection workflow initialization took longer than expected (10+ seconds). This may be due to heavy system load or agents processing complex requirements.',
        actions: [
          {
            label: 'Try Again',
            variant: 'default',
            onClick: () => onRetry?.(),
            icon: <RefreshCw className="h-4 w-4" />
          },
          {
            label: 'Use Simple Form',
            variant: 'outline',
            onClick: () => navigate('/collection/simple-form')
          },
          {
            label: 'View All Workflows',
            variant: 'outline',
            onClick: () => navigate('/collection')
          }
        ],
        severity: 'warning',
        showDetails: true
      };
    }

    // Permission/Auth errors - clear action needed
    if (errorMessage.includes('permission') || errorMessage.includes('auth')) {
      return {
        title: 'Permission Denied',
        description: 'You do not have the required permissions to create collection flows. Contact your administrator to request access.',
        actions: [
          {
            label: 'Go Back',
            variant: 'outline',
            onClick: () => navigate(-1),
            icon: <ArrowLeft className="h-4 w-4" />
          },
          {
            label: 'View Collection Overview',
            variant: 'outline',
            onClick: () => navigate('/collection')
          }
        ],
        severity: 'error'
      };
    }

    // Conflict errors - multiple flows
    if (errorMessage.includes('409') || errorMessage.includes('conflict') || errorMessage.includes('multiple active')) {
      return {
        title: 'Active Collection Flow Exists',
        description: 'Another collection flow is already active. Please complete or cancel the existing flow before starting a new one.',
        actions: [
          {
            label: 'Manage Existing Flows',
            variant: 'default',
            onClick: () => navigate('/collection/progress')
          },
          {
            label: 'View Collection Overview',
            variant: 'outline',
            onClick: () => navigate('/collection')
          }
        ],
        severity: 'warning'
      };
    }

    // Server errors - likely backend issue
    if (errorMessage.includes('500') || errorMessage.includes('server error')) {
      return {
        title: 'Server Error',
        description: 'The collection service is currently experiencing issues. Please try again in a few minutes or contact support if the problem persists.',
        actions: [
          {
            label: 'Refresh Page',
            variant: 'default',
            onClick: () => onRefresh?.() || window.location.reload(),
            icon: <RefreshCw className="h-4 w-4" />
          },
          {
            label: 'Go Back',
            variant: 'outline',
            onClick: () => navigate(-1),
            icon: <ArrowLeft className="h-4 w-4" />
          }
        ],
        severity: 'error'
      };
    }

    // Network/connectivity errors
    if (errorMessage.includes('network') || errorMessage.includes('fetch') || !navigator.onLine) {
      return {
        title: 'Connection Issue',
        description: 'Unable to connect to the collection service. Please check your internet connection and try again.',
        actions: [
          {
            label: 'Retry Connection',
            variant: 'default',
            onClick: () => onRetry?.(),
            icon: <RefreshCw className="h-4 w-4" />
          },
          {
            label: 'Work Offline',
            variant: 'outline',
            onClick: () => navigate('/collection/offline')
          }
        ],
        severity: 'warning'
      };
    }

    // Questionnaire/form generation errors - provide fallback
    if (errorMessage.includes('questionnaire') || errorMessage.includes('form')) {
      return {
        title: 'Form Generation Failed',
        description: 'Unable to generate the adaptive collection form. You can use a standard form template instead.',
        actions: [
          {
            label: 'Use Standard Form',
            variant: 'default',
            onClick: () => navigate('/collection/standard-form')
          },
          {
            label: 'Try Again',
            variant: 'outline',
            onClick: () => onRetry?.(),
            icon: <RefreshCw className="h-4 w-4" />
          }
        ],
        severity: 'warning',
        showDetails: true
      };
    }

    // Generic/unknown errors
    return {
      title: 'Collection Workflow Error',
      description: 'An unexpected error occurred while initializing the collection workflow. Please try again or contact support if the issue persists.',
      actions: [
        {
          label: 'Try Again',
          variant: 'default',
          onClick: () => onRetry?.(),
          icon: <RefreshCw className="h-4 w-4" />
        },
        {
          label: 'Go Back',
          variant: 'outline',
          onClick: () => navigate(-1),
          icon: <ArrowLeft className="h-4 w-4" />
        },
        {
          label: 'Refresh Page',
          variant: 'outline',
          onClick: () => onRefresh?.() || window.location.reload()
        }
      ],
      severity: 'error',
      showDetails: true
    };
  };

  const errorInfo = getErrorInfo();

  return (
    <div className={`max-w-2xl mx-auto mt-8 ${className}`}>
      <Alert className={`border-2 ${
        errorInfo.severity === 'error'
          ? 'border-red-200 bg-red-50'
          : errorInfo.severity === 'warning'
          ? 'border-yellow-200 bg-yellow-50'
          : 'border-blue-200 bg-blue-50'
      }`}>
        <AlertTriangle className={`h-5 w-5 ${
          errorInfo.severity === 'error'
            ? 'text-red-600'
            : errorInfo.severity === 'warning'
            ? 'text-yellow-600'
            : 'text-blue-600'
        }`} />
        <AlertDescription>
          <div className="space-y-4">
            {/* Error Header */}
            <div>
              <h3 className={`text-lg font-semibold ${
                errorInfo.severity === 'error'
                  ? 'text-red-800'
                  : errorInfo.severity === 'warning'
                  ? 'text-yellow-800'
                  : 'text-blue-800'
              }`}>
                {errorInfo.title}
              </h3>
              <p className={`mt-2 ${
                errorInfo.severity === 'error'
                  ? 'text-red-700'
                  : errorInfo.severity === 'warning'
                  ? 'text-yellow-700'
                  : 'text-blue-700'
              }`}>
                {errorInfo.description}
              </p>
            </div>

            {/* Connection Status */}
            {flowId && (
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                {isWebSocketActive ? (
                  <>
                    <Wifi className="h-4 w-4 text-green-600" />
                    <span>Real-time updates active</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4 text-gray-500" />
                    <span>Polling for updates</span>
                  </>
                )}
                <span>•</span>
                <Clock className="h-4 w-4" />
                <span>Flow ID: {flowId.slice(0, 8)}...</span>
              </div>
            )}

            {/* Technical Details (for development/debugging) */}
            {errorInfo.showDetails && process.env.NODE_ENV === 'development' && (
              <details className="mt-4">
                <summary className={`text-sm cursor-pointer ${
                  errorInfo.severity === 'error'
                    ? 'text-red-600'
                    : errorInfo.severity === 'warning'
                    ? 'text-yellow-600'
                    : 'text-blue-600'
                }`}>
                  Technical Details (Development)
                </summary>
                <pre className={`text-xs mt-2 overflow-auto p-2 rounded ${
                  errorInfo.severity === 'error'
                    ? 'bg-red-100 text-red-700'
                    : errorInfo.severity === 'warning'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-blue-100 text-blue-700'
                }`}>
                  {error.message}
                  {error.cause && `\n\nCause: ${error.cause.toString()}`}
                  {error.stack && `\n\nStack: ${error.stack}`}
                </pre>
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              {errorInfo.actions.map((action) => (
                <Button
                  key={action.label}
                  variant={action.variant}
                  onClick={action.onClick}
                  className="flex items-center space-x-1"
                >
                  {action.icon}
                  <span>{action.label}</span>
                </Button>
              ))}
            </div>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default CollectionWorkflowError;
