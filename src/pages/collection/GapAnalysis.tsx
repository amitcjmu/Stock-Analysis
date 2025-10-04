import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, RefreshCw } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import DataGapDiscovery from '@/components/collection/DataGapDiscovery';

import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/hooks/use-toast';
import { FLOW_PHASE_ROUTES } from '@/config/flowRoutes';

interface CollectionFlowDetails {
  id: string;
  flow_id?: string;
  flow_name?: string;
  status: string;
  current_phase: string;
  progress: number;
  flow_metadata?: {
    selected_asset_ids?: string[];
  };
}

const GapAnalysis: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [flowDetails, setFlowDetails] = useState<CollectionFlowDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isContinuing, setIsContinuing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load flow details on mount
  useEffect(() => {
    if (!flowId) {
      setError('No flow ID provided');
      setIsLoading(false);
      return;
    }

    const loadFlowDetails = async () => {
      try {
        setIsLoading(true);
        // Get flow details from incomplete flows API
        const incompleteFlows = await collectionFlowApi.getIncompleteFlows();
        const flow = incompleteFlows.find(f => f.id === flowId);

        if (!flow) {
          throw new Error('Flow not found');
        }

        setFlowDetails(flow);
      } catch (err: unknown) {
        console.error('Failed to load flow details:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load flow details';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    loadFlowDetails();
  }, [flowId]);

  const handleContinueFlow = async () => {
    if (!flowId) return;

    try {
      setIsContinuing(true);
      await collectionFlowApi.continueFlow(flowId);

      // Get updated flow details
      const updatedFlows = await collectionFlowApi.getIncompleteFlows();
      const updatedFlow = updatedFlows.find(f => f.id === flowId);

      if (updatedFlow && updatedFlow.current_phase) {
        // Navigate to next phase
        const phaseRoute = FLOW_PHASE_ROUTES.collection[updatedFlow.current_phase];
        if (phaseRoute) {
          const route = phaseRoute(flowId);
          navigate(route);
          toast({
            title: "Proceeding to Next Phase",
            description: `Moving to ${updatedFlow.current_phase.replace('_', ' ')} phase...`,
            variant: "default"
          });
          return;
        }
      }

      // Fallback navigation
      navigate(`/collection/progress/${flowId}`);
    } catch (err: unknown) {
      console.error('Failed to continue flow:', err);
      const errorMessage = err instanceof Error ? err.message : "Failed to continue to next phase";
      toast({
        title: "Failed to Continue",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsContinuing(false);
    }
  };

  if (isLoading) {
    return (
      <CollectionPageLayout
        title="Gap Analysis"
        description="Analyzing data collection gaps..."
      >
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mr-2" />
          <span>Loading gap analysis...</span>
        </div>
      </CollectionPageLayout>
    );
  }

  if (error) {
    return (
      <CollectionPageLayout
        title="Gap Analysis"
        description="Data collection gap analysis"
      >
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Gap Analysis</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={() => navigate('/collection')}>
                Return to Collection
              </Button>
            </div>
          </CardContent>
        </Card>
      </CollectionPageLayout>
    );
  }

  // Get selected asset IDs from flow metadata
  const selectedAssetIds = flowDetails?.flow_metadata?.selected_asset_ids || [];

  return (
    <CollectionPageLayout
      title="Gap Analysis - Two-Phase Discovery"
      description={`Data collection gap analysis for ${flowDetails?.flow_name || 'collection flow'}`}
    >
      {flowDetails && flowId && (
        <DataGapDiscovery
          flowId={flowId}
          selectedAssetIds={selectedAssetIds}
          onComplete={handleContinueFlow}
        />
      )}
    </CollectionPageLayout>
  );
};

export default GapAnalysis;
