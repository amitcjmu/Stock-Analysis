/**
 * ApplicationGroupsWidget - Hierarchical display of applications and their assets
 *
 * Phase 4 Days 17-18: Assessment Architecture Enhancement
 * Modularized for <400 line compliance
 *
 * Features:
 * - Hierarchical card-based layout with collapsible groups
 * - Application groups with asset details
 * - Readiness indicators with color coding
 * - Search and filtering capabilities
 * - Responsive design (mobile, tablet, desktop)
 * - Accessibility support (ARIA labels, keyboard navigation)
 *
 * Backend Integration:
 * - Fetches from: GET /api/v1/master-flows/{flow_id}/assessment-applications
 * - Uses snake_case for ALL field names (ADR compliance)
 * - Follows TanStack Query patterns for data fetching
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Package,
  Search,
  AlertTriangle,
  Loader2,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { ApplicationGroupCard } from './shared/ApplicationGroupCard';
import {
  ApplicationGroupsFilters,
  type SortOption,
  type SortDirection,
} from './shared/ApplicationGroupsFilters';
import type { ApplicationAssetGroup } from '@/types/assessment';

// ============================================================================
// Component Props
// ============================================================================

export interface ApplicationGroupsWidgetProps {
  flow_id: string;
  client_account_id: string;
  engagement_id?: string; // Optional - not required for tenant scoping
  onAssetClick?: (asset_id: string) => void;
}

// ============================================================================
// Main Component
// ============================================================================

export const ApplicationGroupsWidget: React.FC<ApplicationGroupsWidgetProps> = ({
  flow_id,
  client_account_id,
  engagement_id,
  onAssetClick,
}) => {
  const { getAuthHeaders } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // ============================================================================
  // Data Fetching
  // ============================================================================

  const {
    data: applicationGroups = [],
    isLoading,
    isError,
    error,
  } = useQuery<ApplicationAssetGroup[]>({
    queryKey: ['assessment-applications', flow_id, client_account_id, engagement_id],
    queryFn: async () => {
      const headers = {
        ...getAuthHeaders(),
        'X-Client-Account-ID': client_account_id,
        ...(engagement_id && { 'X-Engagement-ID': engagement_id }), // Conditionally include
      };

      const response = await apiCall(`/master-flows/${flow_id}/assessment-applications`, {
        method: 'GET',
        headers,
      });

      // Backend returns object with applications array property
      // API response: {flow_id, applications: [...], total_applications, total_assets}
      return Array.isArray(response?.applications) ? response.applications : [];
    },
    enabled: !!flow_id && !!client_account_id, // engagement_id is optional
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refresh every minute
  });

  // ============================================================================
  // Filtering and Sorting
  // ============================================================================

  const filteredAndSortedGroups = useMemo(() => {
    let filtered = applicationGroups;

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((group) =>
        group.canonical_application_name.toLowerCase().includes(query)
      );
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'name':
          comparison = a.canonical_application_name.localeCompare(b.canonical_application_name);
          break;
        case 'asset_count':
          comparison = a.asset_count - b.asset_count;
          break;
        case 'readiness': {
          const aTotal = a.readiness_summary.ready + a.readiness_summary.not_ready + a.readiness_summary.in_progress;
          const bTotal = b.readiness_summary.ready + b.readiness_summary.not_ready + b.readiness_summary.in_progress;
          const aPercentage = aTotal > 0 ? (a.readiness_summary.ready / aTotal) * 100 : 0;
          const bPercentage = bTotal > 0 ? (b.readiness_summary.ready / bTotal) * 100 : 0;
          comparison = aPercentage - bPercentage;
          break;
        }
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [applicationGroups, searchQuery, sortBy, sortDirection]);

  // Separate unmapped assets
  const unmappedGroups = useMemo(
    () => filteredAndSortedGroups.filter((g) => g.canonical_application_id === null),
    [filteredAndSortedGroups]
  );

  const mappedGroups = useMemo(
    () => filteredAndSortedGroups.filter((g) => g.canonical_application_id !== null),
    [filteredAndSortedGroups]
  );

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const handleSortChange = (newSortBy: SortOption) => {
    if (sortBy === newSortBy) {
      // Toggle direction if clicking same column
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(newSortBy);
      setSortDirection('asc');
    }
  };

  // ============================================================================
  // Render States
  // ============================================================================

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Application Groups</CardTitle>
          <CardDescription>Loading application groupings...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Application Groups</CardTitle>
          <CardDescription className="text-destructive">
            Failed to load application groups
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>{error instanceof Error ? error.message : 'An error occurred'}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (applicationGroups.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Application Groups</CardTitle>
          <CardDescription>No applications found for this assessment</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-12">
          <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">
            No application groups available. Complete the collection flow first.
          </p>
        </CardContent>
      </Card>
    );
  }

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Application Groups</CardTitle>
              <CardDescription>
                {mappedGroups.length} applications, {unmappedGroups.length} unmapped assets
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search and Filters */}
          <ApplicationGroupsFilters
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            sortBy={sortBy}
            sortDirection={sortDirection}
            onSortChange={handleSortChange}
          />
        </CardContent>
      </Card>

      {/* Mapped Application Groups */}
      {mappedGroups.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {mappedGroups.map((group) => {
            const groupId = group.canonical_application_id || group.canonical_application_name;
            return (
              <ApplicationGroupCard
                key={groupId}
                group={group}
                isExpanded={expandedGroups.has(groupId)}
                onToggle={() => toggleGroup(groupId)}
                onAssetClick={onAssetClick}
              />
            );
          })}
        </div>
      )}

      {/* Unmapped Assets Section */}
      {unmappedGroups.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <h3 className="text-lg font-semibold">Unmapped Assets</h3>
            <Badge variant="secondary">{unmappedGroups.length} assets</Badge>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {unmappedGroups.map((group) => {
              const groupId = `unmapped-${group.canonical_application_name}`;
              return (
                <ApplicationGroupCard
                  key={groupId}
                  group={group}
                  isExpanded={expandedGroups.has(groupId)}
                  onToggle={() => toggleGroup(groupId)}
                  onAssetClick={onAssetClick}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* No Results Message */}
      {filteredAndSortedGroups.length === 0 && searchQuery && (
        <Card>
          <CardContent className="text-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-muted-foreground">No applications match "{searchQuery}"</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ApplicationGroupsWidget;
