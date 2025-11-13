import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ApplicationDeduplicationManager } from '@/components/collection/application-input/ApplicationDeduplicationManager';
import { useAuth } from '@/contexts/AuthContext';
import { ApiClient } from '@/services/ApiClient';
import type { CanonicalApplicationSelection } from '@/types/collection/canonical-applications';

const apiClient = ApiClient.getInstance();

interface UnmappedAsset {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  original_application_name?: string;
}

interface AssetResolutionBannerProps {
  flowId: string;
}

/**
 * AssetResolutionBanner Component
 *
 * Minimal banner that shows unmapped assets from collection flow and reuses
 * existing ApplicationDeduplicationManager component in a modal.
 *
 * Auto-hides when no unmapped assets exist.
 * Per docs/planning/dependency-to-assessment/README.md lines 184-234
 */
export const AssetResolutionBanner: React.FC<AssetResolutionBannerProps> = ({ flowId }) => {
  const { client, engagement, user } = useAuth();
  const queryClient = useQueryClient();
  const [showManager, setShowManager] = useState(false);
  const [selectedApplications, setSelectedApplications] = useState<CanonicalApplicationSelection[]>([]);

  // Query unmapped assets from collection API
  const { data: unmappedAssets, isLoading, refetch } = useQuery({
    queryKey: ['unmapped-assets', flowId, client?.id, engagement?.id],
    queryFn: async (): Promise<UnmappedAsset[]> => {
      if (!client?.id || !engagement?.id || !user?.id) {
        console.warn('AssetResolutionBanner: Missing client/engagement/user context');
        return [];
      }

      try {
        // Bug #628 Fix: Use ApiClient with multi-tenant headers instead of raw fetch()
        // Bug #801 Fix: Add X-User-ID header required by RequestContextEnforcementMiddleware
        // This ensures proper authentication and multi-tenant security headers are included
        const data = await apiClient.get<UnmappedAsset[]>(
          `/collection/assessment/${flowId}/unmapped-assets`,
          {
            headers: {
              'X-Client-Account-Id': client.id.toString(),
              'X-Engagement-Id': engagement.id.toString(),
              'X-User-ID': user.id.toString(),
            }
          }
        );

        return Array.isArray(data) ? data : [];
      } catch (error: any) {
        // Handle 404/401 gracefully by hiding banner
        if (error?.response?.status === 404 || error?.response?.status === 401) {
          console.warn(`Unmapped assets endpoint returned ${error.response.status} - hiding banner`);
          return [];
        }
        console.error('Failed to fetch unmapped assets:', error);
        // Return empty array on error to hide banner gracefully
        return [];
      }
    },
    enabled: !!flowId && !!client?.id && !!engagement?.id && !!user?.id,
    staleTime: 30000, // 30s cache
    // Bug #730 fix - Remove automatic polling, use manual refresh instead
    refetchInterval: false,
  });

  const handleComplete = async () => {
    // Close modal
    setShowManager(false);

    // Invalidate queries to refresh assessment applications
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ['unmapped-assets', flowId],
      }),
      queryClient.invalidateQueries({
        queryKey: ['assessment-applications', flowId],
      }),
    ]);
  };

  // Auto-hide if no unmapped assets
  if (isLoading) return null;
  if (!unmappedAssets || unmappedAssets.length === 0) return null;

  return (
    <>
      <Card className="mb-6 border-amber-200 bg-amber-50">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-amber-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-amber-900">
                Asset Resolution Required
              </h3>
              <p className="mt-1 text-sm text-amber-800">
                Found <span className="font-semibold">{unmappedAssets.length}</span> asset
                {unmappedAssets.length > 1 ? 's' : ''} that need to be mapped to applications before
                proceeding with assessment.
              </p>
              <p className="mt-1 text-xs text-amber-700">
                Use the deduplication manager to link assets to canonical applications or create new
                applications as needed.
              </p>
              <div className="mt-3 flex gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setShowManager(true)}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  Resolve {unmappedAssets.length} Asset{unmappedAssets.length > 1 ? 's' : ''}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span className="ml-2">Refresh</span>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal with ApplicationDeduplicationManager */}
      <Dialog open={showManager} onOpenChange={setShowManager}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Resolve Asset to Application Mappings</DialogTitle>
            <DialogDescription>
              Map the {unmappedAssets.length} selected asset{unmappedAssets.length > 1 ? 's' : ''} to
              canonical applications. Search for existing applications or create new ones.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4">
            {/* Reuse existing ApplicationDeduplicationManager component */}
            <ApplicationDeduplicationManager
              collectionFlowId={flowId}
              initialApplications={selectedApplications}
              onApplicationsChange={setSelectedApplications}
              showBulkImport={false}
              showExportOptions={false}
            />
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowManager(false)}>
              Close
            </Button>
            <Button
              variant="default"
              onClick={handleComplete}
              disabled={selectedApplications.length === 0}
            >
              Complete Resolution ({selectedApplications.length} mapped)
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
