import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AssessmentFlowLayout } from "@/components/assessment/AssessmentFlowLayout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle,
  Package,
  Link as LinkIcon,
} from "lucide-react";
import { useAssessmentFlow } from "@/hooks/useAssessmentFlow";
import { assessmentFlowAPI } from "@/hooks/useAssessmentFlow/api";

interface UnresolvedAsset {
  asset_id: string;
  name: string;
  asset_type: string;
}

interface AssetMapping {
  asset_id: string;
  application_id: string;
  mapping_method: string;
  mapping_confidence: number;
}

const AssetResolutionPage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const { state, resumeFlow } = useAssessmentFlow(flowId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<string | null>(
    null,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate("/assess/overview", { replace: true });
    }
  }, [flowId, navigate]);

  // Fetch asset resolution status
  const {
    data: resolutionData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["asset-resolution", flowId],
    queryFn: () => assessmentFlowAPI.getAssetResolutionStatus(flowId),
    enabled: !!flowId,
    staleTime: 30000,
    refetchInterval: (data) => {
      // Poll every 5 seconds if there are unresolved assets
      if (data?.unresolved_assets && data.unresolved_assets.length > 0) {
        return 5000;
      }
      return false;
    },
  });

  // Create mapping mutation
  const createMappingMutation = useMutation({
    mutationFn: (mapping: {
      asset_id: string;
      application_id: string;
      mapping_method?: string;
      mapping_confidence?: number;
    }) => assessmentFlowAPI.createAssetMapping(flowId, mapping),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset-resolution", flowId] });
      setSelectedAsset(null);
      setSelectedApplication(null);
    },
    onError: (error) => {
      console.error("Failed to create mapping:", error);
    },
  });

  // Complete resolution mutation
  const completeResolutionMutation = useMutation({
    mutationFn: () => assessmentFlowAPI.completeAssetResolution(flowId),
    onSuccess: async (response) => {
      // Navigate to next phase
      await resumeFlow({ phase: response.next_phase });
    },
    onError: (error) => {
      console.error("Failed to complete resolution:", error);
    },
  });

  const handleCreateMapping = async (): Promise<void> => {
    if (!selectedAsset || !selectedApplication) return;

    createMappingMutation.mutate({
      asset_id: selectedAsset,
      application_id: selectedApplication,
      mapping_method: "manual",
      mapping_confidence: 1.0,
    });
  };

  const handleCompleteResolution = async (): Promise<void> => {
    setIsSubmitting(true);
    try {
      await completeResolutionMutation.mutateAsync();
    } finally {
      setIsSubmitting(false);
    }
  };

  const unresolvedAssets = resolutionData?.unresolved_assets || [];
  const existingMappings = resolutionData?.existing_mappings || [];
  const allAssetsResolved = unresolvedAssets.length === 0;

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === "idle") {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Loading assessment...
      </div>
    );
  }

  if (isLoading) {
    return (
      <SidebarProvider>
        <AssessmentFlowLayout flowId={flowId}>
          <div className="p-6 text-sm text-muted-foreground">
            Loading asset resolution data...
          </div>
        </AssessmentFlowLayout>
      </SidebarProvider>
    );
  }

  if (error) {
    return (
      <SidebarProvider>
        <AssessmentFlowLayout flowId={flowId}>
          <div className="p-6">
            <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-600">
                Failed to load asset resolution data
              </p>
            </div>
          </div>
        </AssessmentFlowLayout>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">
              Asset to Application Resolution
            </h1>
            <p className="text-gray-600">
              Map selected assets to applications before performing 6R analysis
            </p>
          </div>

          {/* Status Alert */}
          {state.status === "error" && (
            <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-600">{state.error}</p>
            </div>
          )}

          {/* Completion Banner */}
          {allAssetsResolved && (
            <div className="flex items-center space-x-2 p-4 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-sm text-green-600">
                All assets have been resolved! You can now proceed to the next
                phase.
              </p>
            </div>
          )}

          {/* Resolution Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Resolution Status
              </CardTitle>
              <CardDescription>
                {existingMappings.length} assets mapped,{" "}
                {unresolvedAssets.length} remaining
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${
                        existingMappings.length > 0
                          ? (existingMappings.length /
                              (existingMappings.length +
                                unresolvedAssets.length)) *
                            100
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <span className="text-sm font-medium">
                  {existingMappings.length} /{" "}
                  {existingMappings.length + unresolvedAssets.length}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Unresolved Assets */}
          {unresolvedAssets.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Unresolved Assets</CardTitle>
                <CardDescription>
                  Select an asset and map it to an application
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Select Asset
                  </label>
                  <Select
                    value={selectedAsset || ""}
                    onValueChange={setSelectedAsset}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose an asset to map" />
                    </SelectTrigger>
                    <SelectContent>
                      {unresolvedAssets.map((asset) => (
                        <SelectItem key={asset.asset_id} value={asset.asset_id}>
                          <div className="flex items-center gap-2">
                            <span>{asset.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {asset.asset_type}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Map to Application
                  </label>
                  <Select
                    value={selectedApplication || ""}
                    onValueChange={setSelectedApplication}
                    disabled={!selectedAsset}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose target application" />
                    </SelectTrigger>
                    <SelectContent>
                      {state.selectedApplications.map((app) => (
                        <SelectItem
                          key={app.application_id}
                          value={app.application_id}
                        >
                          <div className="flex items-center gap-2">
                            <span>{app.application_name}</span>
                            <Badge variant="outline" className="text-xs">
                              {app.application_type}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={handleCreateMapping}
                  disabled={
                    !selectedAsset ||
                    !selectedApplication ||
                    createMappingMutation.isPending
                  }
                  className="w-full"
                >
                  <LinkIcon className="h-4 w-4 mr-2" />
                  {createMappingMutation.isPending
                    ? "Creating Mapping..."
                    : "Create Mapping"}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Existing Mappings */}
          {existingMappings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Existing Mappings</CardTitle>
                <CardDescription>
                  Assets that have been successfully mapped to applications
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {existingMappings.map((mapping, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <LinkIcon className="h-4 w-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium">
                            Asset: {mapping.asset_id}
                          </p>
                          <p className="text-xs text-gray-500">
                            Application: {mapping.application_id}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {mapping.mapping_method}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {(mapping.mapping_confidence * 100).toFixed(0)}%
                          confidence
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end items-center pt-6 border-t border-gray-200">
            <Button
              onClick={handleCompleteResolution}
              disabled={
                !allAssetsResolved ||
                isSubmitting ||
                completeResolutionMutation.isPending
              }
              size="lg"
            >
              {isSubmitting || completeResolutionMutation.isPending ? (
                "Processing..."
              ) : (
                <>
                  Complete Resolution
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </AssessmentFlowLayout>
    </SidebarProvider>
  );
};

export default AssetResolutionPage;
