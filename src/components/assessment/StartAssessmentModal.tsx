/**
 * Start Assessment Modal Component
 *
 * Allows users to initialize assessment flows directly from canonical applications,
 * breaking the collection→assessment circular dependency (GPT-5 suggestion).
 *
 * Features:
 * - Two-tab interface: "Ready for Assessment" and "Needs Collection"
 * - Searchable canonical application list across both tabs
 * - Multi-select with visual feedback (ready apps only)
 * - Readiness status indicators (ready/partial/not-ready)
 * - Actionable guidance for not-ready apps (blockers + recommendations)
 * - Direct navigation to assessment or collection flows
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

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

interface CanonicalApplicationsResponse {
  applications: CanonicalApplication[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface StartAssessmentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "ready" | "not-ready";

export const StartAssessmentModal: React.FC<StartAssessmentModalProps> = ({
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

  const [activeTab, setActiveTab] = useState<TabType>("ready");
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAppIds, setSelectedAppIds] = useState<Set<string>>(new Set());
  const [applications, setApplications] = useState<CanonicalApplication[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch canonical applications
  useEffect(() => {
    if (!isOpen || !client?.id || !engagement?.id) return;

    const fetchApplications = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await apiCall<CanonicalApplicationsResponse>(
          `/api/v1/canonical-applications?search=${encodeURIComponent(searchQuery)}&page=1&page_size=100`,
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
    return applications.filter((app) =>
      app.canonical_name.toLowerCase().includes(query)
    );
  }, [applications, searchQuery]);

  // Separate ready and not-ready applications
  const readyApplications = useMemo(() => {
    return filteredApplications.filter(app =>
      app.readiness_status === "ready" || app.readiness_status === "partial"
    );
  }, [filteredApplications]);

  const notReadyApplications = useMemo(() => {
    return filteredApplications.filter(app =>
      app.readiness_status === "not_ready"
    );
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Start New Assessment
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Select one or more canonical applications to assess
          </p>
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
            onClick={() => setActiveTab("not-ready")}
            className={`flex-1 px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === "not-ready"
                ? "border-b-2 border-blue-500 text-blue-600"
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
          ) : (
            // Not Ready Tab Content
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
                        onClick={() => {
                          navigate(`/collection/new?app=${app.id}`);
                          onClose();
                        }}
                        className="ml-4 px-3 py-2 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors whitespace-nowrap"
                      >
                        Start Collection
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
