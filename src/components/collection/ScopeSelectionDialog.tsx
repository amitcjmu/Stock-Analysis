import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';

interface ScopeSelectionDialogProps {
  open: boolean;
  onClose: () => void;
  onScopeSelect: (scope: string, scope_id: string, asset_type?: string) => void;
}

interface ScopeTarget {
  value: string;
  label: string;
  type: string;
}

export const ScopeSelectionDialog: React.FC<ScopeSelectionDialogProps> = ({
  open,
  onClose,
  onScopeSelect
}) => {
  const [scope, setScope] = useState<'tenant' | 'engagement' | 'asset'>('tenant');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [selectedAssetType, setSelectedAssetType] = useState<string>('');

  // Fetch scope targets based on selected scope
  const { data: scopeTargets, isLoading: targetsLoading } = useQuery({
    queryKey: ['scope-targets', scope],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/collection/scope-targets/${scope}`, {
        method: 'GET'
      });
      return response as ScopeTarget[];
    },
    enabled: scope !== 'tenant' // No need to fetch targets for tenant scope
  });

  // Available asset types that can be selected for collection
  const assetTypes = [
    { value: 'server', label: 'Server' },
    { value: 'database', label: 'Database' },
    { value: 'device', label: 'Device' },
    { value: 'application', label: 'Application' }
  ];

  const handleSubmit = () => {
    let scopeId = '';

    if (scope === 'tenant') {
      // For tenant scope, use empty string as it will be handled by backend context
      scopeId = '';
    } else if (scope === 'engagement') {
      // For engagement scope, use the selected engagement ID
      scopeId = selectedTarget;
    } else if (scope === 'asset') {
      // For asset scope, use the selected asset ID
      scopeId = selectedTarget;
    }

    // Call the onScopeSelect callback with the appropriate parameters
    onScopeSelect(scope, scopeId, selectedAssetType || undefined);
    onClose();
  };

  const isFormValid = () => {
    if (scope === 'tenant') {
      return true; // Tenant scope doesn't require additional selection
    }
    if (scope === 'engagement' || scope === 'asset') {
      return selectedTarget !== ''; // Require target selection for engagement/asset scope
    }
    return false;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Select Collection Scope</DialogTitle>
          <DialogDescription>
            Choose what to collect data for. You can start with any asset type without application restrictions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Scope Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Collection Scope</Label>
            <RadioGroup value={scope} onValueChange={(value) => {
              setScope(value as 'tenant' | 'engagement' | 'asset');
              setSelectedTarget(''); // Reset target when scope changes
            }}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="tenant" id="tenant" />
                <Label htmlFor="tenant" className="text-sm">
                  Entire Tenant
                  <span className="block text-xs text-gray-500">
                    Collect data across all engagements
                  </span>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="engagement" id="engagement" />
                <Label htmlFor="engagement" className="text-sm">
                  Current Engagement
                  <span className="block text-xs text-gray-500">
                    Collect data for specific engagement
                  </span>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="asset" id="asset" />
                <Label htmlFor="asset" className="text-sm">
                  Specific Asset
                  <span className="block text-xs text-gray-500">
                    Collect data for individual asset
                  </span>
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Target Selection for Engagement/Asset */}
          {(scope === 'engagement' || scope === 'asset') && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Select {scope === 'engagement' ? 'Engagement' : 'Asset'}
              </Label>
              <Select value={selectedTarget} onValueChange={setSelectedTarget}>
                <SelectTrigger>
                  <SelectValue placeholder={`Choose ${scope}...`} />
                </SelectTrigger>
                <SelectContent>
                  {targetsLoading ? (
                    <SelectItem value="loading" disabled>
                      Loading {scope}s...
                    </SelectItem>
                  ) : scopeTargets && scopeTargets.length > 0 ? (
                    scopeTargets.map((target) => (
                      <SelectItem key={target.value} value={target.value}>
                        {target.label}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled>
                      No {scope}s available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Asset Type Selection (Optional) */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              Asset Type (Optional)
            </Label>
            <Select value={selectedAssetType} onValueChange={setSelectedAssetType}>
              <SelectTrigger>
                <SelectValue placeholder="Any asset type..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Any asset type</SelectItem>
                {assetTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid() || (scope !== 'tenant' && targetsLoading)}
          >
            Start Collection
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
