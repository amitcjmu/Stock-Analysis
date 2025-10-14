import React, { useEffect, useState, useCallback, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  GridReadyEvent,
  CellEditingStoppedEvent,
} from "ag-grid-community";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import {
  Sparkles,
  RefreshCw,
  Save,
  CheckCircle,
  X,
  AlertCircle,
} from "lucide-react";

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  collectionFlowApi,
  type DataGap,
  type GapUpdate,
} from "@/services/api/collection-flow";

interface DataGapDiscoveryProps {
  flowId: string;
  selectedAssetIds: string[];
  onComplete?: () => void;
}

interface GapRowData extends DataGap {
  id?: string;
  isModified?: boolean;
}

const DataGapDiscovery: React.FC<DataGapDiscoveryProps> = ({
  flowId,
  selectedAssetIds,
  onComplete,
}) => {
  // Add custom tooltip styling
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .ag-tooltip {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #374151 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        max-width: 400px !important;
        word-wrap: break-word !important;
        z-index: 9999 !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  const { toast } = useToast();
  const [gaps, setGaps] = useState<GapRowData[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [scanSummary, setScanSummary] = useState<{
    total_gaps: number;
    critical_gaps: number;
    execution_time_ms: number;
  } | null>(null);
  const [modifiedGaps, setModifiedGaps] = useState<Set<string>>(new Set());
  const [enhancementProgress, setEnhancementProgress] = useState<{
    job_id: string;
    status: string;
    processed: number;
    total: number;
    current_asset?: string;
    percentage: number;
  } | null>(null);
  const [selectedGaps, setSelectedGaps] = useState<GapRowData[]>([]);

  // Fetch existing gaps on mount, or scan if none exist
  useEffect(() => {
    const loadGaps = async () => {
      try {
        // First try to fetch existing gaps from database
        const existingGaps = await collectionFlowApi.getGaps(flowId);

        if (existingGaps && existingGaps.length > 0) {
          // Backend always returns database UUIDs - no transformation needed
          setGaps(existingGaps);
        } else if (selectedAssetIds.length > 0) {
          // No existing gaps, trigger a scan if assets are selected
          handleScanGaps();
        }
      } catch (error) {
        console.error("Failed to load gaps:", error);
        // If fetching fails and we have assets, try scanning
        if (selectedAssetIds.length > 0) {
          handleScanGaps();
        }
      }
    };

    loadGaps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flowId, selectedAssetIds]);

  const handleScanGaps = async () => {
    try {
      setIsScanning(true);
      const response = await collectionFlowApi.scanGaps(
        flowId,
        selectedAssetIds,
      );

      // Backend now returns gaps with database UUIDs - no synthetic keys needed
      setGaps(response.gaps);
      setScanSummary(response.summary);

      toast({
        title: "Gap Scan Complete",
        description: `Found ${response.summary.total_gaps} gaps across ${response.summary.assets_analyzed} assets (${response.summary.execution_time_ms}ms)`,
        variant: "default",
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to scan gaps";
      toast({
        title: "Scan Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsScanning(false);
    }
  };

  const handleAnalyzeGaps = async () => {
    // Use selected gaps if available, otherwise all gaps
    const gapsToAnalyze = selectedGaps.length > 0 ? selectedGaps : gaps;

    if (gapsToAnalyze.length === 0) {
      toast({
        title: "No Gaps to Analyze",
        description: selectedGaps.length > 0 ? "Please select gaps to analyze" : "Run a gap scan first",
        variant: "destructive",
      });
      return;
    }

    // Check for >200 gaps limit
    if (gapsToAnalyze.length > 200) {
      toast({
        title: "Too Many Gaps",
        description: `Please select fewer gaps (${gapsToAnalyze.length}/200 max). Use row selection to choose specific gaps.`,
        variant: "destructive",
      });
      return;
    }

    try {
      setIsAnalyzing(true);

      // Start enhancement job (returns 202 Accepted immediately)
      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        gapsToAnalyze,
        selectedAssetIds,
      );

      toast({
        title: "Enhancement Started",
        description: response.message,
        variant: "default",
      });

      // Start polling for progress
      let attempts = 0;
      const maxAttempts = 24; // 12 minutes max (30s interval)

      const pollProgress = setInterval(async () => {
        try {
          const progress = await collectionFlowApi.getEnhancementProgress(flowId);

          setEnhancementProgress({
            job_id: response.job_id,
            status: progress.status,
            processed: progress.processed,
            total: progress.total,
            current_asset: progress.current_asset,
            percentage: progress.percentage,
          });

          if (progress.status === "completed") {
            clearInterval(pollProgress);

            // Re-scan gaps to get AI enhancements from database
            try {
              const updatedGaps = await collectionFlowApi.getGaps(flowId);
              // Backend always returns database UUIDs - no transformation needed
              setGaps(updatedGaps);

              toast({
                title: "Enhancement Complete",
                description: `Enhanced ${progress.processed} assets successfully`,
                variant: "default",
              });
            } catch (fetchError) {
              console.error("Failed to fetch enhanced gaps:", fetchError);
            }

            setIsAnalyzing(false);
            setEnhancementProgress(null);
          } else if (progress.status === "failed") {
            clearInterval(pollProgress);
            toast({
              title: "Enhancement Failed",
              description: "AI enhancement encountered errors. Check logs for details.",
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }

          attempts++;
          if (attempts >= maxAttempts) {
            clearInterval(pollProgress);
            toast({
              title: "Enhancement Timeout",
              description: "Enhancement is taking longer than 12 minutes. Check flow status or backend logs.",
              variant: "destructive",
            });
            setIsAnalyzing(false);
            setEnhancementProgress(null);
          }
        } catch (error) {
          console.error("Progress polling error:", error);
        }
      }, 30000); // Poll every 30 seconds

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to start enhancement";
      toast({
        title: "Enhancement Failed",
        description: errorMessage,
        variant: "destructive",
      });
      setIsAnalyzing(false);
      setEnhancementProgress(null);
    }
  };

  const handleCellEditingStopped = useCallback(
    (event: CellEditingStoppedEvent<GapRowData>) => {
      if (event.oldValue !== event.newValue) {
        const gapId = event.data?.id;
        if (gapId) {
          setModifiedGaps((prev) => new Set(prev).add(gapId));

          // Mark row as modified
          setGaps((prevGaps) =>
            prevGaps.map((gap) =>
              gap.id === gapId ? { ...gap, isModified: true } : gap,
            ),
          );
        }
      }
    },
    [],
  );

  const handleSaveGap = useCallback(
    async (gap: GapRowData) => {
      if (!gap.id || !gap.current_value) return;

      try {
        setIsSaving(true);

        const update: GapUpdate = {
          gap_id: gap.id,
          field_name: gap.field_name,
          resolved_value: String(gap.current_value),
          resolution_status: "resolved",
          resolution_method: "manual_entry",
        };

        await collectionFlowApi.updateGaps(flowId, [update]);

        // Remove from modified set
        setModifiedGaps((prev) => {
          const newSet = new Set(prev);
          newSet.delete(gap.id);
          return newSet;
        });

        // Update gap status
        setGaps((prevGaps) =>
          prevGaps.map((g) =>
            g.id === gap.id ? { ...g, isModified: false } : g,
          ),
        );

        toast({
          title: "Gap Saved",
          description: `Saved resolution for ${gap.field_name}`,
          variant: "default",
        });
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to save gap";
        toast({
          title: "Save Failed",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsSaving(false);
      }
    },
    [flowId, toast],
  );

  const handleBulkAccept = async () => {
    // Accept all AI suggestions with high confidence
    const highConfidenceGaps = gaps.filter(
      (gap) => gap.confidence_score !== null && gap.confidence_score >= 0.8,
    );

    if (highConfidenceGaps.length === 0) {
      toast({
        title: "No High Confidence Suggestions",
        description: "Run AI analysis first or lower confidence threshold",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);

      const updates: GapUpdate[] = highConfidenceGaps.map((gap) => {
        if (!gap.id) {
          throw new Error(`Gap ID missing for ${gap.field_name}`);
        }

        return {
          gap_id: gap.id,  // Backend always returns database UUID
          field_name: gap.field_name,
          resolved_value: gap.suggested_resolution,
          resolution_status: "resolved",
          resolution_method: "ai_suggestion",
        };
      });

      const response = await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Bulk Accept Complete",
        description: `Accepted ${response.gaps_resolved} high-confidence suggestions`,
        variant: "default",
      });

      // Fetch remaining unresolved gaps (don't re-scan, which would recreate them!)
      const updatedGaps = await collectionFlowApi.getGaps(flowId);
      setGaps(updatedGaps);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to bulk accept";
      toast({
        title: "Bulk Accept Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Accept only the selected gaps from AG Grid row selection
  const handleAcceptSelected = async () => {
    if (selectedGaps.length === 0) {
      toast({
        title: "No Gaps Selected",
        description: "Please select gaps from the table to accept",
        variant: "destructive",
      });
      return;
    }

    // Validate that selected gaps have suggested resolutions
    const gapsWithResolutions = selectedGaps.filter(
      (gap) => gap.suggested_resolution && gap.suggested_resolution.trim() !== ''
    );

    if (gapsWithResolutions.length === 0) {
      toast({
        title: "No Resolutions Available",
        description: "Selected gaps need AI suggestions before accepting. Run AI analysis first.",
        variant: "destructive",
      });
      return;
    }

    if (gapsWithResolutions.length < selectedGaps.length) {
      toast({
        title: "Some Gaps Missing Resolutions",
        description: `${selectedGaps.length - gapsWithResolutions.length} selected gap(s) don't have AI suggestions. Only accepting ${gapsWithResolutions.length} gap(s).`,
        variant: "default",
      });
    }

    try {
      setIsSaving(true);

      // CRITICAL FIX: Look up full gap data from gaps state to get database IDs
      // AG Grid selection may not preserve all fields, so we use asset_id + field_name as key
      const updates: GapUpdate[] = gapsWithResolutions.map((selectedGap) => {
        // Find the full gap object in the gaps array using composite key
        const fullGap = gaps.find(
          (g) => g.asset_id === selectedGap.asset_id && g.field_name === selectedGap.field_name
        );

        if (!fullGap || !fullGap.id) {
          throw new Error(
            `Gap ID not found for ${selectedGap.field_name} on asset ${selectedGap.asset_id}`
          );
        }

        return {
          gap_id: fullGap.id,  // Use ID from gaps state
          field_name: selectedGap.field_name,
          resolved_value: selectedGap.suggested_resolution,
          resolution_status: "resolved",
          resolution_method: "ai_suggestion",
        };
      });

      // Debug log to see what we're sending
      console.log('📤 Sending gap updates:', JSON.stringify(updates, null, 2));

      const response = await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Accept Selected Complete",
        description: `Accepted ${response.gaps_resolved} selected gap(s)`,
        variant: "default",
      });

      // Clear selection after successful acceptance
      setSelectedGaps([]);

      // Fetch remaining unresolved gaps (don't re-scan, which would recreate them!)
      const updatedGaps = await collectionFlowApi.getGaps(flowId);
      setGaps(updatedGaps);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to accept selected gaps";
      toast({
        title: "Accept Selected Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleBulkReject = async () => {
    // Reject all AI suggestions (mark as skipped)
    const aiSuggestedGaps = gaps.filter((gap) => gap.confidence_score !== null);

    if (aiSuggestedGaps.length === 0) {
      toast({
        title: "No AI Suggestions",
        description: "Run AI analysis first",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);

      const updates: GapUpdate[] = aiSuggestedGaps.map((gap) => {
        if (!gap.id) {
          throw new Error(`Gap ID missing for ${gap.field_name}`);
        }

        return {
          gap_id: gap.id,  // Backend always returns database UUID
          field_name: gap.field_name,
          resolved_value: "",
          resolution_status: "skipped",
          resolution_method: "manual_entry",
        };
      });

      await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Bulk Reject Complete",
        description: `Rejected ${aiSuggestedGaps.length} AI suggestions`,
        variant: "default",
      });

      // Clear AI suggestions from UI
      setGaps((prevGaps) =>
        prevGaps.map((gap) => ({
          ...gap,
          confidence_score: null,
          ai_suggestions: undefined,
        })),
      );
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to bulk reject";
      toast({
        title: "Bulk Reject Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Confidence score color renderer
  const confidenceRenderer = (params: { value: number | null }) => {
    if (params.value === null || params.value === undefined) {
      return <span className="text-gray-400">No AI</span>;
    }

    const percentage = Math.round(params.value * 100);
    let colorClass = "text-red-600";
    if (params.value >= 0.8) colorClass = "text-green-600";
    else if (params.value >= 0.6) colorClass = "text-yellow-600";

    return <span className={`${colorClass} font-semibold`}>{percentage}%</span>;
  };

  // Save button renderer - wrapped in useCallback for performance
  const actionRenderer = useCallback(
    (params: { data: GapRowData }) => {
      const gap = params.data;
      const isModified = gap.isModified || modifiedGaps.has(gap.id || "");

      if (!isModified) {
        return <span className="text-gray-400">-</span>;
      }

      return (
        <button
          className="save-btn px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          data-gap-id={gap.id}
          onClick={(e) => {
            e.stopPropagation();
            handleSaveGap(gap);
          }}
        >
          Save
        </button>
      );
    },
    [modifiedGaps, handleSaveGap],
  );

  const columnDefs = useMemo<Array<ColDef<GapRowData>>>(
    () => [
      {
        width: 50,
        pinned: "left",
        lockPosition: "left",
        suppressMovable: true,
      },
      {
        field: "asset_name",
        headerName: "Asset",
        width: 150,
        pinned: "left",
      },
      {
        field: "field_name",
        headerName: "Field",
        width: 180,
      },
      {
        field: "gap_category",
        headerName: "Category",
        width: 130,
      },
      {
        field: "priority",
        headerName: "Priority",
        width: 100,
        cellRenderer: (params: { value: number }) => {
          const badges = {
            1: (
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                Critical
              </span>
            ),
            2: (
              <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                High
              </span>
            ),
            3: (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                Medium
              </span>
            ),
            4: (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                Low
              </span>
            ),
          };
          return badges[params.value as 1 | 2 | 3 | 4] || badges[4];
        },
      },
      {
        field: "current_value",
        headerName: "Current Value",
        width: 200,
        editable: true,
        cellEditor: "agTextCellEditor",
      },
      {
        field: "suggested_resolution",
        headerName: "Suggested Resolution",
        width: 250,
      },
      {
        field: "confidence_score",
        headerName: "AI Confidence",
        width: 130,
        cellRenderer: confidenceRenderer,
      },
      {
        headerName: "Actions",
        width: 100,
        cellRenderer: actionRenderer,
        pinned: "right",
      },
    ],
    [actionRenderer],
  );

  const onGridReady = useCallback(
    (params: GridReadyEvent) => {
      // Add click handler for save buttons
      params.api.getRenderedNodes().forEach((node) => {
        const eGui = node.eGridCell?.querySelector(".save-btn");
        if (eGui) {
          eGui.addEventListener("click", (event) => {
            event.stopPropagation();
            const gapId = (event.target as HTMLElement).getAttribute(
              "data-gap-id",
            );
            const gap = gaps.find((g) => g.id === gapId);
            if (gap) {
              handleSaveGap(gap);
            }
          });
        }
      });
    },
    [gaps, handleSaveGap],
  );

  const onSelectionChanged = useCallback((event: unknown) => {
    const selectedRows = (event as { api: { getSelectedRows: () => GapRowData[] } }).api.getSelectedRows();
    setSelectedGaps(selectedRows);
  }, []);

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      {scanSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertCircle className="w-5 h-5 text-orange-600 mr-2" />
              Gap Analysis Summary
            </CardTitle>
            <CardDescription>
              Fast programmatic scan across {scanSummary.total_gaps} gaps
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-600">Total Gaps</div>
                <div className="text-2xl font-bold">
                  {scanSummary.total_gaps}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Critical Gaps</div>
                <div className="text-2xl font-bold text-red-600">
                  {scanSummary.critical_gaps}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Scan Time</div>
                <div className="text-2xl font-bold">
                  {scanSummary.execution_time_ms}ms
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Gap Resolution Actions</CardTitle>
          <CardDescription>
            Scan for gaps, enhance with AI, or manually resolve
            {selectedGaps.length > 0 && (
              <span className="ml-2 text-purple-600 font-medium">
                ({selectedGaps.length} gap{selectedGaps.length !== 1 ? 's' : ''} selected for AI analysis)
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleScanGaps}
              disabled={isScanning || selectedAssetIds.length === 0}
              variant="outline"
            >
              {isScanning ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              {isScanning ? "Scanning..." : "Re-scan Gaps"}
            </Button>

            <Button
              onClick={handleAnalyzeGaps}
              disabled={isAnalyzing || gaps.length === 0}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isAnalyzing ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-2" />
              )}
              {isAnalyzing ? "Analyzing..." : "Perform Agentic Analysis"}
            </Button>

            {/* Progress Display for Non-Blocking AI Enhancement */}
            {enhancementProgress && (
              <div className="flex items-center gap-2 px-3 py-1 bg-purple-50 border border-purple-200 rounded-md text-sm text-purple-700">
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>
                  Processing: {enhancementProgress.processed}/{enhancementProgress.total} assets
                  {enhancementProgress.current_asset && ` - ${enhancementProgress.current_asset}`}
                  ({Math.round((enhancementProgress.processed / enhancementProgress.total) * 100)}%)
                </span>
              </div>
            )}

            <div className="flex-1" />

            {/* Accept Selected Button - Only show when gaps are selected */}
            {selectedGaps.length > 0 && (
              <Button
                onClick={handleAcceptSelected}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Accept Selected ({selectedGaps.length})
              </Button>
            )}

            <Button
              onClick={handleBulkAccept}
              disabled={isSaving || gaps.length === 0}
              variant="outline"
              className="text-green-600 hover:bg-green-50"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Accept All (High Confidence)
            </Button>

            <Button
              onClick={handleBulkReject}
              disabled={isSaving || gaps.length === 0}
              variant="outline"
              className="text-red-600 hover:bg-red-50"
            >
              <X className="w-4 h-4 mr-2" />
              Reject All AI Suggestions
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* AG Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Data Gaps ({gaps.length})</CardTitle>
          <div className="text-sm text-muted-foreground">
            Click cells to edit, then save individually. Color-coded AI
            confidence:
            <Badge className="ml-2 bg-green-100 text-green-800">≥80%</Badge>
            <Badge className="ml-1 bg-yellow-100 text-yellow-800">60-79%</Badge>
            <Badge className="ml-1 bg-red-100 text-red-800">&lt;60%</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div
            className="ag-theme-quartz"
            style={{ height: 500, width: "100%" }}
          >
            <AgGridReact
              theme="legacy"
              rowData={gaps}
              columnDefs={columnDefs}
              defaultColDef={{
                sortable: true,
                filter: true,
                resizable: true,
                tooltipValueGetter: (params) => params.value,
              }}
              getRowId={(params) =>
                params.data.id ||
                `${params.data.asset_id}-${params.data.field_name}`
              }
              onGridReady={onGridReady}
              onCellEditingStopped={handleCellEditingStopped}
              onSelectionChanged={onSelectionChanged}
              rowSelection={{
                mode: "multiRow",
                checkboxes: true,
                headerCheckbox: true,
                enableClickSelection: false,
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Completion Section */}
      {gaps.length === 0 && !isScanning && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Gaps Identified
              </h3>
              <p className="text-gray-600 mb-4">
                All selected assets have complete critical attributes. Ready to
                proceed.
              </p>
              {onComplete && (
                <Button
                  onClick={onComplete}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Continue to Next Phase
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DataGapDiscovery;
