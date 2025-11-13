/**
 * Hook for Asset Soft Delete Functionality (Issue #912)
 * Provides soft delete, restore, and bulk delete operations with confirmation dialogs
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AssetAPI } from '@/lib/api/assets';
import type { Asset } from '@/types/asset';
import { toast } from 'sonner';

/**
 * Hook for managing asset soft delete operations
 */
export const useAssetSoftDelete = () => {
  const queryClient = useQueryClient();

  /**
   * Soft delete a single asset
   */
  const softDeleteMutation = useMutation({
    mutationFn: async ({ asset_id }: { asset_id: number }) => {
      return AssetAPI.softDeleteAsset(asset_id);
    },
    onMutate: async ({ asset_id }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['assets'] });

      // Optimistically update cached data
      queryClient.setQueriesData<Asset[]>({ queryKey: ['assets'] }, (old) => {
        if (!old) return old;
        // Remove the asset from the active list
        return old.filter(asset => asset.id !== asset_id);
      });
    },
    onSuccess: () => {
      toast.success('Asset moved to trash successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete asset: ${error.message}`);
      // Refetch to revert optimistic update
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['deleted-assets'] });
    }
  });

  /**
   * Restore a soft-deleted asset
   */
  const restoreMutation = useMutation({
    mutationFn: async ({ asset_id }: { asset_id: number }) => {
      return AssetAPI.restoreAsset(asset_id);
    },
    onSuccess: () => {
      toast.success('Asset restored successfully');
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['deleted-assets'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to restore asset: ${error.message}`);
    }
  });

  /**
   * Bulk soft delete multiple assets
   */
  const bulkSoftDeleteMutation = useMutation({
    mutationFn: async ({ asset_ids }: { asset_ids: number[] }) => {
      return AssetAPI.bulkSoftDelete(asset_ids);
    },
    onMutate: async ({ asset_ids }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['assets'] });

      // Optimistically update cached data
      queryClient.setQueriesData<Asset[]>({ queryKey: ['assets'] }, (old) => {
        if (!old) return old;
        // Remove the assets from the active list
        return old.filter(asset => !asset_ids.includes(asset.id));
      });
    },
    onSuccess: (data) => {
      toast.success(`${data.deleted_count} assets moved to trash successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete assets: ${error.message}`);
      // Refetch to revert optimistic update
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['deleted-assets'] });
    }
  });

  /**
   * Soft delete with confirmation dialog
   */
  const softDelete = (asset_id: number, asset_name: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to move "${asset_name}" to trash?\n\nYou can restore it later from the Trash view.`
    );

    if (confirmed) {
      softDeleteMutation.mutate({ asset_id });
    }
  };

  /**
   * Restore with confirmation dialog
   */
  const restore = (asset_id: number, asset_name: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to restore "${asset_name}"?`
    );

    if (confirmed) {
      restoreMutation.mutate({ asset_id });
    }
  };

  /**
   * Bulk soft delete with confirmation dialog
   */
  const bulkSoftDelete = (asset_ids: number[], count: number) => {
    const confirmed = window.confirm(
      `Are you sure you want to move ${count} asset${count > 1 ? 's' : ''} to trash?\n\nYou can restore them later from the Trash view.`
    );

    if (confirmed) {
      bulkSoftDeleteMutation.mutate({ asset_ids });
    }
  };

  return {
    softDelete,
    restore,
    bulkSoftDelete,
    softDeleteDirect: softDeleteMutation.mutate,
    restoreDirect: restoreMutation.mutate,
    bulkSoftDeleteDirect: bulkSoftDeleteMutation.mutate,
    isDeleting: softDeleteMutation.isPending || bulkSoftDeleteMutation.isPending,
    isRestoring: restoreMutation.isPending
  };
};
