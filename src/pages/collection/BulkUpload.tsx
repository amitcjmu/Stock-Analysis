import React from "react";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileSpreadsheet } from "lucide-react";
import {
  ArrowLeft,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

// Import API utilities
import { apiCall } from "@/config/api";
import { collectionFlowApi } from "@/services/api/collection-flow";

// Import layout components
import Sidebar from "@/components/Sidebar";
import ContextBreadcrumbs from "@/components/context/ContextBreadcrumbs";

// Import existing collection components
import { BulkDataGrid } from "@/components/collection/BulkDataGrid";
import { ValidationDisplay } from "@/components/collection/ValidationDisplay";
import { ProgressTracker } from "@/components/collection/ProgressTracker";

// Import types
import type {
  ApplicationSummary,
  FormField,
  BulkUploadResult,
  FormValidationResult,
  ProgressMilestone,
} from "@/components/collection/types";

// UI Components
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/components/ui/use-toast";

/**
 * Bulk Upload collection page
 * Handles large-scale data collection via file uploads and bulk processing
 */
const BulkUpload: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State management
  const [uploadResults, setUploadResults] = useState<BulkUploadResult[]>([]);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [validation, setValidation] = useState<FormValidationResult | null>(
    null,
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [collectionFlowId, setCollectionFlowId] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] =
    useState<string>("applications");

  // Ensure collection flow exists on page load
  useEffect(() => {
    const ensureCollectionFlow = async () => {
      try {
        const response = await collectionFlowApi.ensureFlow();
        if (response) {
          // Handle both flow_id and id fields for compatibility
          const flowId = response.flow_id || response.id;
          if (flowId) {
            setCollectionFlowId(flowId);
          }
        }
      } catch (error) {
        console.error("Failed to ensure collection flow:", error);
        toast({
          title: "Error",
          description:
            "Failed to initialize collection flow. Please try again.",
          variant: "destructive",
        });
      }
    };

    ensureCollectionFlow();
  }, [toast]);

  // Mock field definitions for bulk collection
  const bulkFields: FormField[] = [
    {
      id: "name",
      label: "Application Name",
      fieldType: "text",
      criticalAttribute: "name",
      validation: { required: true },
      section: "basic",
      order: 1,
      businessImpactScore: 0.9,
    },
    {
      id: "type",
      label: "Application Type",
      fieldType: "select",
      criticalAttribute: "type",
      options: [
        { value: "web", label: "Web Application" },
        { value: "desktop", label: "Desktop Application" },
        { value: "mobile", label: "Mobile Application" },
        { value: "service", label: "Web Service/API" },
      ],
      validation: { required: true },
      section: "basic",
      order: 2,
      businessImpactScore: 0.8,
    },
    {
      id: "technology",
      label: "Primary Technology",
      fieldType: "select",
      criticalAttribute: "technology",
      options: [
        { value: "java", label: "Java" },
        { value: "dotnet", label: ".NET" },
        { value: "python", label: "Python" },
        { value: "nodejs", label: "Node.js" },
      ],
      section: "technical",
      order: 1,
      businessImpactScore: 0.75,
    },
    {
      id: "criticality",
      label: "Business Criticality",
      fieldType: "select",
      criticalAttribute: "criticality",
      options: [
        { value: "critical", label: "Mission Critical" },
        { value: "important", label: "Important" },
        { value: "moderate", label: "Moderate" },
        { value: "low", label: "Low Impact" },
      ],
      section: "business",
      order: 1,
      businessImpactScore: 0.85,
    },
  ];

  // Progress milestones for bulk upload
  const progressMilestones: ProgressMilestone[] = [
    {
      id: "upload-start",
      title: "Upload Started",
      description: "File upload initiated",
      achieved: uploadResults.length > 0,
      achievedAt:
        uploadResults.length > 0 ? new Date().toISOString() : undefined,
      weight: 0.2,
      required: true,
    },
    {
      id: "data-parsed",
      title: "Data Parsed",
      description: "File data successfully parsed",
      achieved: applications.length > 0,
      weight: 0.3,
      required: true,
    },
    {
      id: "validation-complete",
      title: "Validation Complete",
      description: "Data validation and quality checks completed",
      achieved: validation !== null,
      weight: 0.3,
      required: true,
    },
    {
      id: "processing-complete",
      title: "Processing Complete",
      description: "All data processed and ready for next phase",
      achieved: false,
      weight: 0.2,
      required: true,
    },
  ];

  const handleBulkUpload = async (file: File): Promise<void> => {
    setIsProcessing(true);
    setUploadProgress(0);

    try {
      setUploadProgress(10);

      // Read and parse CSV file
      const fileContent = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = (e) => reject(new Error("Failed to read file"));
        reader.readAsText(file);
      });

      setUploadProgress(30);

      // Parse CSV content
      const lines = fileContent.trim().split("\n");
      const headers = lines[0]
        .split(",")
        .map((h) => h.trim().replace(/"/g, ""));
      const dataRows = lines.slice(1).map((line) => {
        const values = line.split(",").map((v) => v.trim().replace(/"/g, ""));
        const row: Record<string, string> = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || "";
        });
        return row;
      });

      setUploadProgress(50);

      // Check if we have a collection flow ID
      if (!collectionFlowId) {
        throw new Error(
          "Collection flow not initialized. Please refresh the page and try again.",
        );
      }

      // Determine asset type based on template selection or headers
      const assetType =
        selectedTemplate === "servers"
          ? "servers"
          : selectedTemplate === "databases"
            ? "databases"
            : selectedTemplate === "devices"
              ? "devices"
              : "applications"; // Default to applications

      // Call Collection bulk import endpoint with CSV data directly
      const result = await apiCall("/api/v1/collection/bulk-import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          flow_id: collectionFlowId,
          csv_data: dataRows,
          asset_type: assetType,
        }),
      });

      setUploadProgress(80);

      // apiCall returns parsed JSON directly and throws errors on non-2xx responses
      setUploadProgress(100);

      // Create BulkUploadResult from API response
      const uploadResult: BulkUploadResult = {
        uploadId: `upload-${Date.now()}`,
        status: result.success ? "completed" : "failed",
        totalRows: dataRows.length,
        successfulRows: result.processed_count || 0,
        failedRows: result.errors ? result.errors.length : 0,
        validationIssues: result.errors || [],
        processingTime: 2500, // Estimated processing time
        dataQualityScore:
          result.errors && result.errors.length > 0
            ? Math.round((result.processed_count / dataRows.length) * 100)
            : 100,
      };

      // Create applications from uploaded data
      const uploadedApplications: ApplicationSummary[] = dataRows.map(
        (row, index) => ({
          id: `app-${index + 1}`,
          name:
            row.name || row["Application Name"] || `Application ${index + 1}`,
          technology: row.technology || row["Primary Technology"] || "Unknown",
          architecturePattern: "Unknown",
          businessCriticality:
            row.criticality || row["Business Criticality"] || "Unknown",
        }),
      );

      setUploadResults([uploadResult]);
      setApplications(uploadedApplications);

      toast({
        title: "Upload Successful",
        description: `Successfully imported ${uploadResult.successfulRows} ${assetType}. ${result.gap_analysis_triggered ? "Gap analysis has been triggered." : ""}`,
      });

      // If there's a warning about flow creation, show it
      if (result.warning) {
        toast({
          title: "Flow Creation Notice",
          description: result.warning,
          variant: "default",
        });
      }
    } catch (error) {
      console.error("Upload error:", error);
      toast({
        title: "Upload Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to process the uploaded file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  };

  const handleDataChange = (
    applicationId: string,
    fieldId: string,
    value: unknown,
  ): void => {
    setApplications((prev) =>
      prev.map((app) =>
        app.id === applicationId ? { ...app, [fieldId]: value } : app,
      ),
    );
  };

  const handleDownloadTemplate = (): void => {
    // Create a mock CSV template
    const headers = bulkFields.map((field) => field.label).join(",");
    const sampleRow = bulkFields
      .map((field) => {
        switch (field.fieldType) {
          case "select":
            return field.options?.[0]?.value || "";
          case "text":
            return `Sample ${field.label}`;
          default:
            return "";
        }
      })
      .join(",");

    const csvContent = `${headers}\n${sampleRow}`;
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "bulk-collection-template.csv";
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const completedMilestones = progressMilestones.filter(
    (m) => m.achieved,
  ).length;
  const overallProgress =
    (completedMilestones / progressMilestones.length) * 100;

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate("/collection")}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Collection
                </Button>
                <div>
                  <h1 className="text-2xl font-bold">Bulk Data Upload</h1>
                  <p className="text-muted-foreground">
                    Upload and process multiple applications efficiently
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" onClick={handleDownloadTemplate}>
                  <Download className="h-4 w-4 mr-2" />
                  Download Template
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Progress Tracker Sidebar */}
              <div className="lg:col-span-1">
                <ProgressTracker
                  formId="bulk-upload"
                  totalSections={4}
                  completedSections={completedMilestones}
                  overallCompletion={overallProgress}
                  confidenceScore={uploadResults[0]?.dataQualityScore || 0}
                  milestones={progressMilestones}
                  timeSpent={uploadResults[0]?.processingTime || 0}
                  estimatedTimeRemaining={isProcessing ? 60000 : 0}
                />
              </div>

              {/* Main Content */}
              <div className="lg:col-span-3 space-y-6">
                {/* Upload Status */}
                {uploadResults.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span>Upload Results</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {uploadResults.map((result, index) => (
                          <React.Fragment key={result.uploadId}>
                            <div className="text-center">
                              <p className="text-2xl font-bold text-green-600">
                                {result.successfulRows}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Successful
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-2xl font-bold text-red-600">
                                {result.failedRows}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Failed
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-2xl font-bold">
                                {result.totalRows}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Total Rows
                              </p>
                            </div>
                            <div className="text-center">
                              <p className="text-2xl font-bold text-blue-600">
                                {result.dataQualityScore}%
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Quality Score
                              </p>
                            </div>
                          </React.Fragment>
                        ))}
                      </div>

                      {uploadResults[0]?.validationIssues.length > 0 && (
                        <Alert className="mt-4">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            {uploadResults[0].validationIssues.length}{" "}
                            validation issues found. Review the data grid below
                            to address these issues.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Processing Progress */}
                {isProcessing && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Processing Upload</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Processing...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="h-2" />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Bulk Data Grid */}
                <Card>
                  <CardHeader>
                    <CardTitle>Bulk Application Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <BulkDataGrid
                      applications={applications}
                      fields={bulkFields}
                      onDataChange={handleDataChange}
                      onBulkUpload={handleBulkUpload}
                      templateOptions={[
                        {
                          id: "standard",
                          name: "Standard Application Template",
                          description: "Basic application information template",
                          applicableTypes: ["web", "desktop", "mobile"],
                          fieldCount: bulkFields.length,
                          effectivenessScore: 85,
                        },
                        {
                          id: "detailed",
                          name: "Detailed Technical Template",
                          description:
                            "Comprehensive technical assessment template",
                          applicableTypes: ["web", "service"],
                          fieldCount: bulkFields.length + 5,
                          effectivenessScore: 95,
                        },
                      ]}
                    />
                  </CardContent>
                </Card>

                {/* Validation Results */}
                {validation && (
                  <ValidationDisplay
                    validation={validation}
                    showWarnings={true}
                    onErrorClick={(fieldId) => {
                      console.log("Navigate to field:", fieldId);
                    }}
                  />
                )}

                {/* Action Buttons */}
                <div className="flex justify-end space-x-4">
                  <Button
                    variant="outline"
                    onClick={() => navigate("/collection")}
                  >
                    Save and Continue Later
                  </Button>
                  <Button
                    onClick={() => navigate("/collection/data-integration")}
                    disabled={applications.length === 0}
                  >
                    Proceed to Data Integration
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkUpload;
