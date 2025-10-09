/**
 * ApplicationCard Component
 * Individual card for displaying and selecting an asset
 */

import React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Activity, Eye } from "lucide-react";
import type { Asset } from "@/types/asset";

interface ApplicationCardProps {
  asset: Asset;
  isSelected: boolean;
  onToggle: (assetId: string) => void;
}

export const ApplicationCard: React.FC<ApplicationCardProps> = ({
  asset,
  isSelected,
  onToggle,
}) => {
  return (
    <div
      className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
        isSelected
          ? "border-blue-200 bg-blue-50"
          : "border-gray-200 hover:bg-gray-50"
      }`}
    >
      <label className="flex items-center space-x-3 cursor-pointer flex-1">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggle(asset.id.toString())}
        />
        <div className="flex-1">
          <div className="font-medium">
            {asset.name || "Unnamed Application"}
          </div>

          {/* CRITICAL: Asset ID display for debugging */}
          {asset.id && (
            <div className="text-xs text-gray-500 font-mono mt-1">
              Asset ID: {asset.id}
            </div>
          )}

          {asset.environment && (
            <div className="text-sm text-gray-600">
              Environment: {asset.environment}
            </div>
          )}
          {asset.description && (
            <div className="text-sm text-gray-500 mt-1 max-h-10 overflow-hidden">
              {asset.description.length > 100
                ? `${asset.description.substring(0, 100)}...`
                : asset.description}
            </div>
          )}
        </div>
      </label>
      <div className="flex items-center gap-2">
        {/* Status Indicator */}
        <Badge
          variant={asset.status === "active" ? "default" : "secondary"}
          className="flex items-center gap-1"
        >
          {asset.status === "active" ? (
            <Activity className="h-3 w-3" />
          ) : (
            <Eye className="h-3 w-3" />
          )}
          {asset.status === "active" ? "Active" : "Discovered"}
        </Badge>

        {asset.business_criticality && (
          <Badge
            variant={
              asset.business_criticality.toLowerCase() === "critical" ||
              asset.business_criticality.toLowerCase() === "high"
                ? "destructive"
                : asset.business_criticality.toLowerCase() === "medium"
                  ? "secondary"
                  : "default"
            }
          >
            {asset.business_criticality}
          </Badge>
        )}
        {asset.six_r_strategy && (
          <Badge variant="outline">{asset.six_r_strategy}</Badge>
        )}
      </div>
    </div>
  );
};
