import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { useAssetInventory } from '@/hooks/useAssetInventory';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const InitializeAssessmentFlow: React.FC = () => {
  const navigate = useNavigate();
  const { initializeFlow, isLoading, error } = useAssessmentFlow();
  const { assets, isLoading: assetsLoading } = useAssetInventory();
  const [selectedApps, setSelectedApps] = useState<string[]>([]);
  const [initializing, setInitializing] = useState(false);

  // Filter assets to show only applications ready for assessment
  const readyApplications = assets?.filter(
    asset => asset.type === 'Application' && asset.ready_for_assessment
  ) || [];

  const handleSelectApp = (appId: string) => {
    setSelectedApps(prev => 
      prev.includes(appId) 
        ? prev.filter(id => id !== appId)
        : [...prev, appId]
    );
  };

  const handleSelectAll = () => {
    if (selectedApps.length === readyApplications.length) {
      setSelectedApps([]);
    } else {
      setSelectedApps(readyApplications.map(app => app.id));
    }
  };

  const handleInitialize = async () => {
    if (selectedApps.length === 0) return;
    
    setInitializing(true);
    try {
      await initializeFlow(selectedApps, false);
      // Navigation will be handled by the hook
    } catch (err) {
      console.error('Failed to initialize assessment flow:', err);
    } finally {
      setInitializing(false);
    }
  };

  if (assetsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Initialize Assessment Flow</h1>
        <p className="text-gray-600">
          Select applications to assess and generate migration strategies
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Select Applications for Assessment</CardTitle>
          <CardDescription>
            Choose which applications you want to include in this assessment flow.
            Only applications marked as "Ready for Assessment" are shown.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {readyApplications.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">
                No applications are ready for assessment.
              </p>
              <Button 
                variant="outline" 
                onClick={() => navigate('/discovery/inventory')}
              >
                Go to Inventory
              </Button>
            </div>
          ) : (
            <>
              <div className="mb-4 flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                >
                  {selectedApps.length === readyApplications.length 
                    ? 'Deselect All' 
                    : 'Select All'}
                </Button>
                <span className="text-sm text-gray-600">
                  {selectedApps.length} of {readyApplications.length} selected
                </span>
              </div>

              <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
                {readyApplications.map(app => (
                  <div
                    key={app.id}
                    className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <Checkbox
                      checked={selectedApps.includes(app.id)}
                      onCheckedChange={() => handleSelectApp(app.id)}
                    />
                    <div className="flex-1">
                      <div className="font-medium">{app.name}</div>
                      <div className="text-sm text-gray-600">
                        {app.metadata?.business_criticality || 'N/A'} criticality • 
                        {app.metadata?.technical_stack?.join(', ') || 'Unknown stack'}
                      </div>
                    </div>
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate('/assess')}
                  disabled={initializing}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleInitialize}
                  disabled={selectedApps.length === 0 || initializing || isLoading}
                >
                  {initializing || isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Initializing...
                    </>
                  ) : (
                    `Start Assessment (${selectedApps.length} apps)`
                  )}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InitializeAssessmentFlow;