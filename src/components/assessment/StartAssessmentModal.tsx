/**
 * Start Assessment Modal Component
 *
 * Allows users to initialize assessment flows directly from canonical applications,
 * breaking the collection→assessment circular dependency (GPT-5 suggestion).
 *
 * Features:
 * - Searchable canonical application list
 * - Multi-select with visual feedback
 * - Zero-asset app handling
 * - Direct navigation to new assessment flow
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

export const StartAssessmentModal: React.FC<StartAssessmentModalProps> = ({
  isOpen,
  onClose,
}) => {
  const navigate = useNavigate();
  const { user, client, engagement } = useAuth();

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
      setError(err.message || 'Failed to create assessment. Please try again.');
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

        {/* Application List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              Loading applications...
            </div>
          ) : filteredApplications.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No applications found. Try a different search term.
            </div>
          ) : (
            <div className="space-y-2">
              {filteredApplications.map((app) => (
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
                      </div>
                      <div className="mt-1 flex gap-4 text-sm text-gray-600">
                        {app.application_type && (
                          <span>Type: {app.application_type}</span>
                        )}
                        {app.business_criticality && (
                          <span>Criticality: {app.business_criticality}</span>
                        )}
                        <span>Used: {app.usage_count}x</span>
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
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {selectedAppIds.size} application{selectedAppIds.size !== 1 ? 's' : ''} selected
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={creating}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateAssessment}
              disabled={creating || selectedAppIds.size === 0}
              className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? 'Creating...' : 'Start Assessment'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
