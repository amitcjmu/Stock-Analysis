import React from 'react';
import { AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SixRStatusAlertProps {
  status: 'processing' | 'error' | 'idle';
  error?: string;
  onRefresh?: () => void;
}

export const SixRStatusAlert: React.FC<SixRStatusAlertProps> = ({ status, error, onRefresh }) => {
  if (status === 'error' && error) {
    return (
      <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
        <AlertCircle className="h-5 w-5 text-red-600" />
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (status === 'processing') {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            <p className="text-sm text-blue-600">
              AI agents are analyzing 6R strategies and component treatments...
            </p>
          </div>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              className="ml-4"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Check Status
            </Button>
          )}
        </div>
      </div>
    );
  }

  return null;
};
