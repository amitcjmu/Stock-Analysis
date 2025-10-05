import React, { useEffect, useState, useCallback, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  GridReadyEvent,
  CellEditingStoppedEvent,
} from "ag-grid-community";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
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

  // Fetch existing gaps on mount, or scan if none exist
  useEffect(() => {
    const loadGaps = async () => {
      try {
        // First try to fetch existing gaps from database
        const existingGaps = await collectionFlowApi.getGaps(flowId);

        if (existingGaps && existingGaps.length > 0) {
          // Add id field for AG Grid row identification
          const gapsWithIds = existingGaps.map((gap, index) => ({
            ...gap,
            id: `${gap.asset_id}-${gap.field_name}-${index}`,
          }));
          setGaps(gapsWithIds);
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

      // Add id field for AG Grid row identification
      const gapsWithIds = response.gaps.map((gap, index) => ({
        ...gap,
        id: `${gap.asset_id}-${gap.field_name}-${index}`,
      }));

      setGaps(gapsWithIds);
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
    if (gaps.length === 0) {
      toast({
        title: "No Gaps to Analyze",
        description: "Run a gap scan first",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsAnalyzing(true);
      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        gaps,
        selectedAssetIds,
      );

      // Update gaps with AI enhancements
      const enhancedGapsWithIds = response.enhanced_gaps.map((gap, index) => ({
        ...gap,
        id: `${gap.asset_id}-${gap.field_name}-${index}`,
      }));

      setGaps(enhancedGapsWithIds);

      toast({
        title: "AI Analysis Complete",
        description: `Enhanced ${response.summary.enhanced_gaps} gaps with AI suggestions (${response.summary.agent_duration_ms}ms)`,
        variant: "default",
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to analyze gaps";
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
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

      const updates: GapUpdate[] = highConfidenceGaps.map((gap) => ({
        gap_id: gap.id || "",
        field_name: gap.field_name,
        resolved_value: gap.suggested_resolution,
        resolution_status: "resolved",
        resolution_method: "ai_suggestion",
      }));

      const response = await collectionFlowApi.updateGaps(flowId, updates);

      toast({
        title: "Bulk Accept Complete",
        description: `Accepted ${response.gaps_resolved} high-confidence suggestions`,
        variant: "default",
      });

      // Refresh gaps
      await handleScanGaps();
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

      const updates: GapUpdate[] = aiSuggestedGaps.map((gap) => ({
        gap_id: gap.id || "",
        field_name: gap.field_name,
        resolved_value: "",
        resolution_status: "skipped",
        resolution_method: "manual_entry",
      }));

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

            <div className="flex-1" />

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
          <CardDescription>
            Click cells to edit, then save individually. Color-coded AI
            confidence:
            <Badge className="ml-2 bg-green-100 text-green-800">≥80%</Badge>
            <Badge className="ml-1 bg-yellow-100 text-yellow-800">60-79%</Badge>
            <Badge className="ml-1 bg-red-100 text-red-800">&lt;60%</Badge>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="ag-theme-alpine"
            style={{ height: 500, width: "100%" }}
          >
            <AgGridReact
              rowData={gaps}
              columnDefs={columnDefs}
              defaultColDef={{
                sortable: true,
                filter: true,
                resizable: true,
              }}
              getRowId={(params) =>
                params.data.id ||
                `${params.data.asset_id}-${params.data.field_name}`
              }
              onGridReady={onGridReady}
              onCellEditingStopped={handleCellEditingStopped}
              suppressRowClickSelection={true}
              rowSelection="multiple"
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
