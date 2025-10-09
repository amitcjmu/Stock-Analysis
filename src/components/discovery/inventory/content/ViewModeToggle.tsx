import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface ViewModeToggleProps {
  viewMode: 'all' | 'current_flow';
  setViewMode: (mode: 'all' | 'current_flow') => void;
  setCurrentPage: (page: number) => void;
  hasFlowId: boolean;
  assetsLoading: boolean;
  flowId?: string;
}

export const ViewModeToggle: React.FC<ViewModeToggleProps> = ({
  viewMode,
  setViewMode,
  setCurrentPage,
  hasFlowId,
  assetsLoading,
  flowId
}) => {
  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Label htmlFor="view-mode-toggle" className="text-sm font-medium">
              View Mode:
            </Label>
            <div className="flex items-center space-x-2">
              <Label
                htmlFor="view-mode-toggle"
                className={`text-sm cursor-pointer ${
                  viewMode === 'all' ? 'text-blue-600 font-medium' : 'text-gray-600'
                }`}
              >
                All Assets
              </Label>
              <Switch
                id="view-mode-toggle"
                checked={viewMode === 'current_flow'}
                onCheckedChange={(checked) => {
                  if (assetsLoading) return; // Prevent toggling during loading
                  if (!hasFlowId && checked) return; // Guard against switching to current_flow without flowId
                  setViewMode(checked ? 'current_flow' : 'all');
                  setCurrentPage(1); // Reset pagination when switching modes
                }}
                disabled={!hasFlowId || assetsLoading} // Disable toggle if no flow is available or loading
                aria-disabled={!hasFlowId || assetsLoading}
                aria-busy={assetsLoading}
              />
              <Label
                htmlFor="view-mode-toggle"
                className={`text-sm cursor-pointer ${
                  viewMode === 'current_flow' ? 'text-blue-600 font-medium' : 'text-gray-600'
                }`}
              >
                Current Flow Only
              </Label>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {viewMode === 'all'
              ? 'Showing all assets for this client and engagement'
              : hasFlowId
                ? `Showing assets for flow: ${String(flowId).substring(0, 8)}...`
                : 'No flow selected'
            }
          </div>
        </div>
        {!hasFlowId && (
          <div className="mt-2 text-xs text-amber-600">
            ⚠️ No flow selected - only "All Assets" view is available
          </div>
        )}
      </CardContent>
    </Card>
  );
};
