/**
 * Custom AG Grid Cell Renderer for Dependencies
 *
 * Displays selected dependencies as clickable badges.
 * Shows asset names fetched from IDs.
 */

import React, { useState, useEffect } from 'react';
import { ICellRendererParams } from 'ag-grid-community';
import { Badge } from '@/components/ui/badge';
import { Server, Database, Layers, ExternalLink } from 'lucide-react';
import { AssetAPI } from '@/lib/api/assets';
import type { Asset } from '@/types/asset';

interface DependencyCellRendererProps extends ICellRendererParams {
  value: string | null | undefined;
}

export const DependencyCellRenderer: React.FC<DependencyCellRendererProps> = ({ value }) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchAssetDetails = async () => {
      if (!value) {
        setAssets([]);
        return;
      }

      try {
        setIsLoading(true);
        // Parse comma-separated IDs
        const ids = value.toString().split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));

        if (ids.length === 0) {
          setAssets([]);
          return;
        }

        // Fetch all assets and filter by IDs
        // Note: In production, you might want a batch endpoint like GET /assets?ids=1,2,3
        const response = await AssetAPI.getAssets({ page_size: 1000 });
        const matchedAssets = response.assets.filter(asset => ids.includes(asset.id));

        setAssets(matchedAssets);
      } catch (error) {
        console.error('Failed to fetch dependency assets:', error);
        setAssets([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAssetDetails();
  }, [value]);

  // Get icon for asset type
  const getAssetIcon = (assetType: string) => {
    switch (assetType.toLowerCase()) {
      case 'server':
        return <Server className="h-3 w-3" />;
      case 'database':
        return <Database className="h-3 w-3" />;
      default:
        return <Layers className="h-3 w-3" />;
    }
  };

  if (isLoading) {
    return <span className="text-xs text-gray-400">Loading...</span>;
  }

  if (!value || assets.length === 0) {
    return <span className="text-xs text-gray-400">No dependencies</span>;
  }

  return (
    <div className="flex flex-wrap gap-1 py-1">
      {assets.map(asset => (
        <Badge
          key={asset.id}
          variant="outline"
          className="flex items-center gap-1 text-xs cursor-pointer hover:bg-gray-100"
          title={`${asset.asset_type}${asset.hostname ? ` • ${asset.hostname}` : ''}${asset.environment ? ` • ${asset.environment}` : ''}`}
        >
          {getAssetIcon(asset.asset_type)}
          <span>{asset.name}</span>
          <ExternalLink className="h-2.5 w-2.5 opacity-50" />
        </Badge>
      ))}
    </div>
  );
};
