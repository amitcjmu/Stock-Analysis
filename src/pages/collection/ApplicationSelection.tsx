import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
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
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiCall } from "@/config/api";
import { toast } from "@/components/ui/use-toast";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
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
  const buildQueryParams = useCallback((page: number) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: "50", // Optimal page size for smooth scrolling
      asset_type: "application", // Backend filter for applications only
    });

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
  }, [searchTerm, environmentFilter, criticalityFilter]);

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
      criticalityFilter
    ],
    queryFn: async ({ pageParam = 1 }) => {
      try {
        const queryParams = buildQueryParams(pageParam);
        const response = await apiCall(
          `/unified-discovery/assets?${queryParams}`,
        );

        if (!response || !response.assets) {
          throw new Error("Invalid API response structure");
        }

        console.log(
          `📋 Fetched page ${pageParam}: ${response.assets.length} applications (total: ${response.pagination?.total_count || 'unknown'})`,
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
      return pagination?.has_next ? pagination.page + 1 : undefined;
    },
    enabled: !!client && !!engagement && !!flowId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Flatten all pages into a single array of applications
  const applications = applicationsData?.pages?.flatMap(page => page.assets) || [];
  const totalApplicationsCount = applicationsData?.pages?.[0]?.pagination?.total_count || 0;

  // Since server-side filtering is now applied, we use applications directly without client-side filtering
  const filteredApplications = applications;

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
          console.log("📄 Loading next page of applications...");
          fetchNextPage();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '100px',
      }
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
    const shouldSelectAll = typeof checked === "boolean"
      ? checked
      : selectedApplications.size !== filteredApplications.length;
    setSelectedApplications(
      shouldSelectAll ? new Set(filteredApplications.map((app: Asset) => app.id)) : new Set()
    );
  };

  // Get unique filter options from all loaded applications
  const environmentOptions = [...new Set(applications.map(app => app.environment).filter(Boolean))];
  const criticalityOptions = [...new Set(applications.map(app => app.business_criticality).filter(Boolean))];

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
        criticalityFilter
      ]
    });
  }, [searchTerm, environmentFilter, criticalityFilter, queryClient, client?.id, engagement?.id]);

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
          title: "Applications Selected",
          description: `Successfully selected ${selectedApplications.size} application${selectedApplications.size > 1 ? "s" : ""} for collection.`,
          variant: "default",
        });

        // Navigate to the adaptive forms to continue the flow
        navigate(`/collection/adaptive-forms?flowId=${flowId}`);
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
        title="Select Applications"
        description="Choose applications for data collection"
        isLoading={true}
        loadingMessage="Loading available applications..."
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
        title="Select Applications"
        description="Choose applications for data collection"
      >
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load applications. Please try again or contact support if
            the issue persists.
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
      title="Select Applications"
      description={`Choose which applications to include in this collection flow${collectionFlow?.flow_name ? ` (${collectionFlow.flow_name})` : ""}`}
    >
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Application Selection
            </CardTitle>
            <CardDescription>
              Select the applications you want to include in this collection
              flow. The selected applications will undergo gap analysis and
              adaptive questionnaire generation.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {applications && applications.length > 0 ? (
              <>
                {/* Search and Filter Controls */}
                <div className="space-y-4 pb-4 border-b">
                  <div className="flex flex-col sm:flex-row gap-4">
                    {/* Search */}
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        type="text"
                        placeholder="Search applications..."
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
                          <option key={env} value={env}>{env}</option>
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
                          <option key={crit} value={crit}>{crit}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Results Summary */}
                  <div className="flex justify-between items-center text-sm text-gray-600">
                    <span>
                      Showing {filteredApplications.length} of {totalApplicationsCount} applications
                      {(searchTerm || environmentFilter || criticalityFilter) && ' (filtered)'}
                    </span>
                    {(searchTerm || environmentFilter || criticalityFilter) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSearchTerm('');
                          setEnvironmentFilter('');
                          setCriticalityFilter('');
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
                        filteredApplications.length > 0 && selectedApplications.size === filteredApplications.length
                      }
                      onCheckedChange={(val) => handleSelectAll(!!val)}
                    />
                    <span className="font-medium">
                      Select All ({filteredApplications.length} applications {(searchTerm || environmentFilter || criticalityFilter) ? 'shown' : 'available'})
                    </span>
                  </label>
                </div>

                {/* Application List with Infinite Scroll */}
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {filteredApplications.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      {searchTerm || environmentFilter || criticalityFilter ? (
                        <div>
                          <Filter className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                          <p>No applications match your current filters.</p>
                          <p className="text-sm mt-2">Try adjusting your search criteria.</p>
                        </div>
                      ) : (
                        <div>
                          <Cpu className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                          <p>No applications available.</p>
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
                              <div className="font-medium">{app.name || 'Unnamed Application'}</div>
                              {app.environment && (
                                <div className="text-sm text-gray-600">
                                  Environment: {app.environment}
                                </div>
                              )}
                              {app.description && (
                                <div className="text-sm text-gray-500 mt-1 max-h-10 overflow-hidden">
                                  {app.description.length > 100 ? `${app.description.substring(0, 100)}...` : app.description}
                                </div>
                              )}
                            </div>
                          </label>
                          <div className="flex items-center gap-2">
                            {app.business_criticality && (
                              <Badge
                                variant={
                                  app.business_criticality.toLowerCase() === "critical" || app.business_criticality.toLowerCase() === "high"
                                    ? "destructive"
                                    : app.business_criticality.toLowerCase() === "medium"
                                      ? "secondary"
                                      : "default"
                                }
                              >
                                {app.business_criticality}
                              </Badge>
                            )}
                            {app.six_r_strategy && (
                              <Badge variant="outline">{app.six_r_strategy}</Badge>
                            )}
                          </div>
                        </div>
                      ))}

                      {/* Infinite Scroll Trigger - now works with server-side filtering */}
                      <div ref={loadMoreRef} className="py-4">
                        {isFetchingNextPage && (
                          <div className="flex items-center justify-center py-4">
                            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                            <span className="ml-2 text-sm text-gray-600">Loading more applications...</span>
                          </div>
                        )}
                        {!hasNextPage && applications.length > 0 && (
                          <div className="text-center py-4 text-gray-500 text-sm">
                            {(searchTerm || environmentFilter || criticalityFilter)
                              ? `Showing all ${applications.length} matching applications`
                              : `All applications loaded (${applications.length} total)`
                            }
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
                  No applications found in the inventory. Please complete the
                  Discovery flow first to populate the application inventory.
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
