import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface InventoryContentFallbackProps {
  error?: string;
  onRetry?: () => void;
}

export const InventoryContentFallback: React.FC<InventoryContentFallbackProps> = ({
  error = "Unable to load inventory data",
  onRetry
}) => {
  return (
    <Card className="min-h-[400px] flex items-center justify-center">
      <CardContent className="text-center space-y-4 py-8">
        <AlertCircle className="h-12 w-12 text-amber-500 mx-auto" />
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Inventory Data Loading Issue
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            {error}
          </p>
          <p className="text-sm text-gray-500">
            The backend service is currently experiencing issues. This may be due to:
          </p>
          <ul className="text-sm text-gray-500 mt-2 space-y-1">
            <li>• Backend service temporarily unavailable</li>
            <li>• Database connection issues</li>
            <li>• Data processing in progress</li>
          </ul>
        </div>
        {onRetry && (
          <Button onClick={onRetry} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
