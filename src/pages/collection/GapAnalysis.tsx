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
  collection_config?: {
    selected_application_ids?: string[];
  };
  metadata?: {
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
        // Get flow details directly by ID (works for all phases including gap_analysis)
        const flow = await collectionFlowApi.getFlow(flowId);

        if (!flow) {
          throw new Error('Flow not found');
        }

        setFlowDetails(flow);
      } catch (err: unknown) {
        console.error('Failed to load flow details:', err);

        // Bug #799 Fix: Enhanced error handling based on error type
        let errorMessage = 'Failed to load flow details';

        if (err instanceof Error) {
          const msg = err.message.toLowerCase();
          if (msg.includes('404') || msg.includes('not found')) {
            errorMessage = `Collection flow not found (ID: ${flowId}). The flow may have been deleted or the URL is invalid.`;
          } else if (msg.includes('403') || msg.includes('unauthorized') || msg.includes('forbidden')) {
            errorMessage = 'You do not have permission to access this collection flow.';
          } else if (msg.includes('500') || msg.includes('server error')) {
            errorMessage = 'Server error while loading flow. Please try again or contact support.';
          } else {
            errorMessage = err.message;
          }
        }

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

      // Call continueFlow and use the response to get the correct flow_id and next phase
      const continueResult = await collectionFlowApi.continueFlow(flowId);

      console.log('📋 Continue flow result:', continueResult);

      // CRITICAL FIX: Use the flow_id from the response instead of refetching
      // The response includes current_phase and flow_id (may differ from input flowId)
      const responseFlowId = continueResult.flow_id || flowId;
      const currentPhase = continueResult.current_phase;

      if (currentPhase) {
        // Navigate to next phase using the flow_id from the response
        const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];
        if (phaseRoute) {
          const route = phaseRoute(responseFlowId);
          console.log(`🔄 Navigating to ${currentPhase} phase with flow ID ${responseFlowId}: ${route}`);
          navigate(route);
          toast({
            title: "Proceeding to Next Phase",
            description: `Moving to ${currentPhase.replace('_', ' ')} phase...`,
            variant: "default"
          });
          return;
        }
      }

      // Fallback navigation
      console.warn('⚠️ No phase route found, using fallback navigation');
      navigate(`/collection/progress/${responseFlowId}`);
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

  // Get selected asset IDs from collection_config (for backward compat, also try metadata)
  const selectedAssetIds =
    flowDetails?.collection_config?.selected_application_ids ||
    flowDetails?.metadata?.selected_asset_ids ||
    [];

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
