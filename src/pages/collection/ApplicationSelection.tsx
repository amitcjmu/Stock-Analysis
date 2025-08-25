import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
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
  Cpu,
  ArrowLeft,
  ArrowRight,
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

  // Get flow ID from URL params
  const flowId = searchParams.get("flowId");

  // State management
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(
    new Set(),
  );
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

  // Fetch applications from the inventory
  const {
    data: applications,
    isLoading: applicationsLoading,
    error: applicationsError,
  } = useQuery({
    queryKey: ["applications-for-collection", client?.id, engagement?.id],
    queryFn: async () => {
      try {
        const response = await apiCall(
          "/unified-discovery/assets?page=1&page_size=100",
        );

        // Filter only application assets (case-insensitive)
        const apps = (response?.assets || []).filter(
          (asset: Asset) => asset.asset_type?.toLowerCase() === "application",
        );

        console.log(
          `📋 Fetched ${apps.length} applications for collection flow selection`,
        );
        return apps;
      } catch (error) {
        console.error("❌ Failed to fetch applications:", error);
        throw error;
      }
    },
    enabled: !!client && !!engagement && !!flowId,
  });

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

  // Handle select all applications
  const handleSelectAll = () => {
    if (applications) {
      if (selectedApplications.size === applications.length) {
        setSelectedApplications(new Set());
      } else {
        setSelectedApplications(
          new Set(applications.map((app: Asset) => app.id)),
        );
      }
    }
  };

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
          <Button onClick={() => window.location.reload()}>Retry</Button>
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
                {/* Select All Checkbox */}
                <div className="pb-4 border-b">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <Checkbox
                      checked={
                        selectedApplications.size === applications.length
                      }
                      onCheckedChange={handleSelectAll}
                    />
                    <span className="font-medium">
                      Select All ({applications.length} applications available)
                    </span>
                  </label>
                </div>

                {/* Application List */}
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {applications.map((app: Asset) => (
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
                          <div className="font-medium">{app.name}</div>
                          {app.environment && (
                            <div className="text-sm text-gray-600">
                              Environment: {app.environment}
                            </div>
                          )}
                          {app.description && (
                            <div className="text-sm text-gray-500 mt-1">
                              {app.description}
                            </div>
                          )}
                        </div>
                      </label>
                      <div className="flex items-center gap-2">
                        {app.criticality && (
                          <Badge
                            variant={
                              app.criticality === "High"
                                ? "destructive"
                                : app.criticality === "Medium"
                                  ? "secondary"
                                  : "default"
                            }
                          >
                            {app.criticality}
                          </Badge>
                        )}
                        {app.six_r_strategy && (
                          <Badge variant="outline">{app.six_r_strategy}</Badge>
                        )}
                      </div>
                    </div>
                  ))}
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
