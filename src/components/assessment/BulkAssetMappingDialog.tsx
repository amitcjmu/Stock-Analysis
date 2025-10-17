/**
 * Bulk Asset Mapping Dialog Component
 *
 * Allows users to map multiple unmapped assets to canonical applications in bulk.
 * Integrated into Assessment Application Resolver workflow.
 *
 * Features:
 * - Searchable canonical application dropdown
 * - Asset multi-select with checkboxes
 * - In-line confirmation with toast notifications
 * - Auto-refresh ApplicationGroupsWidget after successful mapping
 *
 * Phase 2.2 Implementation - Assessment Canonical Grouping Remediation
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Check, X, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { canonicalApplicationsApi } from '@/services/api/canonical-applications';
import { apiCall } from '@/config/api';
import type { CanonicalApplication } from '@/types/collection/canonical-applications';

interface UnmappedAsset {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  technology_stack?: string[];
}

interface BulkAssetMappingDialogProps {
  unmappedAssets: UnmappedAsset[];
  onComplete: () => void;
  onCancel: () => void;
}

interface BulkMappingRequest {
  mappings: Array<{
    asset_id: string;
    canonical_application_id: string;
  }>;
  collection_flow_id?: string;
}

interface BulkMappingResponse {
  total_requested: number;
  successfully_mapped: number;
  already_mapped: number;
  errors: Array<{
    asset_id: string;
    error: string;
  }>;
}

export const BulkAssetMappingDialog: React.FC<BulkAssetMappingDialogProps> = ({
  unmappedAssets,
  onComplete,
  onCancel,
}) => {
  const { client, engagement } = useAuth();
  const queryClient = useQueryClient();

  // State
  const [selectedCanonicalAppId, setSelectedCanonicalAppId] = useState<string | null>(null);
  const [selectedAssetIds, setSelectedAssetIds] = useState<Set<string>>(new Set());
  const [mappingResults, setMappingResults] = useState<Record<string, 'success' | 'error'>>({});

  // Query canonical applications
  const { data: canonicalAppsData, isLoading: isLoadingApps } = useQuery({
    queryKey: ['canonical-applications', client?.id, engagement?.id],
    queryFn: async () => {
      return await canonicalApplicationsApi.getCanonicalApplications({
        limit: 100,
        include_variants: false,
        include_history: false,
      });
    },
    enabled: !!client?.id && !!engagement?.id,
  });

  const canonicalApps = canonicalAppsData?.applications || [];

  // Bulk mapping mutation
  const bulkMapMutation = useMutation({
    mutationFn: async (request: BulkMappingRequest) => {
      const response = await apiCall('/api/v1/canonical-applications/bulk-map-assets', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return response as BulkMappingResponse;
    },
    onSuccess: (data) => {
      console.log('[BulkMapping] Completed:', data);

      // Show in-line confirmation
      const results: Record<string, 'success' | 'error'> = {};

      // Mark successful mappings
      Array.from(selectedAssetIds).forEach(assetId => {
        const hasError = data.errors.find(e => e.asset_id === assetId);
        results[assetId] = hasError ? 'error' : 'success';
      });

      setMappingResults(results);

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['assessment-applications'] });
      queryClient.invalidateQueries({ queryKey: ['flow-status'] });

      // Auto-close after 2 seconds if all successful
      if (data.errors.length === 0) {
        setTimeout(() => {
          onComplete();
        }, 2000);
      }
    },
    onError: (error) => {
      console.error('[BulkMapping] Failed:', error);
      alert(`Mapping failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Handlers
  const handleToggleAsset = (assetId: string) => {
    setSelectedAssetIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(assetId)) {
        newSet.delete(assetId);
      } else {
        newSet.add(assetId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedAssetIds.size === unmappedAssets.length) {
      setSelectedAssetIds(new Set());
    } else {
      setSelectedAssetIds(new Set(unmappedAssets.map(a => a.asset_id)));
    }
  };

  const handleBulkMap = async () => {
    if (!selectedCanonicalAppId || selectedAssetIds.size === 0) {
      return;
    }

    const mappings = Array.from(selectedAssetIds).map(asset_id => ({
      asset_id,
      canonical_application_id: selectedCanonicalAppId,
    }));

    await bulkMapMutation.mutateAsync({ mappings });
  };

  // Computed values
  const selectedCanonicalApp = useMemo(() => {
    return canonicalApps.find(app => app.id === selectedCanonicalAppId);
  }, [canonicalApps, selectedCanonicalAppId]);

  const hasResults = Object.keys(mappingResults).length > 0;
  const isSubmitDisabled = !selectedCanonicalAppId || selectedAssetIds.size === 0 || bulkMapMutation.isPending || hasResults;

  return (
    <Dialog open onOpenChange={onCancel}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Map Unmapped Assets to Canonical Application</DialogTitle>
          <DialogDescription>
            Select a canonical application and choose which assets to map. Assets will be grouped by canonical application in the assessment.
          </DialogDescription>
        </DialogHeader>

        {/* Canonical App Selector */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Canonical Application <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedCanonicalAppId || ''}
              onChange={(e) => setSelectedCanonicalAppId(e.target.value || null)}
              disabled={isLoadingApps || hasResults}
              className="w-full border rounded-md px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">Select canonical application...</option>
              {canonicalApps.map((app: CanonicalApplication) => (
                <option key={app.id} value={app.id}>
                  {app.canonical_name}
                  {app.metadata?.business_criticality && ` (${app.metadata.business_criticality})`}
                  {app.metadata?.collection_count > 0 && ` • ${app.metadata.collection_count} collections`}
                </option>
              ))}
            </select>
            {isLoadingApps && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Loading canonical applications...
              </p>
            )}
          </div>

          {/* Selected canonical app info */}
          {selectedCanonicalApp && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-blue-900">{selectedCanonicalApp.canonical_name}</p>
                  {selectedCanonicalApp.description && (
                    <p className="text-blue-700 mt-1">{selectedCanonicalApp.description}</p>
                  )}
                  <div className="flex gap-2 mt-2">
                    {selectedCanonicalApp.metadata?.total_variants > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {selectedCanonicalApp.metadata.total_variants} variants
                      </Badge>
                    )}
                    {selectedCanonicalApp.metadata?.business_criticality && (
                      <Badge
                        variant={selectedCanonicalApp.metadata.business_criticality === 'critical' ? 'destructive' : 'secondary'}
                        className="text-xs"
                      >
                        {selectedCanonicalApp.metadata.business_criticality}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Asset Multi-Select */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">
              Assets to Map ({selectedAssetIds.size} of {unmappedAssets.length} selected)
            </label>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              disabled={hasResults}
              className="text-xs"
            >
              {selectedAssetIds.size === unmappedAssets.length ? 'Deselect All' : 'Select All'}
            </Button>
          </div>

          <div className="border rounded-md divide-y max-h-[400px] overflow-y-auto">
            {unmappedAssets.map((asset) => {
              const isSelected = selectedAssetIds.has(asset.asset_id);
              const result = mappingResults[asset.asset_id];

              return (
                <div
                  key={asset.asset_id}
                  className={`p-3 hover:bg-gray-50 transition-colors ${
                    result === 'success' ? 'bg-green-50 border-green-200' :
                    result === 'error' ? 'bg-red-50 border-red-200' :
                    ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Checkbox */}
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => handleToggleAsset(asset.asset_id)}
                      disabled={hasResults}
                      className="mt-1"
                    />

                    {/* Asset Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold text-sm truncate">{asset.asset_name}</h4>
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          {asset.asset_type}
                        </Badge>

                        {/* Result indicators */}
                        {result === 'success' && (
                          <Badge variant="default" className="bg-green-600 text-xs flex-shrink-0">
                            <Check className="h-3 w-3 mr-1" />
                            Mapped
                          </Badge>
                        )}
                        {result === 'error' && (
                          <Badge variant="destructive" className="text-xs flex-shrink-0">
                            <X className="h-3 w-3 mr-1" />
                            Failed
                          </Badge>
                        )}
                      </div>

                      {/* Technology stack preview */}
                      {asset.technology_stack && asset.technology_stack.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {asset.technology_stack.slice(0, 3).map((tech, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {tech}
                            </Badge>
                          ))}
                          {asset.technology_stack.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{asset.technology_stack.length - 3} more
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {unmappedAssets.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">No unmapped assets to display.</p>
            </div>
          )}
        </div>

        {/* Error Summary */}
        {hasResults && mappingResults && Object.values(mappingResults).some(r => r === 'error') && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-900">
                <p className="font-medium">Some assets failed to map</p>
                <p className="text-red-700 mt-1">
                  Check individual asset errors above and retry if needed.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={onCancel}>
            {hasResults ? 'Close' : 'Cancel'}
          </Button>
          {!hasResults && (
            <Button
              onClick={handleBulkMap}
              disabled={isSubmitDisabled}
            >
              {bulkMapMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Mapping...
                </>
              ) : (
                <>
                  Map {selectedAssetIds.size} Asset{selectedAssetIds.size !== 1 ? 's' : ''} to {selectedCanonicalApp?.canonical_name || 'Application'}
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
