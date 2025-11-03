/**
 * Asset Conflict Resolution Modal
 *
 * Displays duplicate asset conflicts in a modal with side-by-side comparison.
 * Allows users to choose resolution actions (keep/replace/merge) for each conflict.
 *
 * CC: Uses shadcn/ui components, snake_case fields, and HTTP-only communication
 */

import React, { useState, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { FieldMergeSelector } from './FieldMergeSelector';
import { assetConflictService } from '@/services/api/assetConflictService';
import type {
  AssetConflict,
  ResolutionAction,
  ConflictResolution,
  MergeFieldSelections,
} from '@/types/assetConflict';
import { useToast } from '@/components/ui/use-toast';
import SecureLogger from '@/utils/secureLogger';

interface AssetConflictModalProps {
  conflicts: AssetConflict[];
  isOpen: boolean;
  onClose: () => void;
  onResolutionComplete: () => void;
}

/**
 * Get conflict type badge color
 */
function getConflictTypeBadge(type: string): { variant: 'default' | 'secondary' | 'destructive'; label: string } {
  switch (type) {
    case 'hostname':
      return { variant: 'destructive', label: 'Hostname Conflict' };
    case 'ip_address':
      return { variant: 'destructive', label: 'IP Address Conflict' };
    case 'name':
      return { variant: 'secondary', label: 'Name Conflict' };
    default:
      return { variant: 'default', label: 'Conflict' };
  }
}

/**
 * Asset comparison row
 */
function AssetComparisonRow({ label, existingValue, newValue }: { label: string; existingValue: unknown; newValue: unknown }) {
  const displayValue = (val: unknown) => {
    if (val === null || val === undefined) return <span className="text-gray-400">(empty)</span>;
    if (typeof val === 'object') return <span className="text-xs">{JSON.stringify(val)}</span>;
    return String(val);
  };

  const differs = existingValue !== newValue && !(existingValue == null && newValue == null);

  return (
    <div className={`grid grid-cols-3 gap-4 py-2 border-b last:border-0 ${differs ? 'bg-yellow-50' : ''}`}>
      <div className="font-medium text-sm text-gray-700">{label}</div>
      <div className="text-sm">{displayValue(existingValue)}</div>
      <div className="text-sm">{displayValue(newValue)}</div>
    </div>
  );
}

// Backend-defined field allowlists (must match backend/app/services/asset_service/deduplication.py)
const ALLOWED_MERGE_FIELDS = new Set([
  // Technical specs
  'operating_system', 'os_version', 'cpu_cores', 'memory_gb', 'storage_gb',
  // Network info
  'ip_address', 'fqdn', 'mac_address',
  // Infrastructure
  'environment', 'location', 'datacenter', 'rack_location', 'availability_zone',
  // Business info
  'business_owner', 'technical_owner', 'department', 'application_name',
  'technology_stack', 'criticality', 'business_criticality',
  // Migration planning
  'six_r_strategy', 'migration_priority', 'migration_complexity', 'migration_wave',
  // Metadata
  'description', 'custom_attributes',
  // Performance metrics
  'cpu_utilization_percent', 'memory_utilization_percent', 'disk_iops',
  'network_throughput_mbps', 'current_monthly_cost', 'estimated_cloud_cost',
]);

export const AssetConflictModal: React.FC<AssetConflictModalProps> = ({
  conflicts,
  isOpen,
  onClose,
  onResolutionComplete,
}) => {
  const { toast } = useToast();

  // Track resolution action for each conflict
  const [resolutions, setResolutions] = useState<Record<string, ResolutionAction>>({});

  // Track merge field selections for conflicts with "merge" action
  const [mergeSelections, setMergeSelections] = useState<Record<string, MergeFieldSelections>>({});

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentTab, setCurrentTab] = useState<string>('all');

  // Filter conflicts by type
  const conflictsByType = useMemo(() => {
    return {
      all: conflicts,
      hostname: conflicts.filter((c) => c.conflict_type === 'hostname'),
      ip_address: conflicts.filter((c) => c.conflict_type === 'ip_address'),
      name: conflicts.filter((c) => c.conflict_type === 'name'),
    };
  }, [conflicts]);

  // Get current tab conflicts
  const displayedConflicts = conflictsByType[currentTab as keyof typeof conflictsByType] || conflicts;

  // Handle resolution action change
  const handleResolutionChange = (conflictId: string, action: ResolutionAction) => {
    setResolutions((prev) => ({
      ...prev,
      [conflictId]: action,
    }));

    if (action === 'merge') {
      // Auto-populate merge selections with all differing fields from new data
      const conflict = conflicts.find((c) => c.conflict_id === conflictId);
      if (conflict?.existing_asset && conflict?.new_asset) {
        const fieldSelections: MergeFieldSelections = {};

        Object.keys(conflict.new_asset).forEach((field) => {
          // CRITICAL: Only include fields that backend allows merging
          if (!ALLOWED_MERGE_FIELDS.has(field)) {
            return; // Skip protected/disallowed fields
          }

          const existingValue = conflict.existing_asset[field];
          const newValue = conflict.new_asset[field];

          // Select 'new' for fields that differ
          if (existingValue !== newValue && newValue !== null && newValue !== undefined) {
            fieldSelections[field] = 'new';
          }
        });

        // Set merge selections for this conflict
        if (Object.keys(fieldSelections).length > 0) {
          setMergeSelections((prev) => ({
            ...prev,
            [conflictId]: fieldSelections,
          }));
        }
      }
    } else {
      // Clear merge selections if action is not "merge"
      setMergeSelections((prev) => {
        const updated = { ...prev };
        delete updated[conflictId];
        return updated;
      });
    }
  };

  // Handle merge field selections
  const handleMergeSelectionsChange = (conflictId: string, selections: MergeFieldSelections) => {
    setMergeSelections((prev) => ({
      ...prev,
      [conflictId]: selections,
    }));
  };

  // Apply resolution action to all conflicts
  const handleApplyToAll = (action: ResolutionAction) => {
    const allResolutions: Record<string, ResolutionAction> = {};
    conflicts.forEach((conflict) => {
      allResolutions[conflict.conflict_id] = action;
    });
    setResolutions(allResolutions);

    // If action is "merge", auto-select all differing fields from new data
    if (action === 'merge') {
      const autoMergeSelections: Record<string, MergeFieldSelections> = {};
      conflicts.forEach((conflict) => {
        const fieldSelections: MergeFieldSelections = {};

        // For each field in the conflict details, select 'new' if values differ
        if (conflict.existing_asset && conflict.new_asset) {
          Object.keys(conflict.new_asset).forEach((field) => {
            // CRITICAL: Only include fields that backend allows merging
            if (!ALLOWED_MERGE_FIELDS.has(field)) {
              return; // Skip protected/disallowed fields
            }

            const existingValue = conflict.existing_asset[field];
            const newValue = conflict.new_asset[field];

            // Select 'new' for fields that differ
            if (existingValue !== newValue && newValue !== null && newValue !== undefined) {
              fieldSelections[field] = 'new';
            }
          });
        }

        // Only add merge selections if there are fields to merge
        if (Object.keys(fieldSelections).length > 0) {
          autoMergeSelections[conflict.conflict_id] = fieldSelections;
        }
      });

      setMergeSelections(autoMergeSelections);

      toast({
        title: 'Applied to All',
        description: `Set all conflicts to merge with new data for ${Object.keys(autoMergeSelections).length} conflicts`,
      });
    } else {
      // Clear merge selections if action is not "merge"
      setMergeSelections({});

      toast({
        title: 'Applied to All',
        description: `Set all conflicts to "${action.replace('_', ' ')}"`,
      });
    }
  };

  // Submit resolutions
  const handleSubmit = async () => {
    // Validate that all conflicts have a resolution
    const unresolvedConflicts = conflicts.filter((c) => !resolutions[c.conflict_id]);
    if (unresolvedConflicts.length > 0) {
      toast({
        variant: 'destructive',
        title: 'Incomplete Resolutions',
        description: `Please select a resolution action for all ${unresolvedConflicts.length} remaining conflicts.`,
      });
      return;
    }

    // Validate merge selections for "merge" actions
    const invalidMergeActions = conflicts.filter((c) => {
      const action = resolutions[c.conflict_id];
      const selections = mergeSelections[c.conflict_id];
      // Check if merge action exists without selections OR with empty selections
      return action === 'merge' && (!selections || Object.keys(selections).length === 0);
    });

    if (invalidMergeActions.length > 0) {
      toast({
        variant: 'destructive',
        title: 'Missing Merge Selections',
        description: `Please select fields to merge for ${invalidMergeActions.length} conflicts. Tip: The merge action auto-selects all differing fields by default.`,
      });
      return;
    }

    setIsSubmitting(true);
    SecureLogger.info('Submitting conflict resolutions', { conflictCount: conflicts.length });

    try {
      // Build resolution request
      const resolutionRequests: ConflictResolution[] = conflicts.map((conflict) => ({
        conflict_id: conflict.conflict_id,
        resolution_action: resolutions[conflict.conflict_id],
        merge_field_selections:
          resolutions[conflict.conflict_id] === 'merge'
            ? mergeSelections[conflict.conflict_id]
            : undefined,
      }));

      // Call backend API
      const response = await assetConflictService.resolveConflicts({
        resolutions: resolutionRequests,
      });

      SecureLogger.info('Conflict resolution response', response);

      // Show success/error feedback
      if (response.errors && response.errors.length > 0) {
        toast({
          variant: 'destructive',
          title: 'Partial Success',
          description: `Resolved ${response.resolved_count} of ${response.total_requested} conflicts. ${response.errors.length} errors occurred.`,
        });
      } else {
        toast({
          title: 'Success',
          description: `Successfully resolved ${response.resolved_count} conflict${response.resolved_count > 1 ? 's' : ''}.`,
        });
      }

      // Close modal and notify parent
      onResolutionComplete();
      onClose();
    } catch (error) {
      SecureLogger.error('Failed to resolve conflicts', error);
      toast({
        variant: 'destructive',
        title: 'Resolution Failed',
        description: error instanceof Error ? error.message : 'Failed to resolve conflicts. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Calculate progress
  const resolvedCount = Object.keys(resolutions).length;
  const progressPercentage = conflicts.length > 0 ? Math.round((resolvedCount / conflicts.length) * 100) : 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            Resolve Asset Conflicts - {conflicts.length} Pending
          </DialogTitle>
          <div className="mt-2">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600">
                Progress: {resolvedCount} of {conflicts.length} conflicts resolved
              </span>
              <span className="text-gray-600">{progressPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </DialogHeader>

        {/* Bulk Actions */}
        <Alert className="my-2">
          <AlertDescription className="flex items-center justify-between">
            <span className="text-sm font-medium">Apply action to all conflicts:</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => handleApplyToAll('keep_existing')}>
                Keep All Existing
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleApplyToAll('replace_with_new')}>
                Replace All
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleApplyToAll('merge')}>
                Merge All
              </Button>
            </div>
          </AlertDescription>
        </Alert>

        {/* Tabs for filtering by conflict type */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">All ({conflicts.length})</TabsTrigger>
            <TabsTrigger value="hostname">Hostname ({conflictsByType.hostname.length})</TabsTrigger>
            <TabsTrigger value="ip_address">IP Address ({conflictsByType.ip_address.length})</TabsTrigger>
            <TabsTrigger value="name">Name ({conflictsByType.name.length})</TabsTrigger>
          </TabsList>

          <TabsContent value={currentTab} className="flex-1 overflow-y-auto mt-4 space-y-4">
            {displayedConflicts.map((conflict) => {
              const currentAction = resolutions[conflict.conflict_id];
              const { variant, label } = getConflictTypeBadge(conflict.conflict_type);

              return (
                <Card key={conflict.conflict_id} className="border-2">
                  <CardContent className="pt-4 space-y-4">
                    {/* Conflict Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant={variant} className="mb-2">
                          {label}
                        </Badge>
                        <p className="font-medium text-lg">{conflict.conflict_key}</p>
                        <p className="text-sm text-gray-500">
                          Conflict Type: {conflict.conflict_type}
                        </p>
                      </div>
                      {currentAction && (
                        <Badge variant="outline" className="text-green-600 border-green-600">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Action Selected
                        </Badge>
                      )}
                    </div>

                    {/* Resolution Action Selector */}
                    <div className="space-y-2">
                      <Label className="text-sm font-semibold">Resolution Action</Label>
                      <RadioGroup
                        value={currentAction || ''}
                        onValueChange={(value) => handleResolutionChange(conflict.conflict_id, value as ResolutionAction)}
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="keep_existing" id={`${conflict.conflict_id}-keep`} />
                          <Label htmlFor={`${conflict.conflict_id}-keep`} className="cursor-pointer">
                            Keep Existing Asset (no changes)
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="replace_with_new" id={`${conflict.conflict_id}-replace`} />
                          <Label htmlFor={`${conflict.conflict_id}-replace`} className="cursor-pointer">
                            Replace with New Data (update all fields)
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="merge" id={`${conflict.conflict_id}-merge`} />
                          <Label htmlFor={`${conflict.conflict_id}-merge`} className="cursor-pointer">
                            Merge Fields (choose field-by-field)
                          </Label>
                        </div>
                      </RadioGroup>
                    </div>

                    {/* Field Merge Selector (only for "merge" action) */}
                    {currentAction === 'merge' && (
                      <FieldMergeSelector
                        existing_asset={conflict.existing_asset}
                        new_asset={conflict.new_asset}
                        onChange={(selections) => handleMergeSelectionsChange(conflict.conflict_id, selections)}
                        initialSelections={mergeSelections[conflict.conflict_id]}
                      />
                    )}

                    {/* Side-by-Side Asset Comparison */}
                    <div className="mt-4">
                      <Label className="text-sm font-semibold mb-2 block">Asset Comparison</Label>
                      <div className="grid grid-cols-3 gap-4 py-2 border-b font-semibold text-sm bg-gray-50">
                        <div>Field</div>
                        <div>Existing Asset</div>
                        <div>New Asset</div>
                      </div>
                      <div className="border rounded-lg">
                        <AssetComparisonRow
                          label="Name"
                          existingValue={conflict.existing_asset.name}
                          newValue={conflict.new_asset.name}
                        />
                        <AssetComparisonRow
                          label="Hostname"
                          existingValue={conflict.existing_asset.hostname}
                          newValue={conflict.new_asset.hostname}
                        />
                        <AssetComparisonRow
                          label="IP Address"
                          existingValue={conflict.existing_asset.ip_address}
                          newValue={conflict.new_asset.ip_address}
                        />
                        <AssetComparisonRow
                          label="Asset Type"
                          existingValue={conflict.existing_asset.asset_type}
                          newValue={conflict.new_asset.asset_type}
                        />
                        <AssetComparisonRow
                          label="Operating System"
                          existingValue={conflict.existing_asset.operating_system}
                          newValue={conflict.new_asset.operating_system}
                        />
                        <AssetComparisonRow
                          label="Environment"
                          existingValue={conflict.existing_asset.environment}
                          newValue={conflict.new_asset.environment}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}

            {displayedConflicts.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <XCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>No conflicts in this category.</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter className="border-t pt-4 mt-4">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || resolvedCount === 0}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Resolve {resolvedCount > 0 ? `${resolvedCount} ` : ''}Conflicts
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AssetConflictModal;
