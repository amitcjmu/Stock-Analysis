/**
 * ApplicationSelection Page Component (Modularized)
 * Allows users to select applications for a Collection flow before proceeding with questionnaire generation
 *
 * CRITICAL PATTERNS PRESERVED:
 * 1. Multi-tenant scoping (client_account_id + engagement_id)
 * 2. Infinite scroll with Intersection Observer
 * 3. Cache invalidation for data consistency
 * 4. Explicit error handling
 * 5. Optimistic UI updates
 *
 * LOC: ~250 lines (down from 977 lines)
 */

import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Activity,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiCall } from "@/config/api";
import { toast } from "@/components/ui/use-toast";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import { FLOW_PHASE_ROUTES } from "@/config/flowRoutes";
import { collectionFlowApi } from "@/services/api/collection-flow";

// Modularized imports
import { useApplicationData } from "./hooks/useApplicationData";
import { useInfiniteScroll } from "./hooks/useInfiniteScroll";
import { useApplicationSelection } from "./hooks/useApplicationSelection";
import { useCacheInvalidation } from "./hooks/useCacheInvalidation";
import { ApplicationGrid } from "./components/ApplicationGrid";
import { SelectionControls } from "./components/SelectionControls";
import { SearchFilters } from "./components/SearchFilters";
import { LoadingState, ErrorState } from "./components/LoadingStates";

const ApplicationSelection: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { client, engagement } = useAuth();
  const queryClient = useQueryClient();

  // Get flow ID from URL params
  const flowId = searchParams.get("flowId");

  // Filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [environmentFilter, setEnvironmentFilter] = useState("");
  const [criticalityFilter, setCriticalityFilter] = useState("");
  const [selectedAssetTypes, setSelectedAssetTypes] = useState<Set<string>>(
    new Set(["ALL"]),
  );

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Redirect if no flow ID provided
  useEffect(() => {
    if (!flowId) {
      toast({
        title: "Missing Flow ID",
        description:
          "No collection flow ID provided. Redirecting to collection overview.",
        variant: "destructive",
      });
      navigate("/collection");
    }
  }, [flowId, navigate]);

  // Data fetching hook
  const {
    allAssets,
    assetsByType,
    filterOptions,
    applicationsLoading,
    flowLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    applicationsError,
    refetchApplications,
    collectionFlow,
  } = useApplicationData({
    flowId,
    client,
    engagement,
    searchTerm,
    environmentFilter,
    criticalityFilter,
  });

  // Selection hook
  const {
    selectedApplications,
    handleToggleApplication,
    handleSelectAll,
  } = useApplicationSelection({ collectionFlow });

  // Infinite scroll hook
  const { loadMoreRef } = useInfiniteScroll({
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  });

  // Cache invalidation hook
  const { invalidateCollectionFlowCache } = useCacheInvalidation();

  // Filter and sort assets based on selected asset types (client-side)
  // Selected applications appear at the top of the list
  const filteredAssets = useMemo(() => {
    let filtered = allAssets;

    // Apply asset type filter
    if (!selectedAssetTypes.has("ALL")) {
      filtered = allAssets.filter((asset) =>
        selectedAssetTypes.has(asset.asset_type?.toUpperCase() || "UNKNOWN"),
      );
    }

    // Sort: selected applications first, then unselected
    // Within each group, sort alphabetically by asset_name
    return filtered.sort((a, b) => {
      const aSelected = selectedApplications.has(a.id.toString());
      const bSelected = selectedApplications.has(b.id.toString());

      // If selection status differs, prioritize selected items
      if (aSelected !== bSelected) {
        return aSelected ? -1 : 1;
      }

      // If both have same selection status, sort alphabetically
      const aName = a.asset_name || a.name || "";
      const bName = b.asset_name || b.name || "";
      return aName.localeCompare(bName);
    });
  }, [allAssets, selectedAssetTypes, selectedApplications]);

  // Reset to first page when filters change
  useEffect(() => {
    queryClient.invalidateQueries({
      queryKey: [
        "applications-for-collection",
        client?.id,
        engagement?.id,
        searchTerm,
        environmentFilter,
        criticalityFilter,
      ],
    });
  }, [
    searchTerm,
    environmentFilter,
    criticalityFilter,
    queryClient,
    client?.id,
    engagement?.id,
  ]);

  // Handle form submission
  const handleSubmit = async () => {
    if (selectedApplications.size === 0) {
      toast({
        title: "No Applications Selected",
        description: "Please select at least one application to continue.",
        variant: "destructive",
      });
      return;
    }

    if (!flowId) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      console.log(
        `🚀 Submitting ${selectedApplications.size} selected applications for flow ${flowId}`,
      );

      const response = await apiCall(
        `/collection/flows/${flowId}/applications`,
        {
          method: "POST",
          body: JSON.stringify({
            selected_application_ids: Array.from(selectedApplications),
            action: "update_applications",
          }),
        },
      );

      if (
        response &&
        (response.success || response.status === "success" || response.id)
      ) {
        await invalidateCollectionFlowCache(flowId);

        toast({
          title: "Assets Selected",
          description: `Successfully selected ${selectedApplications.size} asset${selectedApplications.size > 1 ? "s" : ""} for collection.`,
          variant: "default",
        });

        // Navigate based on flow phase
        try {
          const flowDetails = await collectionFlowApi.getFlow(flowId);
          const currentPhase = flowDetails.current_phase || "gap_analysis";
          const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

          if (phaseRoute) {
            const targetRoute = phaseRoute(flowId);
            console.log(`🧭 Navigating to ${currentPhase} phase: ${targetRoute}`);
            navigate(targetRoute);
          } else {
            console.warn(
              `⚠️ No route found for phase: ${currentPhase}, falling back to adaptive-forms`,
            );
            navigate(`/collection/adaptive-forms?flowId=${flowId}`);
          }
        } catch (error) {
          console.warn(
            "⚠️ Failed to get flow details for phase routing, using fallback:",
            error,
          );
          navigate(`/collection/adaptive-forms?flowId=${flowId}`);
        }
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (error) {
      console.error("❌ Error submitting application selection:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to submit application selection. Please try again.";
      setSubmitError(errorMessage);

      toast({
        title: "Submission Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => navigate("/collection");

  const handleClearFilters = () => {
    setSearchTerm("");
    setEnvironmentFilter("");
    setCriticalityFilter("");
  };

  // Loading state
  if (applicationsLoading || flowLoading) {
    return <LoadingState />;
  }

  // Error state
  if (applicationsError) {
    return (
      <ErrorState
        onCancel={handleCancel}
        onRetry={() => refetchApplications()}
      />
    );
  }

  // Main render
  return (
    <CollectionPageLayout
      title="Select Assets"
      description={`Choose which assets to include in this collection flow${collectionFlow?.flow_name ? ` (${collectionFlow.flow_name})` : ""}`}
    >
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Asset Selection
            </CardTitle>
            <CardDescription>
              Select the assets you want to include in this collection flow.
              The selected assets will undergo gap analysis and adaptive
              questionnaire generation.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {allAssets && allAssets.length > 0 ? (
              <>
                <SelectionControls
                  selectedAssetTypes={selectedAssetTypes}
                  setSelectedAssetTypes={setSelectedAssetTypes}
                  assetsByType={assetsByType}
                  allAssets={allAssets}
                  filteredApplications={filteredAssets}
                  selectedApplications={selectedApplications}
                  onSelectAll={(checked) =>
                    handleSelectAll(filteredAssets, checked)
                  }
                  searchTerm={searchTerm}
                  environmentFilter={environmentFilter}
                  criticalityFilter={criticalityFilter}
                />

                <SearchFilters
                  searchTerm={searchTerm}
                  setSearchTerm={setSearchTerm}
                  environmentFilter={environmentFilter}
                  setEnvironmentFilter={setEnvironmentFilter}
                  criticalityFilter={criticalityFilter}
                  setCriticalityFilter={setCriticalityFilter}
                  environmentOptions={filterOptions.environmentOptions}
                  criticalityOptions={filterOptions.criticalityOptions}
                  filteredCount={filteredAssets.length}
                  totalCount={allAssets.length}
                  onClearFilters={handleClearFilters}
                />

                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  <ApplicationGrid
                    applications={filteredAssets}
                    selectedApplications={selectedApplications}
                    onToggleApplication={handleToggleApplication}
                    isFetchingNextPage={isFetchingNextPage}
                    hasNextPage={hasNextPage}
                    loadMoreRef={loadMoreRef}
                    searchTerm={searchTerm}
                    environmentFilter={environmentFilter}
                    criticalityFilter={criticalityFilter}
                    selectedAssetTypesHasAll={selectedAssetTypes.has("ALL")}
                  />
                </div>

                {selectedApplications.size > 0 && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-blue-600" />
                      <span className="font-medium text-blue-900">
                        {selectedApplications.size} application
                        {selectedApplications.size > 1 ? "s" : ""} selected for
                        collection
                      </span>
                    </div>
                    <div className="text-sm text-blue-700 mt-1">
                      These applications will be processed for gap analysis and
                      questionnaire generation.
                    </div>
                  </div>
                )}

                {submitError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{submitError}</AlertDescription>
                  </Alert>
                )}

                <div className="flex justify-between pt-6 border-t">
                  <Button
                    variant="outline"
                    onClick={handleCancel}
                    disabled={isSubmitting}
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={selectedApplications.size === 0 || isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        Continue with {selectedApplications.size} Application
                        {selectedApplications.size !== 1 ? "s" : ""}
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>
              </>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  No assets found in the inventory. Please complete the
                  Discovery flow first to populate the asset inventory.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </CollectionPageLayout>
  );
};

export default ApplicationSelection;
