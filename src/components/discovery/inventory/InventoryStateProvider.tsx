import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, AlertCircle, Database, RefreshCw } from 'lucide-react';

interface InventoryStateProviderProps {
  isLoading: boolean;
  isAnalyzing: boolean;
  error: string | null;
  flowStateError: string | null;
  totalAssets: number;
  onTriggerAnalysis: () => void;
  onRetry: () => void;
  children: React.ReactNode;
}

export const InventoryStateProvider: React.FC<InventoryStateProviderProps> = ({
  isLoading,
  isAnalyzing,
  error,
  flowStateError,
  totalAssets,
  onTriggerAnalysis,
  onRetry,
  children
}) => {

  // Loading state - while fetching data
  if (isLoading && !error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <h3 className="text-lg font-semibold mb-2">Loading Asset Inventory</h3>
          <p className="text-gray-600">Fetching asset data and inventory status...</p>
        </div>
      </div>
    );
  }

  // Analyzing state - during crew operations
  if (isAnalyzing) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="relative">
            <Database className="h-12 w-12 mx-auto mb-4 text-green-600" />
            <div className="absolute -top-1 -right-1">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold mb-2">🤖 Inventory Building in Progress</h3>
          <p className="text-gray-600 mb-4">
            CrewAI agents are analyzing and classifying your assets...
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-2">Active Crew Members:</div>
              <ul className="space-y-1 text-left">
                <li>• 🏗️ Inventory Manager - Coordinating classification</li>
                <li>• 🖥️ Server Classification Expert - Analyzing infrastructure</li>
                <li>• 📱 Application Discovery Expert - Identifying applications</li>
                <li>• 🔧 Device Classification Expert - Categorizing devices</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || flowStateError) {
    return (
      <div className="max-w-2xl mx-auto">
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">Failed to load asset inventory</p>
              {error && <p>Error: {error}</p>}
              {flowStateError && <p>Flow Error: {flowStateError}</p>}
            </div>
          </AlertDescription>
        </Alert>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <Database className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Cannot Load Inventory</h3>
              <p className="text-gray-600 mb-6">
                We encountered an error while loading your asset inventory. This might be due to:
              </p>
              <ul className="text-left space-y-2 mb-6 text-sm text-gray-600">
                <li>• Network connectivity issues</li>
                <li>• Database connection problems</li>
                <li>• Invalid session or authentication</li>
                <li>• CrewAI service unavailability</li>
              </ul>
              <div className="flex gap-3 justify-center">
                <Button onClick={onRetry} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry Loading
                </Button>
                <Button onClick={onTriggerAnalysis}>
                  <Database className="h-4 w-4 mr-2" />
                  Trigger New Analysis
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No data state
  if (!isLoading && totalAssets === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <Database className="h-16 w-16 mx-auto mb-6 text-gray-300" />
              <h3 className="text-xl font-semibold mb-3">No Assets Discovered</h3>
              <p className="text-gray-600 mb-6">
                Your asset inventory is empty. This could be because:
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="text-sm text-blue-800 text-left">
                  <div className="font-medium mb-2">Possible Reasons:</div>
                  <ul className="space-y-1">
                    <li>• Data cleansing phase hasn't been completed yet</li>
                    <li>• Field mapping phase had issues with data classification</li>
                    <li>• No CMDB data was uploaded in previous phases</li>
                    <li>• Inventory building crew hasn't been triggered</li>
                  </ul>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <div className="text-sm text-green-800 text-left">
                  <div className="font-medium mb-2">🤖 What the Inventory Building Crew Does:</div>
                  <ul className="space-y-1">
                    <li>• Classifies assets into servers, applications, devices, and databases</li>
                    <li>• Analyzes infrastructure relationships and hosting patterns</li>
                    <li>• Builds comprehensive asset inventory for migration planning</li>
                    <li>• Prepares data for dependency analysis phase</li>
                  </ul>
                </div>
              </div>

              <Button onClick={onTriggerAnalysis} size="lg" className="mb-4">
                <Database className="h-5 w-5 mr-2" />
                Start Inventory Building Analysis
              </Button>

              <p className="text-xs text-gray-500">
                This will trigger the CrewAI Inventory Building Crew to analyze and classify your assets
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Success state - render children
  return <>{children}</>;
};
