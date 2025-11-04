/**
 * Asset Creation Preview Modal (Issue #907)
 *
 * Displays transformed assets ready for creation with inline editing capabilities.
 * Allows users to review, edit, select, and approve assets before database creation.
 *
 * Features:
 * - Table view with inline editing for key fields
 * - Row selection for targeted approval
 * - Bulk actions (Approve Selected, Cancel)
 * - Real-time validation feedback
 * - Polling for updated data during flow processing
 *
 * CC: All field names use snake_case to match backend API
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import {
  getAssetPreview,
  approveAssets,
  type AssetPreviewData,
  type AssetPreviewResponse,
} from '@/lib/api/assetPreview';

interface AssetCreationPreviewModalProps {
  flow_id: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface EditableAsset extends AssetPreviewData {
  isSelected: boolean;
  validationErrors: Record<string, string>;
}

export const AssetCreationPreviewModal: React.FC<
  AssetCreationPreviewModalProps
> = ({ flow_id, isOpen, onClose, onSuccess }) => {
  const queryClient = useQueryClient();
  const [editableAssets, setEditableAssets] = useState<EditableAsset[]>([]);
  const [hasUnsavedEdits, setHasUnsavedEdits] = useState(false);

  // Fetch asset preview with polling during flow processing
  const {
    data: previewData,
    isLoading,
    error,
  } = useQuery<AssetPreviewResponse>({
    queryKey: ['assetPreview', flow_id],
    queryFn: async () => {
      console.log('📡 Fetching asset preview for flow:', flow_id);
      const result = await getAssetPreview(flow_id);
      console.log('📊 Asset preview API response:', {
        flow_id,
        status: result.status,
        count: result.count,
        hasAssets: !!result.assets_preview,
        assetsLength: result.assets_preview?.length || 0
      });
      return result;
    },
    enabled: isOpen && !!flow_id,
    refetchInterval: (data) => {
      // Poll every 5 seconds if preview not ready, otherwise no polling
      return data?.status === 'preview_ready' ? false : 5000;
    },
  });

  // CC FIX (Issue #907): Initialize editable assets when preview data loads
  // Replaced deprecated onSuccess callback with useEffect
  useEffect(() => {
    if (previewData?.assets_preview && editableAssets.length === 0) {
      console.log(`🎨 Initializing ${previewData.assets_preview.length} editable assets`);
      setEditableAssets(
        previewData.assets_preview.map((asset) => ({
          ...asset,
          isSelected: true, // Default: all selected
          validationErrors: {},
        }))
      );
    }
  }, [previewData, editableAssets.length]);

  // Approve assets mutation
  const approveMutation = useMutation({
    mutationFn: (asset_ids: string[]) => approveAssets(flow_id, asset_ids),
    onSuccess: () => {
      queryClient.invalidateQueries(['assetPreview', flow_id]);
      queryClient.invalidateQueries(['discoveryFlow', flow_id]);
      if (onSuccess) {
        onSuccess();
      }
      onClose();
    },
    onError: (error: Error) => {
      console.error('Failed to approve assets:', error);
    },
  });

  // Computed: Selected assets for approval
  const selectedAssets = useMemo(() => {
    return editableAssets.filter((asset) => asset.isSelected);
  }, [editableAssets]);

  // Computed: Validation state
  const hasValidationErrors = useMemo(() => {
    return editableAssets.some(
      (asset) => Object.keys(asset.validationErrors).length > 0
    );
  }, [editableAssets]);

  // Handler: Toggle asset selection
  const handleToggleSelection = (assetId: string | undefined) => {
    if (!assetId) return;
    setEditableAssets((prev) =>
      prev.map((asset) =>
        asset.id === assetId
          ? { ...asset, isSelected: !asset.isSelected }
          : asset
      )
    );
  };

  // Handler: Toggle all selections
  const handleToggleAll = () => {
    const allSelected = editableAssets.every((asset) => asset.isSelected);
    setEditableAssets((prev) =>
      prev.map((asset) => ({ ...asset, isSelected: !allSelected }))
    );
  };

  // Handler: Update field value with validation
  const handleFieldEdit = (
    assetId: string | undefined,
    field: keyof AssetPreviewData,
    value: string | number
  ) => {
    if (!assetId) return;

    setEditableAssets((prev) =>
      prev.map((asset) => {
        if (asset.id !== assetId) return asset;

        const updatedAsset = { ...asset, [field]: value };
        const errors = { ...asset.validationErrors };

        // Basic validation
        if (field === 'name' && !value) {
          errors.name = 'Asset name is required';
        } else if (field === 'name') {
          delete errors.name;
        }

        if (field === 'hostname' && !value) {
          errors.hostname = 'Hostname is required for server assets';
        } else if (field === 'hostname') {
          delete errors.hostname;
        }

        setHasUnsavedEdits(true);
        return { ...updatedAsset, validationErrors: errors };
      })
    );
  };

  // Handler: Approve selected assets
  const handleApprove = () => {
    if (selectedAssets.length === 0) return;
    if (hasValidationErrors) return;

    const assetIds = selectedAssets
      .map((asset) => asset.id)
      .filter((id): id is string => !!id);

    approveMutation.mutate(assetIds);
  };

  // Loading state
  if (isLoading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-3 text-lg">Loading asset preview...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  // Error state
  if (error) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Error Loading Preview
            </DialogTitle>
          </DialogHeader>
          <Alert variant="destructive">
            <AlertDescription>
              {error instanceof Error
                ? error.message
                : 'Failed to load asset preview'}
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // Assets already created state
  if (previewData?.status === 'assets_already_created') {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Assets Already Created
            </DialogTitle>
          </DialogHeader>
          <Alert>
            <AlertDescription>
              {previewData.message ||
                'Assets for this flow have already been created.'}
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[90vw] max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>Review Assets for Creation</DialogTitle>
          <DialogDescription>
            Review, edit, and approve assets before creating them in the
            database.
            {hasUnsavedEdits && (
              <Badge variant="outline" className="ml-2">
                Unsaved edits
              </Badge>
            )}
          </DialogDescription>
        </DialogHeader>

        {/* Asset count and selection summary */}
        <div className="flex items-center justify-between py-2 px-4 bg-muted rounded-md">
          <span className="text-sm font-medium">
            Total Assets: {previewData?.count || 0} | Selected:{' '}
            {selectedAssets.length}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleAll}
            disabled={editableAssets.length === 0}
          >
            {editableAssets.every((asset) => asset.isSelected)
              ? 'Deselect All'
              : 'Select All'}
          </Button>
        </div>

        {/* Validation errors alert */}
        {hasValidationErrors && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Please fix validation errors before approving assets.
            </AlertDescription>
          </Alert>
        )}

        {/* Asset table */}
        <div className="border rounded-md overflow-auto max-h-[500px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={editableAssets.every((asset) => asset.isSelected)}
                    onCheckedChange={handleToggleAll}
                  />
                </TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Hostname</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Environment</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {editableAssets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    No assets available for preview
                  </TableCell>
                </TableRow>
              ) : (
                editableAssets.map((asset) => (
                  <TableRow
                    key={asset.id}
                    className={
                      asset.isSelected ? 'bg-accent/50' : 'opacity-60'
                    }
                  >
                    <TableCell>
                      <Checkbox
                        checked={asset.isSelected}
                        onCheckedChange={() => handleToggleSelection(asset.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={asset.name}
                        onChange={(e) =>
                          handleFieldEdit(asset.id, 'name', e.target.value)
                        }
                        className={
                          asset.validationErrors.name
                            ? 'border-destructive'
                            : ''
                        }
                      />
                      {asset.validationErrors.name && (
                        <span className="text-xs text-destructive">
                          {asset.validationErrors.name}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{asset.asset_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Input
                        value={asset.hostname || ''}
                        onChange={(e) =>
                          handleFieldEdit(asset.id, 'hostname', e.target.value)
                        }
                        placeholder="hostname"
                        className={
                          asset.validationErrors.hostname
                            ? 'border-destructive'
                            : ''
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={asset.ip_address || ''}
                        onChange={(e) =>
                          handleFieldEdit(
                            asset.id,
                            'ip_address',
                            e.target.value
                          )
                        }
                        placeholder="IP"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={asset.environment || ''}
                        onChange={(e) =>
                          handleFieldEdit(
                            asset.id,
                            'environment',
                            e.target.value
                          )
                        }
                        placeholder="environment"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={asset.description || ''}
                        onChange={(e) =>
                          handleFieldEdit(
                            asset.id,
                            'description',
                            e.target.value
                          )
                        }
                        placeholder="description"
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleApprove}
            disabled={
              selectedAssets.length === 0 ||
              hasValidationErrors ||
              approveMutation.isLoading
            }
          >
            {approveMutation.isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Approving...
              </>
            ) : (
              `Approve ${selectedAssets.length} Asset${
                selectedAssets.length !== 1 ? 's' : ''
              }`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
