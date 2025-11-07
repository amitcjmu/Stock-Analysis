/**
 * Custom AG Grid Cell Editor for Multi-Select Dependencies
 *
 * Allows users to select multiple assets as dependencies from a searchable list.
 * Shows selected dependencies as badges and provides filtering by asset type.
 */

import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle, useCallback } from 'react';
import type { ICellEditorParams } from 'ag-grid-community';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { X, Search, Server, Database, Layers } from 'lucide-react';
import { AssetAPI } from '@/lib/api/assets';
import type { Asset } from '@/types/asset';

interface DependencyCellEditorProps extends ICellEditorParams {
  value: string | null | undefined;
}

export const DependencyCellEditor = forwardRef((props: DependencyCellEditorProps, ref) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<number[]>([]);
  const [availableAssets, setAvailableAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle closing the editor
  const handleClose = useCallback(() => {
    // AG Grid will call getValue() when the editor stops
    if (props.stopEditing) {
      props.stopEditing();
    }
  }, [props]);

  // Parse initial value (comma-separated asset IDs or names)
  useEffect(() => {
    const parseInitialValue = () => {
      if (!props.value) {
        setSelectedAssets([]);
        return;
      }

      // Value could be comma-separated IDs or names
      const parts = props.value.toString().split(',').map(p => p.trim());
      const ids: number[] = [];

      parts.forEach(part => {
        // Try to parse as number (ID)
        const id = parseInt(part);
        if (!isNaN(id)) {
          ids.push(id);
        }
      });

      setSelectedAssets(ids);
    };

    parseInitialValue();
  }, [props.value]);

  // Fetch available assets with pagination (backend max is 200 per page)
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        setIsLoading(true);
        const allAssets: Asset[] = [];
        let page = 1;
        let hasMore = true;
        const pageSize = 200; // Backend maximum

        // Fetch all assets in batches of 200
        while (hasMore) {
          const response = await AssetAPI.getAssets({
            page: page,
            page_size: pageSize
          });

          allAssets.push(...response.assets);

          // Check if there are more pages
          hasMore = response.assets.length === pageSize;
          page++;

          // Safety limit to prevent infinite loops
          if (page > 20) { // Max 4000 assets (20 pages * 200)
            console.warn('Reached maximum page limit (20 pages) for asset fetching');
            break;
          }
        }

        // Exclude the current asset from the list
        const currentAssetId = props.data?.id;
        const filtered = allAssets.filter(asset =>
          !asset.is_deleted && asset.id !== currentAssetId
        );

        setAvailableAssets(filtered);
      } catch (error) {
        console.error('Failed to fetch assets for dependencies:', error);
        setAvailableAssets([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAssets();
  }, [props.data?.id]);

  // Expose getValue method to AG Grid
  useImperativeHandle(ref, () => ({
    getValue: () => {
      // Return comma-separated asset IDs
      return selectedAssets.length > 0 ? selectedAssets.join(',') : null;
    },
    isCancelBeforeStart: () => false,
    isCancelAfterEnd: () => false,
  }));

  // Toggle asset selection
  const toggleAsset = (assetId: number) => {
    setSelectedAssets(prev =>
      prev.includes(assetId)
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  };

  // Remove selected asset
  const removeAsset = (assetId: number) => {
    setSelectedAssets(prev => prev.filter(id => id !== assetId));
  };

  // Filter assets by search term and type
  const filteredAssets = availableAssets.filter(asset => {
    const matchesSearch = !searchTerm ||
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.hostname?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = filterType === 'all' || asset.asset_type === filterType;

    return matchesSearch && matchesType;
  });

  // Get selected asset details for display
  const selectedAssetDetails = availableAssets.filter(asset =>
    selectedAssets.includes(asset.id)
  );

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

  return (
    <div
      ref={containerRef}
      className="ag-custom-component-popup"
      style={{
        position: 'absolute',
        zIndex: 9999,
        backgroundColor: 'white',
        border: '1px solid #d1d5db',
        borderRadius: '8px',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        width: '500px',
        maxHeight: '500px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header with search and filters */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-3">
          <Search className="h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search assets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
            autoFocus
          />
        </div>

        {/* Asset type filter */}
        <div className="flex gap-2 flex-wrap">
          <Button
            size="sm"
            variant={filterType === 'all' ? 'default' : 'outline'}
            onClick={() => setFilterType('all')}
          >
            All
          </Button>
          <Button
            size="sm"
            variant={filterType === 'Application' ? 'default' : 'outline'}
            onClick={() => setFilterType('Application')}
          >
            Applications
          </Button>
          <Button
            size="sm"
            variant={filterType === 'Server' ? 'default' : 'outline'}
            onClick={() => setFilterType('Server')}
          >
            Servers
          </Button>
          <Button
            size="sm"
            variant={filterType === 'Database' ? 'default' : 'outline'}
            onClick={() => setFilterType('Database')}
          >
            Databases
          </Button>
        </div>
      </div>

      {/* Selected assets badges */}
      {selectedAssetDetails.length > 0 && (
        <div className="p-3 border-b bg-gray-50 flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700">Selected:</span>
          {selectedAssetDetails.map(asset => (
            <Badge key={asset.id} variant="default" className="flex items-center gap-1">
              {getAssetIcon(asset.asset_type)}
              <span>{asset.name}</span>
              <button
                onClick={() => removeAsset(asset.id)}
                className="ml-1 hover:bg-red-600 rounded-full p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Asset list */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading assets...</div>
        ) : filteredAssets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {searchTerm ? 'No assets match your search' : 'No assets available'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredAssets.map(asset => (
              <div
                key={asset.id}
                className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded cursor-pointer"
                onClick={() => toggleAsset(asset.id)}
              >
                <Checkbox
                  checked={selectedAssets.includes(asset.id)}
                  onCheckedChange={() => toggleAsset(asset.id)}
                />
                <div className="flex items-center gap-2 flex-1">
                  {getAssetIcon(asset.asset_type)}
                  <div className="flex-1">
                    <div className="font-medium text-sm">{asset.name}</div>
                    <div className="text-xs text-gray-500">
                      {asset.asset_type}
                      {asset.hostname && ` • ${asset.hostname}`}
                      {asset.environment && ` • ${asset.environment}`}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with action buttons */}
      <div className="p-3 border-t bg-gray-50 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {selectedAssets.length} asset{selectedAssets.length !== 1 ? 's' : ''} selected
          {filteredAssets.length > 0 && ` • ${filteredAssets.length} available`}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSelectedAssets([]);
              handleClose();
            }}
          >
            Cancel
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleClose}
          >
            Done
          </Button>
        </div>
      </div>
    </div>
  );
});

DependencyCellEditor.displayName = 'DependencyCellEditor';
