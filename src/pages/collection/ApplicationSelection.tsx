import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  useInfiniteQuery,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  Cpu,
  ArrowLeft,
  ArrowRight,
  Search,
  Filter,
  Activity,
  Eye,
  Server,
  Database,
  Network,
  HardDrive,
  Shield,
  Cloud,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiCall } from "@/config/api";
import { toast } from "@/components/ui/use-toast";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import { FLOW_PHASE_ROUTES } from "@/config/flowRoutes";
import { collectionFlowApi } from "@/services/api/collection-flow";
import type { Asset } from "@/types/asset";

/**
 * ApplicationSelection page component
 * Allows users to select applications for a Collection flow before proceeding with questionnaire generation
 */
const ApplicationSelection: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { client, engagement } = useAuth();
  const queryClient = useQueryClient();

  // Get flow ID from URL params
  const flowId = searchParams.get("flowId");

  // State management
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(
    new Set(),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [environmentFilter, setEnvironmentFilter] = useState("");
  const [criticalityFilter, setCriticalityFilter] = useState("");
  const [selectedAssetTypes, setSelectedAssetTypes] = useState<Set<string>>(
    new Set(["ALL"]), // Default to showing all asset types
  );

  // Refs for infinite scroll
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

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

  // Build query parameters for API calls including filters
  const buildQueryParams = useCallback(
    (page: number) => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "50", // Optimal page size for smooth scrolling
      });

      // CRITICAL FIX: Add client_account_id and engagement_id for multi-tenant scoping
      // Without these, the query returns 0 assets even if inventory exists
      if (client?.account_id) {
        params.append("client_account_id", client.account_id.toString());
      }
      if (engagement?.id) {
        params.append("engagement_id", engagement.id.toString());
      }

      // Add client-side filters to server request for proper pagination
      if (searchTerm.trim()) {
        params.append("search", searchTerm.trim());
      }
      if (environmentFilter) {
        params.append("environment", environmentFilter);
      }
      if (criticalityFilter) {
        params.append("business_criticality", criticalityFilter);
      }

      return params.toString();
    },
    [searchTerm, environmentFilter, criticalityFilter, client, engagement],
  );

  // Fetch applications with infinite scroll support
  const {
    data: applicationsData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: applicationsLoading,
    error: applicationsError,
    refetch: refetchApplications,
  } = useInfiniteQuery({
    queryKey: [
      "applications-for-collection",
      client?.id,
      engagement?.id,
      searchTerm,
      environmentFilter,
      criticalityFilter,
    ],
    queryFn: async ({ pageParam = 1 }) => {
      try {
        const queryParams = buildQueryParams(pageParam);
        const response = await apiCall(
          `/asset-inventory/list/paginated?${queryParams}`,
        );

        if (!response || !response.assets) {
          throw new Error("Invalid API response structure");
        }

        console.log(
          `📋 Fetched page ${pageParam}: ${response.assets.length} applications (total: ${response.pagination?.total_count || "unknown"})`,
        );

        return {
          assets: response.assets,
          pagination: response.pagination,
          currentPage: pageParam,
        };
      } catch (error) {
        console.error("❌ Failed to fetch applications:", error);
        throw error;
      }
    },
    getNextPageParam: (lastPage) => {
      const { pagination } = lastPage;
      return pagination?.has_next ? pagination.current_page + 1 : undefined;
    },
    enabled: !!client && !!engagement && !!flowId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Flatten all pages into a single array of assets
  const allAssets =
    applicationsData?.pages?.flatMap((page) => page.assets) || [];

  // Group assets by type with counts
  const assetsByType = useMemo(() => {
    const grouped: Record<string, Asset[]> = {
      ALL: allAssets,
      APPLICATION: [],
      SERVER: [],
      DATABASE: [],
      NETWORK_DEVICE: [],
      STORAGE_DEVICE: [],
      SECURITY_DEVICE: [],
      VIRTUALIZATION: [],
      UNKNOWN: [],
    };

    allAssets.forEach((asset) => {
      const type = asset.asset_type?.toUpperCase() || "UNKNOWN";
      if (grouped[type]) {
        grouped[type].push(asset);
      } else {
        grouped.UNKNOWN.push(asset);
      }
    });

    return grouped;
  }, [allAssets]);

  // Filter assets based on selected asset types
  const filteredAssets = useMemo(() => {
    if (selectedAssetTypes.has("ALL")) {
      return allAssets;
    }

    return allAssets.filter((asset) =>
      selectedAssetTypes.has(asset.asset_type?.toUpperCase() || "UNKNOWN"),
    );
  }, [allAssets, selectedAssetTypes]);

  // For backward compatibility, keep this name but it now includes all asset types
  const filteredApplications = filteredAssets;
  const totalApplicationsCount = filteredAssets.length;

  // Fetch current collection flow details to check existing selections
  const { data: collectionFlow, isLoading: flowLoading } = useQuery({
    queryKey: ["collection-flow", flowId],
    queryFn: async () => {
      if (!flowId) return null;
      try {
        return await apiCall(`/collection/flows/${flowId}`);
      } catch (error) {
        console.error("Failed to fetch collection flow:", error);
        return null;
      }
    },
    enabled: !!flowId,
  });

  // Pre-populate selections if flow already has applications
  useEffect(() => {
    if (collectionFlow?.collection_config?.selected_application_ids) {
      const existingSelections =
        collectionFlow.collection_config.selected_application_ids;
      setSelectedApplications(new Set(existingSelections));
      console.log(
        `🔄 Pre-populated ${existingSelections.length} existing application selections`,
      );
    }
  }, [collectionFlow]);

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
          console.log("📄 Loading next page of assets...");
          fetchNextPage();
        }
      },
      {
        threshold: 0.1,
        rootMargin: "100px",
      },
    );

    observerRef.current.observe(loadMoreRef.current);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Handle application selection toggle
  const handleToggleApplication = (appId: string) => {
    const newSelection = new Set(selectedApplications);
    if (newSelection.has(appId)) {
      newSelection.delete(appId);
    } else {
      newSelection.add(appId);
    }
    setSelectedApplications(newSelection);
  };

  // Handle select all applications (filtered)
  const handleSelectAll = (checked?: boolean) => {
    if (!filteredApplications) return;
    const shouldSelectAll =
      typeof checked === "boolean"
        ? checked
        : selectedApplications.size !== filteredApplications.length;
    setSelectedApplications(
      shouldSelectAll
        ? new Set(filteredApplications.map((app: Asset) => app.id))
        : new Set(),
    );
  };

  // Get unique filter options from all loaded assets
  const environmentOptions = [
    ...new Set(allAssets.map((app) => app.environment).filter(Boolean)),
  ];
  const criticalityOptions = [
    ...new Set(
      allAssets.map((app) => app.business_criticality).filter(Boolean),
    ),
  ];

  // Reset to first page when filters change
  useEffect(() => {
    // Invalidate and refetch when filters change to reset pagination
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

      // Submit selected applications to the collection flow
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
        // CRITICAL: Invalidate collection flow cache so AdaptiveForms fetches updated data
        await queryClient.invalidateQueries({
          queryKey: ["collection-flow", flowId],
          exact: true,
        });

        // Also invalidate any related collection flow queries
        await queryClient.invalidateQueries({
          queryKey: ["collection-flows"],
        });

        console.log(
          `✅ Cache invalidated for flow ${flowId} after application selection`,
        );

        toast({
          title: "Assets Selected",
          description: `Successfully selected ${selectedApplications.size} asset${selectedApplications.size > 1 ? "s" : ""} for collection.`,
          variant: "default",
        });

        // Navigate based on flow phase (not hardcoded path)
        try {
          const flowDetails = await collectionFlowApi.getFlow(flowId);
          const currentPhase = flowDetails.current_phase || "gap_analysis";
          const phaseRoute = FLOW_PHASE_ROUTES.collection[currentPhase];

          if (phaseRoute) {
            const targetRoute = phaseRoute(flowId);
            console.log(
              `🧭 Navigating to ${currentPhase} phase: ${targetRoute}`,
            );
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

  // Handle cancel - go back to collection overview
  const handleCancel = () => {
    navigate("/collection");
  };

  // Show loading state
  if (applicationsLoading || flowLoading) {
    return (
      <CollectionPageLayout
        title="Select Assets"
        description="Choose assets for data collection"
        isLoading={true}
        loadingMessage="Loading available assets..."
        loadingSubMessage="Fetching inventory data"
      >
        {/* Loading handled by layout */}
      </CollectionPageLayout>
    );
  }

  // Show error state
  if (applicationsError) {
    return (
      <CollectionPageLayout
        title="Select Assets"
        description="Choose assets for data collection"
      >
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load assets. Please try again or contact support if the
            issue persists.
          </AlertDescription>
        </Alert>
        <div className="mt-4 flex gap-2">
          <Button onClick={handleCancel} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Collection
          </Button>
          <Button onClick={() => refetchApplications()}>Retry</Button>
        </div>
      </CollectionPageLayout>
    );
  }

  // Main component render
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
                {/* Asset Type Selection */}
                <div className="space-y-3 pb-4 border-b">
                  <Label className="text-sm font-medium">Asset Types</Label>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant={
                        selectedAssetTypes.has("ALL") ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() => setSelectedAssetTypes(new Set(["ALL"]))}
                    >
                      All Assets ({allAssets.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("APPLICATION")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("APPLICATION")) {
                          newSet.delete("APPLICATION");
                        } else {
                          newSet.add("APPLICATION");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Cpu className="h-3 w-3 mr-1" />
                      Applications ({assetsByType.APPLICATION.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("SERVER") ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("SERVER")) {
                          newSet.delete("SERVER");
                        } else {
                          newSet.add("SERVER");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Server className="h-3 w-3 mr-1" />
                      Servers ({assetsByType.SERVER.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("DATABASE")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("DATABASE")) {
                          newSet.delete("DATABASE");
                        } else {
                          newSet.add("DATABASE");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Database className="h-3 w-3 mr-1" />
                      Databases ({assetsByType.DATABASE.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("NETWORK_DEVICE")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("NETWORK_DEVICE")) {
                          newSet.delete("NETWORK_DEVICE");
                        } else {
                          newSet.add("NETWORK_DEVICE");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Network className="h-3 w-3 mr-1" />
                      Network ({assetsByType.NETWORK_DEVICE.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("STORAGE_DEVICE")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("STORAGE_DEVICE")) {
                          newSet.delete("STORAGE_DEVICE");
                        } else {
                          newSet.add("STORAGE_DEVICE");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <HardDrive className="h-3 w-3 mr-1" />
                      Storage ({assetsByType.STORAGE_DEVICE.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("SECURITY_DEVICE")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("SECURITY_DEVICE")) {
                          newSet.delete("SECURITY_DEVICE");
                        } else {
                          newSet.add("SECURITY_DEVICE");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Shield className="h-3 w-3 mr-1" />
                      Security ({assetsByType.SECURITY_DEVICE.length})
                    </Button>

                    <Button
                      variant={
                        selectedAssetTypes.has("VIRTUALIZATION")
                          ? "default"
                          : "outline"
                      }
                      size="sm"
                      onClick={() => {
                        const newSet = new Set(selectedAssetTypes);
                        newSet.delete("ALL");
                        if (newSet.has("VIRTUALIZATION")) {
                          newSet.delete("VIRTUALIZATION");
                        } else {
                          newSet.add("VIRTUALIZATION");
                        }
                        setSelectedAssetTypes(
                          newSet.size === 0 ? new Set(["ALL"]) : newSet,
                        );
                      }}
                    >
                      <Cloud className="h-3 w-3 mr-1" />
                      Virtualization ({assetsByType.VIRTUALIZATION.length})
                    </Button>
                  </div>
                </div>

                {/* Search and Filter Controls */}
                <div className="space-y-4 pb-4 border-b">
                  <div className="flex flex-col sm:flex-row gap-4">
                    {/* Search */}
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        type="text"
                        placeholder="Search assets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>

                    {/* Environment Filter */}
                    <div className="sm:w-48">
                      <select
                        value={environmentFilter}
                        onChange={(e) => setEnvironmentFilter(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">All Environments</option>
                        {environmentOptions.map((env) => (
                          <option key={env} value={env}>
                            {env}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Criticality Filter */}
                    <div className="sm:w-48">
                      <select
                        value={criticalityFilter}
                        onChange={(e) => setCriticalityFilter(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">All Criticalities</option>
                        {criticalityOptions.map((crit) => (
                          <option key={crit} value={crit}>
                            {crit}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Results Summary */}
                  <div className="flex justify-between items-center text-sm text-gray-600">
                    <span>
                      Showing {filteredApplications.length} of{" "}
                      {totalApplicationsCount} applications
                      {(searchTerm || environmentFilter || criticalityFilter) &&
                        " (filtered)"}
                    </span>
                    {(searchTerm || environmentFilter || criticalityFilter) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSearchTerm("");
                          setEnvironmentFilter("");
                          setCriticalityFilter("");
                        }}
                      >
                        Clear Filters
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
                        selectedApplications.size ===
                          filteredApplications.length
                      }
                      onCheckedChange={(val) => handleSelectAll(!!val)}
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

                {/* Application List with Infinite Scroll */}
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {filteredApplications.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      {searchTerm || environmentFilter || criticalityFilter || !selectedAssetTypes.has("ALL") ? (
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
                  ) : (
                    <>
                      {filteredApplications.map((app: Asset) => (
                        <div
                          key={app.id}
                          className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                            selectedApplications.has(app.id)
                              ? "border-blue-200 bg-blue-50"
                              : "border-gray-200 hover:bg-gray-50"
                          }`}
                        >
                          <label className="flex items-center space-x-3 cursor-pointer flex-1">
                            <Checkbox
                              checked={selectedApplications.has(app.id)}
                              onCheckedChange={() =>
                                handleToggleApplication(app.id)
                              }
                            />
                            <div className="flex-1">
                              <div className="font-medium">
                                {app.name || "Unnamed Application"}
                              </div>

                              {/* CRITICAL FIX: Add Asset ID display */}
                              {app.id && (
                                <div className="text-xs text-gray-500 font-mono mt-1">
                                  Asset ID: {app.id}
                                </div>
                              )}

                              {app.environment && (
                                <div className="text-sm text-gray-600">
                                  Environment: {app.environment}
                                </div>
                              )}
                              {app.description && (
                                <div className="text-sm text-gray-500 mt-1 max-h-10 overflow-hidden">
                                  {app.description.length > 100
                                    ? `${app.description.substring(0, 100)}...`
                                    : app.description}
                                </div>
                              )}
                            </div>
                          </label>
                          <div className="flex items-center gap-2">
                            {/* CRITICAL FIX: Add Status Indicator */}
                            <Badge
                              variant={app.status === "active" ? "default" : "secondary"}
                              className="flex items-center gap-1"
                            >
                              {app.status === "active" ? (
                                <Activity className="h-3 w-3" />
                              ) : (
                                <Eye className="h-3 w-3" />
                              )}
                              {app.status === "active" ? "Active" : "Discovered"}
                            </Badge>

                            {app.business_criticality && (
                              <Badge
                                variant={
                                  app.business_criticality.toLowerCase() ===
                                    "critical" ||
                                  app.business_criticality.toLowerCase() ===
                                    "high"
                                    ? "destructive"
                                    : app.business_criticality.toLowerCase() ===
                                        "medium"
                                      ? "secondary"
                                      : "default"
                                }
                              >
                                {app.business_criticality}
                              </Badge>
                            )}
                            {app.six_r_strategy && (
                              <Badge variant="outline">
                                {app.six_r_strategy}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}

                      {/* Infinite Scroll Trigger - now works with server-side filtering */}
                      <div ref={loadMoreRef} className="py-4">
                        {isFetchingNextPage && (
                          <div className="flex items-center justify-center py-4">
                            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                            <span className="ml-2 text-sm text-gray-600">
                              Loading more assets...
                            </span>
                          </div>
                        )}
                        {!hasNextPage && filteredApplications.length > 0 && (
                          <div className="text-center py-4 text-gray-500 text-sm">
                            {searchTerm ||
                            environmentFilter ||
                            criticalityFilter
                              ? `Showing all ${filteredApplications.length} matching applications`
                              : `All applications loaded (${filteredApplications.length} total)`}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>

                {/* Selection Summary */}
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

                {/* Error Alert */}
                {submitError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{submitError}</AlertDescription>
                  </Alert>
                )}

                {/* Action Buttons */}
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
