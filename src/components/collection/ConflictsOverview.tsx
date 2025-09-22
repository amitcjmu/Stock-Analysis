import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, CheckCircle2, Clock, ExternalLink } from 'lucide-react';
import { collectionFlowApi } from '@/services/api/collection-flow';

interface ConflictsSummary {
  total_conflicts: number;
  pending_conflicts: number;
  resolved_conflicts: number;
  auto_resolved_conflicts: number;
  assets_with_conflicts: number;
  most_common_fields: Array<{
    field_name: string;
    conflict_count: number;
  }>;
}

interface ConflictsOverviewProps {
  asset_id?: string; // Optional - if provided, shows conflicts for specific asset
  className?: string;
}

export const ConflictsOverview: React.FC<ConflictsOverviewProps> = ({
  asset_id,
  className = ''
}) => {
  // If asset_id is provided, fetch conflicts for specific asset
  // Otherwise, fetch summary across all assets (would need a new API endpoint)
  const { data: conflictsData, isLoading, error } = useQuery({
    queryKey: asset_id ? ['asset-conflicts', asset_id] : ['conflicts-summary'],
    queryFn: async () => {
      if (asset_id) {
        // Fetch conflicts for specific asset
        const conflicts = await collectionFlowApi.getAssetConflicts(asset_id);

        // Transform to summary format
        const pending = conflicts.filter(c => c.resolution_status === 'pending').length;
        const autoResolved = conflicts.filter(c => c.resolution_status === 'auto_resolved').length;
        const manualResolved = conflicts.filter(c => c.resolution_status === 'manual_resolved').length;

        // Count field frequencies
        const fieldCounts: Record<string, number> = {};
        conflicts.forEach(conflict => {
          fieldCounts[conflict.field_name] = (fieldCounts[conflict.field_name] || 0) + 1;
        });

        const mostCommonFields = Object.entries(fieldCounts)
          .map(([field_name, conflict_count]) => ({ field_name, conflict_count }))
          .sort((a, b) => b.conflict_count - a.conflict_count)
          .slice(0, 3);

        return {
          total_conflicts: conflicts.length,
          pending_conflicts: pending,
          resolved_conflicts: manualResolved,
          auto_resolved_conflicts: autoResolved,
          assets_with_conflicts: 1, // Single asset
          most_common_fields: mostCommonFields
        } as ConflictsSummary;
      } else {
        // For now, return mock summary data
        // In real implementation, this would call a summary endpoint
        return {
          total_conflicts: 12,
          pending_conflicts: 5,
          resolved_conflicts: 4,
          auto_resolved_conflicts: 3,
          assets_with_conflicts: 8,
          most_common_fields: [
            { field_name: 'business_criticality', conflict_count: 4 },
            { field_name: 'technology_stack', conflict_count: 3 },
            { field_name: 'environment', conflict_count: 2 }
          ]
        } as ConflictsSummary;
      }
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000 // Refetch every minute
  });

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !conflictsData) {
    return (
      <div className={`text-center p-4 ${className}`}>
        <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
        <p className="text-sm text-gray-600">Failed to load conflicts data</p>
        <p className="text-xs text-gray-500 mt-1">Check your connection and try again</p>
      </div>
    );
  }

  const getStatusIcon = (status: 'pending' | 'resolved' | 'auto_resolved') => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-amber-500" />;
      case 'resolved':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'auto_resolved':
        return <CheckCircle2 className="h-4 w-4 text-blue-500" />;
    }
  };

  const getStatusBadge = (status: 'pending' | 'resolved' | 'auto_resolved', count: number) => {
    const variant = status === 'pending' ? 'destructive' :
                   status === 'resolved' ? 'default' : 'secondary';

    return (
      <Badge variant={variant} className="flex items-center gap-1">
        {getStatusIcon(status)}
        {count}
      </Badge>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Summary Stats */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Total Conflicts</span>
          <span className="text-lg font-bold">{conflictsData.total_conflicts}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm">Pending Resolution</span>
          {getStatusBadge('pending', conflictsData.pending_conflicts)}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm">Manually Resolved</span>
          {getStatusBadge('resolved', conflictsData.resolved_conflicts)}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm">Auto-resolved</span>
          {getStatusBadge('auto_resolved', conflictsData.auto_resolved_conflicts)}
        </div>

        {!asset_id && (
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm font-medium">Assets Affected</span>
            <span className="text-lg font-semibold text-blue-600">
              {conflictsData.assets_with_conflicts}
            </span>
          </div>
        )}
      </div>

      {/* Most Common Conflict Fields */}
      {conflictsData.most_common_fields.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Most Common Fields</h4>
          <div className="space-y-1">
            {conflictsData.most_common_fields.map((field, index) => (
              <div key={field.field_name} className="flex items-center justify-between text-xs">
                <span className="text-gray-600 truncate">
                  {field.field_name.replace(/_/g, ' ')}
                </span>
                <Badge variant="outline" className="text-xs">
                  {field.conflict_count}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="space-y-2 pt-3 border-t">
        {conflictsData.pending_conflicts > 0 && (
          <Button
            size="sm"
            className="w-full"
            onClick={() => {
              // Navigate to conflict resolution page
              const url = asset_id
                ? `/collection/data-integration?asset_id=${asset_id}`
                : '/collection/data-integration';
              window.location.href = url;
            }}
          >
            Resolve Conflicts
            <ExternalLink className="h-3 w-3 ml-1" />
          </Button>
        )}

        {conflictsData.total_conflicts === 0 && (
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <CheckCircle2 className="h-6 w-6 text-green-500 mx-auto mb-1" />
            <p className="text-xs text-green-700 font-medium">All Conflicts Resolved</p>
            <p className="text-xs text-green-600">Data quality is excellent</p>
          </div>
        )}
      </div>
    </div>
  );
};
