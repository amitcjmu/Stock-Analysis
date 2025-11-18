/**
 * Start Assessment Modal Component
 *
 * Allows users to initialize assessment flows directly from canonical applications,
 * breaking the collection→assessment circular dependency (GPT-5 suggestion).
 *
 * Features:
 * - Three-tab interface: "Ready for Assessment", "Needs Mapping", and "Needs Collection"
 * - Searchable canonical application list across all tabs
 * - Multi-select with visual feedback (ready apps only)
 * - Asset mapping interface for unmapped assets
 * - Readiness status indicators (ready/partial/not-ready)
 * - Actionable guidance for not-ready apps (blockers + recommendations)
 * - Direct navigation to assessment or collection flows
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { useToast } from '@/components/ui/use-toast';

interface CanonicalApplication {
  id: string;
  canonical_name: string;
  application_type?: string;
  business_criticality?: string;
  usage_count: number;
  confidence_score: number;
  is_verified: boolean;

  // Readiness metadata (added per backend API update)
  linked_asset_count: number;
  ready_asset_count: number;
  not_ready_asset_count: number;
  readiness_status: "ready" | "partial" | "not_ready";
  readiness_blockers: string[];
  readiness_recommendations: string[];
}

interface UnmappedAsset {
  is_unmapped_asset: true;
  asset_id: string;
  asset_name: string;
  asset_type: string;
  mapped_to_application_id: string | null;
  mapped_to_application_name: string | null;
  discovery_status: string;
  assessment_readiness: string;
}

type ApplicationOrAsset = CanonicalApplication | UnmappedAsset;

interface CanonicalApplicationsResponse {
  applications: ApplicationOrAsset[];
  total: number;
  canonical_apps_count: number;
  unmapped_assets_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface StartAssessmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  assessmentFlowId?: string; // Optional: If navigating from existing assessment flow
}

type TabType = "ready" | "needs-mapping" | "needs-collection";

// Type guard to check if item is an unmapped asset
function isUnmappedAsset(item: ApplicationOrAsset): item is UnmappedAsset {
  return 'is_unmapped_asset' in item && item.is_unmapped_asset === true;
}

export const StartAssessmentModal: React.FC<StartAssessmentModalProps> = ({
  isOpen,
  onClose,
  assessmentFlowId,
}) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState<TabType>("ready");
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAppIds, setSelectedAppIds] = useState<Set<string>>(new Set());
  const [applications, setApplications] = useState<ApplicationOrAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [startingCollection, setStartingCollection] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [assetMappings, setAssetMappings] = useState<Record<string, string>>({});
  const [mappingInProgress, setMappingInProgress] = useState<string | null>(null);
  const [refreshingReadiness, setRefreshingReadiness] = useState(false);

  // Fetch canonical applications and unmapped assets
  useEffect(() => {
    if (!isOpen || !client?.id || !engagement?.id) return;

    const fetchApplications = async () => {
      // Reset applications state to force fresh data load
      // This prevents stale state from persisting after "Refresh Readiness"
      setApplications([]);
      setLoading(true);
      setError(null);

      try {
        // Add cache-busting timestamp to ensure fresh data from database
        const timestamp = Date.now();
        console.log(`🔄 Fetching applications from DB with timestamp: ${timestamp}`);

        const response = await apiCall<CanonicalApplicationsResponse>(
          `/api/v1/canonical-applications?search=${encodeURIComponent(searchQuery)}&page=1&page_size=100&include_unmapped_assets=true&_t=${timestamp}`,
          {
            method: 'GET',
            headers: {
              'X-Client-Account-ID': client.id,
              'X-Engagement-ID': engagement.id,
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
            },
          }
        );

        console.log(`✅ Fetched ${response.applications.length} applications from database`);
        setApplications(response.applications);
      } catch (err) {
        console.error('Failed to fetch canonical applications:', err);
        setError('Failed to load applications. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, [isOpen, searchQuery, client?.id, engagement?.id]);

  // Filter applications based on search
  const filteredApplications = useMemo(() => {
    if (!searchQuery.trim()) return applications;

    const query = searchQuery.toLowerCase();
    return applications.filter((item) => {
      if (isUnmappedAsset(item)) {
        return item.asset_name.toLowerCase().includes(query);
      }
      return item.canonical_name.toLowerCase().includes(query);
    });
  }, [applications, searchQuery]);

  // Get list of canonical applications for mapping dropdown
  const availableApplications = useMemo(() => {
    return applications.filter(app => !isUnmappedAsset(app)) as CanonicalApplication[];
  }, [applications]);

  // Separate items by tab category
  const readyApplications = useMemo(() => {
    return filteredApplications.filter(item =>
      !isUnmappedAsset(item) &&
      (item.readiness_status === "ready" || item.readiness_status === "partial")
    ) as CanonicalApplication[];
  }, [filteredApplications]);

  const unmappedAssets = useMemo(() => {
    // Show ONLY truly unmapped assets (not already mapped to applications)
    // Once mapped, assets won't appear in this tab
    return filteredApplications.filter(item =>
      isUnmappedAsset(item) &&
      !item.mapped_to_application_id  // Exclude already-mapped assets
    ) as UnmappedAsset[];
  }, [filteredApplications]);

  const notReadyApplications = useMemo(() => {
    return filteredApplications.filter(item =>
      !isUnmappedAsset(item) &&
      item.readiness_status === "not_ready"
    ) as CanonicalApplication[];
  }, [filteredApplications]);

  // Handle app selection toggle
  const toggleAppSelection = (appId: string) => {
    const newSelection = new Set(selectedAppIds);
    if (newSelection.has(appId)) {
      newSelection.delete(appId);
    } else {
      newSelection.add(appId);
    }
    setSelectedAppIds(newSelection);
  };

  // Handle mapping dropdown change
  const handleMappingChange = (assetId: string, appId: string) => {
    setAssetMappings(prev => ({
      ...prev,
      [assetId]: appId
    }));
  };

  // Handle asset mapping to application
  const handleApplyMapping = async (assetId: string) => {
    const appId = assetMappings[assetId];
    if (!appId || !client?.id || !engagement?.id) return;

    setMappingInProgress(assetId);

    try {
      await apiCall('/api/v1/canonical-applications/map-asset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-ID': client.id,
          'X-Engagement-ID': engagement.id,
        },
        body: JSON.stringify({
          asset_id: assetId,
          canonical_application_id: appId,
        }),
      });

      // Clear mapping from state
      setAssetMappings(prev => {
        const newMappings = { ...prev };
        delete newMappings[assetId];
        return newMappings;
      });

      // Refetch applications to update mapping status
      const response = await apiCall<CanonicalApplicationsResponse>(
        `/api/v1/canonical-applications?search=${encodeURIComponent(searchQuery)}&page=1&page_size=100&include_unmapped_assets=true`,
        {
          method: 'GET',
          headers: {
            'X-Client-Account-ID': client.id,
            'X-Engagement-ID': engagement.id,
          },
        }
      );
      setApplications(response.applications);
    } catch (err) {
      console.error('Failed to map asset:', err);
      setError('Failed to map asset. Please try again.');
    } finally {
      setMappingInProgress(null);
    }
  };

  // Handle starting collection for a single application
  const handleStartCollection = async (app: CanonicalApplication) => {
    if (startingCollection) return; // Prevent double-click

    setStartingCollection(app.id);
    try {
      // Bug #1066 Fix: Fetch assessment readiness summary to get SPECIFIC gap fields
      // instead of passing empty missing_attributes
      const missing_attributes: Record<string, string[]> = {};

      if (assessmentFlowId) {
        // If we have an assessment flow context, fetch detailed gap reports
        console.log(`🔍 Fetching readiness summary for assessment flow ${assessmentFlowId}`);

        try {
          const readinessSummary = await apiCall<{asset_reports: any[]}>(
            `/api/v1/assessment-flow/${assessmentFlowId}/readiness-summary?detailed=true`,
            {
              method: 'GET',
              headers: {
                'X-Client-Account-ID': client.id,
                'X-Engagement-ID': engagement.id,
              },
            }
          );

          // Extract SPECIFIC gap fields from assessment analysis (critical and high-priority only)
          if (readinessSummary.asset_reports && readinessSummary.asset_reports.length > 0) {
            for (const report of readinessSummary.asset_reports) {
              // Only include not-ready assets for this specific application
              if (!report.is_ready) {
                const gapFields = [
                  ...(report.critical_gaps || []).map((gap: any) => gap.field_id || gap.field_name),
                  ...(report.high_priority_gaps || []).map((gap: any) => gap.field_id || gap.field_name),
                ].filter(Boolean);

                if (gapFields.length > 0) {
                  missing_attributes[report.asset_id] = gapFields;
                }
              }
            }
          }

          console.log(`✅ Extracted specific gaps for ${Object.keys(missing_attributes).length} assets:`, missing_attributes);
        } catch (error) {
          console.warn('Failed to fetch readiness summary, falling back to asset list:', error);
        }
      }

      // Fallback: If no assessment context or gap fetch failed, use on-demand readiness gap analysis
      if (Object.keys(missing_attributes).length === 0) {
        console.log(`⚠️  No assessment flow context, fetching readiness gaps for canonical app ${app.id}`);

        try {
          const gapsResponse = await apiCall<{
            missing_attributes: Record<string, string[]>;
            asset_count: number;
            not_ready_count: number;
          }>(
            `/api/v1/canonical-applications/${app.id}/readiness-gaps`,
            {
              method: 'GET',
              headers: {
                'X-Client-Account-ID': client.id,
                'X-Engagement-ID': engagement.id,
              },
            }
          );

          // Use the gap fields returned by the backend's readiness analysis
          Object.assign(missing_attributes, gapsResponse.missing_attributes);

          if (gapsResponse.asset_count === 0) {
            toast({
              title: 'No Assets Found',
              description: `No assets found for application "${app.canonical_name}". Please check asset mapping.`,
              variant: 'destructive',
            });
            return;
          }

          console.log(`✅ Fetched readiness gaps for ${gapsResponse.asset_count} assets (${gapsResponse.not_ready_count} not ready):`, missing_attributes);
        } catch (error) {
          console.error('Failed to fetch readiness gaps:', error);
          toast({
            title: 'Gap Analysis Failed',
            description: `Failed to analyze data gaps for "${app.canonical_name}". Please try again.`,
            variant: 'destructive',
          });
          return;
        }
      }

      // Validate that we have something to collect
      if (Object.keys(missing_attributes).length === 0) {
        toast({
          title: 'No Data Gaps',
          description: `Application "${app.canonical_name}" has no missing data requiring collection.`,
          variant: 'default',
        });
        return;
      }

      console.log(`🚀 Starting collection for ${app.canonical_name} with ${Object.keys(missing_attributes).length} assets`);

      // Call ensureFlow with missing_attributes (and assessment_flow_id if available)
      const collectionFlow = await collectionFlowApi.ensureFlow(missing_attributes, assessmentFlowId);

      toast({
        title: 'Collection Flow Started',
        description: `Collection started for ${app.canonical_name} (${Object.keys(missing_attributes).length} assets)`,
      });

      onClose();
      navigate(`/collection/adaptive-forms?flowId=${collectionFlow.flow_id || collectionFlow.id}`);

    } catch (error: any) {
      console.error('Failed to start collection:', error);
      toast({
        title: 'Collection Start Failed',
        description: error?.message || 'Failed to start collection flow. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setStartingCollection(null);
    }
  };

  // Handle refreshing readiness status for all applications
  const handleRefreshReadiness = async () => {
    if (refreshingReadiness || !client?.id || !engagement?.id) return;

    setRefreshingReadiness(true);
    try {
      console.log('🔄 Refreshing readiness status for all applications...');

      // Get only canonical applications (not unmapped assets)
      const canonicalApps = applications.filter(
        (item): item is CanonicalApplication => !isUnmappedAsset(item)
      );

      if (canonicalApps.length === 0) {
        toast({
          title: 'No Applications',
          description: 'No applications to refresh readiness for.',
          variant: 'default',
        });
        return;
      }

      // Call readiness-gaps endpoint for each application to get live status
      // IMPORTANT: Pass update_database=true to persist results to Asset.assessment_readiness
      const refreshPromises = canonicalApps.map(async (app) => {
        try {
          const gapsResponse = await apiCall<{
            missing_attributes: Record<string, string[]>;
            asset_count: number;
            not_ready_count: number;
            updated_count?: number;
          }>(
            `/api/v1/canonical-applications/${app.id}/readiness-gaps?update_database=true`,
            {
              method: 'GET',
              headers: {
                'X-Client-Account-ID': client.id,
                'X-Engagement-ID': engagement.id,
              },
            }
          );

          // Update readiness status based on live gap analysis
          const hasGaps = gapsResponse.not_ready_count > 0;
          const newReadinessStatus: "ready" | "partial" | "not_ready" =
            hasGaps ? "not_ready" : "ready";

          return {
            ...app,
            not_ready_asset_count: gapsResponse.not_ready_count,
            ready_asset_count: gapsResponse.asset_count - gapsResponse.not_ready_count,
            readiness_status: newReadinessStatus,
            // Preserve updated_count for database update tracking
            updated_count: gapsResponse.updated_count || 0,
          };
        } catch (error) {
          console.error(`Failed to refresh readiness for ${app.canonical_name}:`, error);
          // Return original app data if refresh fails (with 0 updates)
          return { ...app, updated_count: 0 };
        }
      });

      const refreshedApps = await Promise.all(refreshPromises);

      // Update applications state with refreshed readiness data
      setApplications((prev) =>
        prev.map((item) => {
          if (isUnmappedAsset(item)) return item;
          const refreshed = refreshedApps.find((app) => app.id === item.id);
          return refreshed || item;
        })
      );

      // Calculate total database updates (sum of updated_count from all responses)
      const totalDbUpdates = refreshedApps.reduce((sum, app) => {
        const response = app as any;
        return sum + (response.updated_count || 0);
      }, 0);

      toast({
        title: 'Readiness Refreshed',
        description: `Updated readiness status for ${canonicalApps.length} applications (${totalDbUpdates} assets persisted to database).`,
      });

      console.log(`✅ Refreshed readiness for ${canonicalApps.length} applications (${totalDbUpdates} DB updates)`);
    } catch (error: any) {
      console.error('Failed to refresh readiness:', error);
      toast({
        title: 'Refresh Failed',
        description: error?.message || 'Failed to refresh readiness status. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setRefreshingReadiness(false);
    }
  };

  // Handle assessment creation
  const handleCreateAssessment = async () => {
    if (selectedAppIds.size === 0) {
      setError('Please select at least one application');
      return;
    }

    if (!client?.id || !engagement?.id || !user?.id) {
      setError('Missing authentication context');
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const response = await apiCall(
        '/api/v1/master-flows/new/assessment/initialize-from-canonical',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Client-Account-ID': client.id,
            'X-Engagement-ID': engagement.id,
            'X-User-ID': user.id,
          },
          body: JSON.stringify({
            canonical_application_ids: Array.from(selectedAppIds),
          }),
        }
      );

      // Navigate to new assessment flow - directly to architecture phase
      // Per Bug #999 investigation: Navigate to first phase instead of overview page
      // Overview page has no "Start Assessment" button, causing users to get stuck
      const flowId = response.flow_id;
      navigate(`/assessment/${flowId}/architecture`);
      onClose();
    } catch (err: any) {
      console.error('Failed to create assessment:', err);

      // Extract detailed error from backend response
      // FastAPI HTTPException wraps errors in a 'detail' property
      // Backend returns: detail: { error: string, message: string, action: string }
      if (err.response?.detail) {
        const errorData = err.response.detail;

        if (errorData.error && errorData.message) {
          // Build user-friendly error message with guidance
          const errorParts = [errorData.message];
          if (errorData.action) {
            errorParts.push(errorData.action);
          }
          setError(errorParts.join('\n\n'));
        } else if (errorData.message) {
          // Fallback if only message exists
          setError(errorData.message);
        } else if (typeof errorData === 'string') {
          // Detail is a plain string
          setError(errorData);
        } else {
          // Last resort fallback
          setError(err.message || 'Failed to create assessment. Please try again.');
        }
      } else if (err.response?.message) {
        // Some endpoints return message directly
        setError(err.response.message);
      } else {
        // No structured response - use generic error
        setError(err.message || 'Failed to create assessment. Please try again.');
      }
    } finally {
      setCreating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Start New Assessment
              </h2>
              <p className="mt-1 text-sm text-gray-600">
                Select one or more canonical applications to assess
              </p>
            </div>
            <button
              onClick={handleRefreshReadiness}
              disabled={refreshingReadiness || loading}
              className="ml-4 px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              title="Refresh readiness status using live gap analysis"
            >
              <svg
                className={`h-4 w-4 ${refreshingReadiness ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {refreshingReadiness ? 'Refreshing...' : 'Refresh Readiness'}
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="px-6 py-4 border-b border-gray-200">
          <input
            type="text"
            placeholder="Search applications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab("ready")}
            className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === "ready"
                ? "border-b-2 border-blue-500 text-blue-600"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            Ready for Assessment ({readyApplications.length})
          </button>
          <button
            onClick={() => setActiveTab("needs-mapping")}
            className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === "needs-mapping"
                ? "border-b-2 border-green-500 text-green-600"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            Needs Mapping ({unmappedAssets.length})
          </button>
          <button
            onClick={() => setActiveTab("needs-collection")}
            className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === "needs-collection"
                ? "border-b-2 border-orange-500 text-orange-600"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            Needs Collection ({notReadyApplications.length})
          </button>
        </div>

        {/* Application List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm whitespace-pre-wrap">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              Loading applications...
            </div>
          ) : activeTab === "ready" ? (
            // Ready Tab Content
            readyApplications.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No ready applications found. Complete collection flows first.
              </div>
            ) : (
              <div className="space-y-2">
                {readyApplications.map((app) => (
                  <div
                    key={app.id}
                    onClick={() => toggleAppSelection(app.id)}
                    className={`p-4 border rounded-md cursor-pointer transition-colors ${
                      selectedAppIds.has(app.id)
                        ? 'bg-blue-50 border-blue-500'
                        : 'bg-white border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900">
                            {app.canonical_name}
                          </h3>
                          {app.is_verified && (
                            <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
                              Verified
                            </span>
                          )}
                          {app.readiness_status === "partial" && (
                            <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded flex items-center gap-1">
                              <span>⚠️</span>
                              <span>Partial</span>
                            </span>
                          )}
                        </div>
                        <div className="mt-1 flex gap-4 text-sm text-gray-600">
                          {app.application_type && (
                            <span>Type: {app.application_type}</span>
                          )}
                          {app.business_criticality && (
                            <span>Criticality: {app.business_criticality}</span>
                          )}
                          <span>Assets: {app.ready_asset_count}/{app.linked_asset_count} ready</span>
                          <span>Confidence: {(app.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedAppIds.has(app.id)}
                        onChange={() => toggleAppSelection(app.id)}
                        className="mt-1 h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : activeTab === "needs-mapping" ? (
            // Needs Mapping Tab Content
            unmappedAssets.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                All assets are mapped to applications!
              </div>
            ) : (
              <div className="space-y-3">
                {unmappedAssets.map((asset) => (
                  <div
                    key={asset.asset_id}
                    className="p-4 border border-green-200 rounded-md bg-green-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900">{asset.asset_name}</h3>
                          <span className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded capitalize">
                            {asset.asset_type}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded ${
                            asset.discovery_status === "completed"
                              ? "bg-green-200 text-green-800"
                              : "bg-yellow-200 text-yellow-800"
                          }`}>
                            {asset.discovery_status}
                          </span>
                        </div>

                        <div className="mt-2 text-sm text-gray-600">
                          Asset ID: {asset.asset_id.substring(0, 8)}...
                        </div>
                      </div>

                      <div className="ml-4 flex items-center gap-2">
                        <select
                          value={assetMappings[asset.asset_id] || ""}
                          onChange={(e) => handleMappingChange(asset.asset_id, e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          disabled={mappingInProgress === asset.asset_id}
                        >
                          <option value="">Select Application...</option>
                          {availableApplications.map((app) => (
                            <option key={app.id} value={app.id}>
                              {app.canonical_name}
                            </option>
                          ))}
                        </select>

                        <button
                          onClick={() => handleApplyMapping(asset.asset_id)}
                          disabled={!assetMappings[asset.asset_id] || mappingInProgress === asset.asset_id}
                          className="px-3 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {mappingInProgress === asset.asset_id ? 'Mapping...' : 'Map'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            // Needs Collection Tab Content
            notReadyApplications.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                All applications are ready for assessment!
              </div>
            ) : (
              <div className="space-y-3">
                {notReadyApplications.map((app) => (
                  <div
                    key={app.id}
                    className="p-4 border border-orange-200 rounded-md bg-orange-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-orange-600 text-lg">⚠️</span>
                          <h3 className="font-medium text-gray-900">
                            {app.canonical_name}
                          </h3>
                          <span className="px-2 py-1 text-xs bg-orange-200 text-orange-800 rounded">
                            Not Ready
                          </span>
                        </div>

                        <div className="mt-2 text-sm text-gray-700">
                          <strong>Assets:</strong> {app.linked_asset_count} linked ({app.ready_asset_count} ready, {app.not_ready_asset_count} not ready)
                        </div>

                        {app.readiness_blockers.length > 0 && (
                          <div className="mt-3">
                            <strong className="text-sm text-gray-700">Issues:</strong>
                            <ul className="mt-1 text-sm text-gray-600 list-disc list-inside space-y-1">
                              {app.readiness_blockers.map((blocker, idx) => (
                                <li key={idx}>{blocker}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {app.readiness_recommendations.length > 0 && (
                          <div className="mt-3">
                            <strong className="text-sm text-gray-700">Next Steps:</strong>
                            <ul className="mt-1 text-sm text-gray-600 list-disc list-inside space-y-1">
                              {app.readiness_recommendations.map((rec, idx) => (
                                <li key={idx}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      <button
                        onClick={() => handleStartCollection(app)}
                        disabled={startingCollection === app.id}
                        className="ml-4 px-3 py-2 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {startingCollection === app.id ? 'Starting...' : 'Start Collection'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {activeTab === "ready" ? (
              <>
                {selectedAppIds.size} application{selectedAppIds.size !== 1 ? 's' : ''} selected
              </>
            ) : activeTab === "needs-mapping" ? (
              <>Map assets to applications to include in assessment</>
            ) : (
              <>Complete collection flows to enable assessment</>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={creating}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            {activeTab === "ready" && (
              <button
                onClick={handleCreateAssessment}
                disabled={creating || selectedAppIds.size === 0}
                className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Start Assessment'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
