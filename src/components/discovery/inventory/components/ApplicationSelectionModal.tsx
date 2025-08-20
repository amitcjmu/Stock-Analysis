import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2, AlertCircle, Cpu } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import type { Asset } from '@/types/asset';

interface ApplicationSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  flowId?: string;
  preSelectedApplicationIds?: string[];
  existingCollectionFlowId?: string; // For connecting to existing collection flows
}

export const ApplicationSelectionModal: React.FC<ApplicationSelectionModalProps> = ({
  isOpen,
  onClose,
  flowId,
  preSelectedApplicationIds = [],
  existingCollectionFlowId
}) => {
  const navigate = useNavigate();
  const { client, engagement } = useAuth();
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(new Set(preSelectedApplicationIds));
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);

  // Update selected applications when pre-selected IDs change
  useEffect(() => {
    if (preSelectedApplicationIds && preSelectedApplicationIds.length > 0) {
      setSelectedApplications(new Set(preSelectedApplicationIds));
    }
  }, [preSelectedApplicationIds]);

  // Fetch applications from the inventory
  const { data: applications, isLoading } = useQuery({
    queryKey: ['applications-for-collection', client?.id, engagement?.id],
    queryFn: async () => {
      const response = await apiCall('/assets/list/paginated?page=1&page_size=100');

      // Filter only application assets (case-insensitive)
      const apps = (response?.assets || []).filter(
        (asset: Asset) => asset.asset_type?.toLowerCase() === 'application'
      );

      return apps;
    },
    enabled: isOpen && !!client && !!engagement
  });

  // Handle application selection
  const handleToggleApplication = (appId: string) => {
    const newSelection = new Set(selectedApplications);
    if (newSelection.has(appId)) {
      newSelection.delete(appId);
    } else {
      newSelection.add(appId);
    }
    setSelectedApplications(newSelection);
  };

  // Handle select all
  const handleSelectAll = () => {
    if (applications) {
      if (selectedApplications.size === applications.length) {
        setSelectedApplications(new Set());
      } else {
        setSelectedApplications(new Set(applications.map((app: Asset) => app.id)));
      }
    }
  };

  // Handle transition to Collection flow
  const handleProcessForAssessment = async () => {
    if (selectedApplications.size === 0) return;

    setIsTransitioning(true);
    setTransitionError(null);

    try {
      let response;

      if (existingCollectionFlowId) {
        // Update existing collection flow with selected applications
        console.log('🔄 Updating existing Collection flow:', existingCollectionFlowId);

        response = await apiCall(`/collection/flows/${existingCollectionFlowId}`, {
          method: 'PUT',
          body: JSON.stringify({
            action: 'update_applications',
            collection_config: {
              selected_application_ids: Array.from(selectedApplications),
              discovery_flow_id: flowId,
              updated_at: new Date().toISOString()
            }
          })
        });

        // Validate response before navigation
        if (response && (response.id || response.status === 'success')) {
          console.log('✅ Collection flow updated successfully');
          navigate(`/collection?flowId=${existingCollectionFlowId}`);
          onClose();
        } else {
          throw new Error('Failed to update Collection flow - invalid response');
        }
      } else {
        // Create new Collection flow from Discovery
        console.log('➕ Creating new Collection flow from Discovery');

        response = await apiCall('/collection/flows/from-discovery', {
          method: 'POST',
          body: JSON.stringify({
            discovery_flow_id: flowId,
            selected_application_ids: Array.from(selectedApplications),
            collection_strategy: {
              start_phase: 'gap_analysis',
              automation_tier: 'inherited',
              priority: 'critical_gaps_first'
            }
          })
        });

        if (response && response.id) {
          console.log('✅ Collection flow created successfully');
          navigate(`/collection?flowId=${response.id}`);
          onClose();
        } else {
          throw new Error('Failed to create Collection flow - invalid response');
        }
      }
    } catch (error) {
      console.error('❌ Error processing Collection flow:', error);
      setTransitionError(
        error instanceof Error
          ? error.message
          : 'Failed to process Collection flow. Please try again.'
      );
    } finally {
      setIsTransitioning(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            {existingCollectionFlowId
              ? 'Update Collection Flow Applications'
              : preSelectedApplicationIds.length > 0
              ? `Process ${preSelectedApplicationIds.length} Selected Application${preSelectedApplicationIds.length > 1 ? 's' : ''} for Assessment`
              : 'Select Applications for Assessment'}
          </DialogTitle>
          <DialogDescription>
            {existingCollectionFlowId
              ? 'Select applications for your existing Collection flow. This will enable questionnaire generation and gap analysis.'
              : preSelectedApplicationIds.length > 0
              ? 'The following applications have been selected from your inventory. You can modify the selection before processing.'
              : 'Choose which applications you want to process for detailed migration assessment.'}
            The selected applications will undergo gap analysis and data collection.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Loading applications...</span>
            </div>
          ) : applications && applications.length > 0 ? (
            <>
              {/* Select All Checkbox */}
              <div className="mb-4 pb-3 border-b">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <Checkbox
                    checked={selectedApplications.size === applications.length}
                    onCheckedChange={handleSelectAll}
                  />
                  <span className="font-medium">
                    Select All ({applications.length} applications)
                  </span>
                </label>
              </div>

              {/* Application List */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {applications.map((app: Asset) => (
                  <div
                    key={app.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                  >
                    <label className="flex items-center space-x-3 cursor-pointer flex-1">
                      <Checkbox
                        checked={selectedApplications.has(app.id)}
                        onCheckedChange={() => handleToggleApplication(app.id)}
                      />
                      <div className="flex-1">
                        <div className="font-medium">{app.name}</div>
                        {app.environment && (
                          <div className="text-sm text-gray-600">
                            Environment: {app.environment}
                          </div>
                        )}
                      </div>
                    </label>
                    <div className="flex items-center gap-2">
                      {app.criticality && (
                        <Badge
                          variant={
                            app.criticality === 'High' ? 'destructive' :
                            app.criticality === 'Medium' ? 'secondary' :
                            'default'
                          }
                        >
                          {app.criticality}
                        </Badge>
                      )}
                      {app.six_r_strategy && (
                        <Badge variant="outline">
                          {app.six_r_strategy}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Selection Summary */}
              {selectedApplications.size > 0 && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900">
                      {selectedApplications.size} application{selectedApplications.size > 1 ? 's' : ''} selected for assessment
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No applications found in the inventory. Please complete the Discovery flow first.
              </AlertDescription>
            </Alert>
          )}

          {/* Error Alert */}
          {transitionError && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{transitionError}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isTransitioning}
          >
            Cancel
          </Button>
          <Button
            onClick={handleProcessForAssessment}
            disabled={selectedApplications.size === 0 || isTransitioning}
          >
            {isTransitioning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Collection Flow...
              </>
            ) : (
              <>
                Process {selectedApplications.size} Application{selectedApplications.size !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
