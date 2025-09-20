import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ArrowLeft,
  ArrowRight,
  AlertCircle,
  Cpu,
  Plus,
  List,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiCall } from "@/config/api";
import { toast } from "@/components/ui/use-toast";
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import { ApplicationDeduplicationManager } from "@/components/collection/application-input";
import type { Asset } from "@/types/asset";
import type { CanonicalApplicationSelection } from "@/types/collection/canonical-applications";

/**
 * EnhancedApplicationSelection Component
 *
 * Enhanced version of ApplicationSelection that supports both:
 * 1. Traditional selection from existing asset inventory
 * 2. New free-form application input with deduplication
 *
 * This provides a smooth migration path and flexibility for different use cases.
 */
const EnhancedApplicationSelection: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { client, engagement } = useAuth();
  const queryClient = useQueryClient();

  const flowId = searchParams.get("flowId");
  const [activeTab, setActiveTab] = useState<"inventory" | "freeform">("freeform");
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(new Set());
  const [canonicalApplications, setCanonicalApplications] = useState<CanonicalApplicationSelection[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Redirect if no flow ID provided
  useEffect(() => {
    if (!flowId) {
      toast({
        title: "Missing Flow ID",
        description: "No collection flow ID provided. Redirecting to collection overview.",
        variant: "destructive",
      });
      navigate("/collection");
    }
  }, [flowId, navigate]);

  // Fetch existing assets for inventory tab
  const {
    data: assetsData,
    isLoading: assetsLoading,
    error: assetsError,
  } = useQuery({
    queryKey: ["applications-for-collection", client?.id, engagement?.id],
    queryFn: async () => {
      if (!client || !engagement) return { assets: [], pagination: null };
      const queryParams = new URLSearchParams({
        page: "1",
        page_size: "1000",
        asset_type: "application",
      });
      return await apiCall(`/unified-discovery/assets?${queryParams.toString()}`);
    },
    enabled: !!client && !!engagement && !!flowId && activeTab === "inventory",
  });

  // Fetch current collection flow details
  const { data: collectionFlow } = useQuery({
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

  // Pre-populate selections from existing flow
  useEffect(() => {
    if (collectionFlow?.collection_config?.selected_application_ids) {
      setSelectedApplications(new Set(collectionFlow.collection_config.selected_application_ids));
    }
  }, [collectionFlow]);

  // Handle inventory application toggle
  const handleToggleApplication = (appId: string) => {
    const newSelection = new Set(selectedApplications);
    if (newSelection.has(appId)) {
      newSelection.delete(appId);
    } else {
      newSelection.add(appId);
    }
    setSelectedApplications(newSelection);
  };

  // Handle canonical applications change
  const handleCanonicalApplicationsChange = (apps: CanonicalApplicationSelection[]) => {
    setCanonicalApplications(apps);
  };

  // Calculate total applications selected
  const totalSelected = selectedApplications.size + canonicalApplications.length;

  // Handle form submission
  const handleSubmit = async () => {
    if (totalSelected === 0) {
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
      console.log(`🚀 Submitting ${totalSelected} applications for flow ${flowId}`);

      // Prepare submission data
      const submissionData = {
        // Traditional asset-based selections
        selected_application_ids: Array.from(selectedApplications),
        // New canonical application selections
        canonical_applications: canonicalApplications,
        action: "update_applications",
        selection_metadata: {
          inventory_selections: selectedApplications.size,
          freeform_selections: canonicalApplications.length,
          total_selections: totalSelected,
          selection_method: activeTab === "inventory" ? "asset_based" : "canonical_based",
        },
      };

      const response = await apiCall(`/collection/flows/${flowId}/applications`, {
        method: "POST",
        body: JSON.stringify(submissionData),
      });

      if (response && (response.success || response.status === "success" || response.id)) {
        // Invalidate cache
        await queryClient.invalidateQueries({
          queryKey: ["collection-flow", flowId],
          exact: true,
        });

        toast({
          title: "Applications Selected",
          description: `Successfully selected ${totalSelected} application${totalSelected > 1 ? "s" : ""} for collection.`,
          variant: "default",
        });

        // Navigate to next step
        navigate(`/collection/adaptive-forms?flowId=${flowId}`);
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (error: any) {
      console.error("❌ Error submitting application selection:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to submit application selection. Please try again.";
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

  // Handle cancel
  const handleCancel = () => {
    navigate("/collection");
  };

  // Show loading state
  if (assetsLoading && activeTab === "inventory") {
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

  return (
    <CollectionPageLayout
      title="Select Applications"
      description={`Choose applications for collection flow${collectionFlow?.flow_name ? ` (${collectionFlow.flow_name})` : ""}`}
    >
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Application Selection
            </CardTitle>
            <CardDescription>
              Choose applications for this collection flow using either existing inventory or free-form entry with intelligent deduplication.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "inventory" | "freeform")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="freeform" className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Smart Entry (Recommended)
                </TabsTrigger>
                <TabsTrigger value="inventory" className="flex items-center gap-2">
                  <List className="h-4 w-4" />
                  From Inventory ({assetsData?.assets?.length || 0})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="freeform" className="space-y-6 mt-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">✨ Smart Application Entry</h3>
                  <p className="text-blue-800 text-sm">
                    Type application names freely and our AI will suggest existing applications and detect duplicates automatically.
                    This is the recommended approach for better data consistency and future suggestions.
                  </p>
                </div>

                <ApplicationDeduplicationManager
                  collectionFlowId={flowId}
                  initialApplications={[]}
                  onApplicationsChange={handleCanonicalApplicationsChange}
                  disabled={isSubmitting}
                  maxApplications={100}
                  showBulkImport={true}
                  showExportOptions={true}
                />
              </TabsContent>

              <TabsContent value="inventory" className="space-y-6 mt-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-900 mb-2">📋 Traditional Inventory Selection</h3>
                  <p className="text-yellow-800 text-sm">
                    Select from applications discovered in your inventory. Note: This may include duplicates and variations that haven't been normalized.
                  </p>
                </div>

                {assetsError ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Failed to load inventory applications. Please try the Smart Entry tab or refresh the page.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {assetsData?.assets?.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Cpu className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                        <p>No applications found in inventory.</p>
                        <p className="text-sm mt-2">Try using the Smart Entry tab instead.</p>
                      </div>
                    ) : (
                      assetsData?.assets?.map((app: Asset) => (
                        <div
                          key={app.id}
                          className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                            selectedApplications.has(app.id.toString())
                              ? "border-blue-200 bg-blue-50"
                              : "border-gray-200 hover:bg-gray-50"
                          }`}
                        >
                          <label className="flex items-center space-x-3 cursor-pointer flex-1">
                            <input
                              type="checkbox"
                              checked={selectedApplications.has(app.id.toString())}
                              onChange={() => handleToggleApplication(app.id.toString())}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
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
                        </div>
                      ))
                    )}
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* Selection Summary */}
            {totalSelected > 0 && (
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-2">
                  <div className="font-medium text-green-900">
                    {totalSelected} application{totalSelected > 1 ? "s" : ""} selected for collection
                  </div>
                </div>
                <div className="text-sm text-green-700 mt-1">
                  {selectedApplications.size > 0 && `${selectedApplications.size} from inventory`}
                  {selectedApplications.size > 0 && canonicalApplications.length > 0 && " • "}
                  {canonicalApplications.length > 0 && `${canonicalApplications.length} from smart entry`}
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
              <Button variant="outline" onClick={handleCancel} disabled={isSubmitting}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={totalSelected === 0 || isSubmitting}>
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Continue with {totalSelected} Application{totalSelected !== 1 ? "s" : ""}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </CollectionPageLayout>
  );
};

export default EnhancedApplicationSelection;
