/**
 * SelectionControls Component
 * Displays asset type filters and select all checkbox
 */

import React from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Cpu,
  Server,
  Database,
  Network,
  HardDrive,
  Shield,
  Cloud,
} from "lucide-react";
import type { Asset } from "@/types/asset";
import type { AssetsByType } from "../types";

interface SelectionControlsProps {
  selectedAssetTypes: Set<string>;
  setSelectedAssetTypes: React.Dispatch<React.SetStateAction<Set<string>>>;
  assetsByType: AssetsByType;
  allAssets: Asset[];
  filteredApplications: Asset[];
  selectedApplications: Set<string>;
  onSelectAll: (checked: boolean) => void;
  searchTerm: string;
  environmentFilter: string;
  criticalityFilter: string;
}

export const SelectionControls: React.FC<SelectionControlsProps> = ({
  selectedAssetTypes,
  setSelectedAssetTypes,
  assetsByType,
  allAssets,
  filteredApplications,
  selectedApplications,
  onSelectAll,
  searchTerm,
  environmentFilter,
  criticalityFilter,
}) => {
  const toggleAssetType = (type: string) => {
    const newSet = new Set(selectedAssetTypes);
    newSet.delete("ALL");
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedAssetTypes(newSet.size === 0 ? new Set(["ALL"]) : newSet);
  };

  return (
    <>
      {/* Asset Type Selection */}
      <div className="space-y-3 pb-4 border-b">
        <Label className="text-sm font-medium">Asset Types</Label>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={selectedAssetTypes.has("ALL") ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedAssetTypes(new Set(["ALL"]))}
          >
            All Assets ({allAssets.length})
          </Button>

          <Button
            variant={
              selectedAssetTypes.has("APPLICATION") ? "default" : "outline"
            }
            size="sm"
            onClick={() => toggleAssetType("APPLICATION")}
          >
            <Cpu className="h-3 w-3 mr-1" />
            Applications ({assetsByType.APPLICATION.length})
          </Button>

          <Button
            variant={selectedAssetTypes.has("SERVER") ? "default" : "outline"}
            size="sm"
            onClick={() => toggleAssetType("SERVER")}
          >
            <Server className="h-3 w-3 mr-1" />
            Servers ({assetsByType.SERVER.length})
          </Button>

          <Button
            variant={selectedAssetTypes.has("DATABASE") ? "default" : "outline"}
            size="sm"
            onClick={() => toggleAssetType("DATABASE")}
          >
            <Database className="h-3 w-3 mr-1" />
            Databases ({assetsByType.DATABASE.length})
          </Button>

          {/* Bug #971 Fix: Use NETWORK instead of NETWORK_DEVICE to match normalization */}
          <Button
            variant={
              selectedAssetTypes.has("NETWORK") ? "default" : "outline"
            }
            size="sm"
            onClick={() => toggleAssetType("NETWORK")}
          >
            <Network className="h-3 w-3 mr-1" />
            Network ({assetsByType.NETWORK.length})
          </Button>

          <Button
            variant={
              selectedAssetTypes.has("STORAGE_DEVICE") ? "default" : "outline"
            }
            size="sm"
            onClick={() => toggleAssetType("STORAGE_DEVICE")}
          >
            <HardDrive className="h-3 w-3 mr-1" />
            Storage ({assetsByType.STORAGE_DEVICE.length})
          </Button>

          <Button
            variant={
              selectedAssetTypes.has("SECURITY_DEVICE") ? "default" : "outline"
            }
            size="sm"
            onClick={() => toggleAssetType("SECURITY_DEVICE")}
          >
            <Shield className="h-3 w-3 mr-1" />
            Security ({assetsByType.SECURITY_DEVICE.length})
          </Button>

          <Button
            variant={
              selectedAssetTypes.has("VIRTUALIZATION") ? "default" : "outline"
            }
            size="sm"
            onClick={() => toggleAssetType("VIRTUALIZATION")}
          >
            <Cloud className="h-3 w-3 mr-1" />
            Virtualization ({assetsByType.VIRTUALIZATION.length})
          </Button>
        </div>
      </div>

      {/* Select All Checkbox */}
      <div className="pb-4 border-b">
        <label className="flex items-center space-x-2 cursor-pointer">
          <Checkbox
            checked={
              filteredApplications.length > 0 &&
              selectedApplications.size === filteredApplications.length
            }
            onCheckedChange={(val) => onSelectAll(!!val)}
          />
          <span className="font-medium">
            Select All ({filteredApplications.length} applications{" "}
            {searchTerm || environmentFilter || criticalityFilter
              ? "shown"
              : "available"}
            )
          </span>
        </label>
      </div>
    </>
  );
};
