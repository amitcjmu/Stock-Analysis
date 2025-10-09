/**
 * ApplicationGrid Component
 * Displays the grid of application cards with infinite scroll
 */

import React from "react";
import { Loader2, Filter, Activity } from "lucide-react";
import { ApplicationCard } from "./ApplicationCard";
import type { Asset } from "@/types/asset";

interface ApplicationGridProps {
  applications: Asset[];
  selectedApplications: Set<string>;
  onToggleApplication: (appId: string) => void;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
  loadMoreRef: React.RefObject<HTMLDivElement>;
  searchTerm: string;
  environmentFilter: string;
  criticalityFilter: string;
  selectedAssetTypesHasAll: boolean;
}

export const ApplicationGrid: React.FC<ApplicationGridProps> = ({
  applications,
  selectedApplications,
  onToggleApplication,
  isFetchingNextPage,
  hasNextPage,
  loadMoreRef,
  searchTerm,
  environmentFilter,
  criticalityFilter,
  selectedAssetTypesHasAll,
}) => {
  const hasFilters = searchTerm || environmentFilter || criticalityFilter || !selectedAssetTypesHasAll;

  if (applications.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {hasFilters ? (
          <div>
            <Filter className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p>No assets match your current filters.</p>
            <p className="text-sm mt-2">
              Try adjusting your search criteria or asset type selection.
            </p>
          </div>
        ) : (
          <div>
            <Activity className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p>No assets available.</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      {applications.map((app: Asset) => (
        <ApplicationCard
          key={app.id}
          asset={app}
          isSelected={selectedApplications.has(app.id.toString())}
          onToggle={onToggleApplication}
        />
      ))}

      {/* Infinite Scroll Trigger */}
      <div ref={loadMoreRef} className="py-4">
        {isFetchingNextPage && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-gray-600">
              Loading more assets...
            </span>
          </div>
        )}
        {!hasNextPage && applications.length > 0 && (
          <div className="text-center py-4 text-gray-500 text-sm">
            {hasFilters
              ? `Showing all ${applications.length} matching applications`
              : `All applications loaded (${applications.length} total)`}
          </div>
        )}
      </div>
    </>
  );
};
