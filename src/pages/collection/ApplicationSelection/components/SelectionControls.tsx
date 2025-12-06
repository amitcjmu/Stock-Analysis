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
  summary: {
    applications: number;
    servers: number;
    databases: number;
    components: number;
    network: number;
    storage: number;
    security: number;
    virtualization: number;
    unknown: number;
  } | null;
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
  summary,
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

          {(summary?.applications ?? assetsByType.APPLICATION.length) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("APPLICATION") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("APPLICATION")}
            >
              <Cpu className="h-3 w-3 mr-1" />
              Applications ({summary?.applications ?? assetsByType.APPLICATION.length})
            </Button>
          )}

          {(summary?.servers ?? assetsByType.SERVER.length) > 0 && (
            <Button
              variant={selectedAssetTypes.has("SERVER") ? "default" : "outline"}
              size="sm"
              onClick={() => toggleAssetType("SERVER")}
            >
              <Server className="h-3 w-3 mr-1" />
              Servers ({summary?.servers ?? assetsByType.SERVER.length})
            </Button>
          )}

          {(summary?.databases ?? assetsByType.DATABASE.length) > 0 && (
            <Button
              variant={selectedAssetTypes.has("DATABASE") ? "default" : "outline"}
              size="sm"
              onClick={() => toggleAssetType("DATABASE")}
            >
              <Database className="h-3 w-3 mr-1" />
              Databases ({summary?.databases ?? assetsByType.DATABASE.length})
            </Button>
          )}

          {(summary?.components ?? 0) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("COMPONENT") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("COMPONENT")}
            >
              <Cpu className="h-3 w-3 mr-1" />
              Components ({summary?.components ?? 0})
            </Button>
          )}

          {/* Bug #971 Fix: Use NETWORK instead of NETWORK_DEVICE to match normalization */}
          {(summary?.network ?? assetsByType.NETWORK.length) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("NETWORK") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("NETWORK")}
            >
              <Network className="h-3 w-3 mr-1" />
              Network ({summary?.network ?? assetsByType.NETWORK.length})
            </Button>
          )}

          {(summary?.storage ?? assetsByType.STORAGE_DEVICE.length) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("STORAGE_DEVICE") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("STORAGE_DEVICE")}
            >
              <HardDrive className="h-3 w-3 mr-1" />
              Storage ({summary?.storage ?? assetsByType.STORAGE_DEVICE.length})
            </Button>
          )}

          {(summary?.security ?? assetsByType.SECURITY_DEVICE.length) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("SECURITY_DEVICE") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("SECURITY_DEVICE")}
            >
              <Shield className="h-3 w-3 mr-1" />
              Security ({summary?.security ?? assetsByType.SECURITY_DEVICE.length})
            </Button>
          )}

          {(summary?.virtualization ?? assetsByType.VIRTUALIZATION.length) > 0 && (
            <Button
              variant={
                selectedAssetTypes.has("VIRTUALIZATION") ? "default" : "outline"
              }
              size="sm"
              onClick={() => toggleAssetType("VIRTUALIZATION")}
            >
              <Cloud className="h-3 w-3 mr-1" />
              Virtualization ({summary?.virtualization ?? assetsByType.VIRTUALIZATION.length})
            </Button>
          )}
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
