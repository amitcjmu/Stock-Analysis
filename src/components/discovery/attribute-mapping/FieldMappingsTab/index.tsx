import React, { useState, useEffect, useCallback } from "react";
import { RefreshCw, LayoutGrid, Columns } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useFieldOptions } from "../../../../contexts/FieldOptionsContext";
import { useAuth } from "../../../../contexts/AuthContext";
import { apiCall } from "../../../../config/api";

// Components
import ThreeColumnFieldMapper from "./components/ThreeColumnFieldMapper/ThreeColumnFieldMapper";
import { AttributeMappingAGGrid } from "../AttributeMappingAGGrid";
import { BulkMappingActions } from "../BulkMappingActions";

// Types
import type { FieldMappingsTabProps } from "./types";
import type { ImportedDataRecord } from "../AttributeMappingAGGrid";

// ============================================================================
// VIEW TOGGLE COMPONENT
// ============================================================================

interface ViewToggleProps {
  viewMode: "grid" | "legacy";
  onViewModeChange: (mode: "grid" | "legacy") => void;
}

const ViewToggle: React.FC<ViewToggleProps> = ({
  viewMode,
  onViewModeChange,
}) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-gray-100 rounded-lg">
      <button
        onClick={() => onViewModeChange("grid")}
        className={`
          px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
          ${
            viewMode === "grid"
              ? "bg-white text-blue-600 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          }
        `}
        aria-pressed={viewMode === "grid"}
        aria-label="Switch to Grid View"
      >
        <LayoutGrid className="w-4 h-4" />
        Grid View
      </button>

      <button
        onClick={() => onViewModeChange("legacy")}
        className={`
          px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2
          ${
            viewMode === "legacy"
              ? "bg-white text-blue-600 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          }
        `}
        aria-pressed={viewMode === "legacy"}
        aria-label="Switch to Tabbed View"
      >
        <Columns className="w-4 h-4" />
        Tabbed View
      </button>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  fieldMappings,
  isAnalyzing,
  onMappingAction,
  onRemoveMapping,
  onMappingChange,
  onRefresh,
  onApproveMappingWithLearning,
  onRejectMappingWithLearning,
  onBulkLearnMappings,
  learnedMappings,
  clientAccountId,
  engagementId,
  sessionInfo,
  canContinueToDataCleansing,
  onContinueToDataCleansing
}) => {
  // ============================================================================
  // STATE & HOOKS
  // ============================================================================

  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState<"grid" | "legacy">(() => {
    const saved = localStorage.getItem("attribute-mapping-view-mode");
    return saved === "grid" || saved === "legacy" ? saved : "legacy";
  });

  // Track selected source fields from AG Grid
  const [selectedSourceFields, setSelectedSourceFields] = useState<string[]>(
    [],
  );

  const queryClient = useQueryClient();
  const { client, engagement, getAuthHeaders } = useAuth();
  const { availableFields, isLoading: fieldsLoading } = useFieldOptions();

  // Get flow_id from sessionInfo
  const flow_id = sessionInfo?.flowId;

  // ============================================================================
  // VIEW MODE PERSISTENCE
  // ============================================================================

  const handleViewModeChange = useCallback((mode: "grid" | "legacy") => {
    setViewMode(mode);
    localStorage.setItem("attribute-mapping-view-mode", mode);
  }, []);

  // ============================================================================
  // IMPORTED DATA FETCHING (for Grid View only)
  // ============================================================================

  const {
    data: importResponse,
    isLoading: importDataLoading,
    error: importDataError,
  } = useQuery({
    queryKey: ["imported-data", client?.id, engagement?.id, flow_id],
    queryFn: async () => {
      try {
        const headers = getAuthHeaders();
        if (client?.id) {
          headers["X-Client-Account-ID"] = client.id;
        }
        if (engagement?.id) {
          headers["X-Engagement-ID"] = engagement.id;
        }

        // Use flow-specific endpoint if flow_id is available
        if (flow_id) {
          return await apiCall(
            `/api/v1/data-import/flows/${flow_id}/import-data`,
            {
              method: "GET",
              headers,
            },
          );
        } else {
          // Fallback to latest-import endpoint if no flow_id
          return await apiCall("/api/v1/data-import/latest-import", {
            method: "GET",
            headers,
          });
        }
      } catch (error: unknown) {
        // Handle 404 errors gracefully
        const hasErrorStatus = (err: unknown): err is { status: number } => {
          return typeof err === "object" && err !== null && "status" in err;
        };

        if (hasErrorStatus(error) && error.status === 404) {
          console.log("Import endpoint not available yet");
          return {
            success: false,
            data: [],
            import_metadata: null,
            message: "No data imports found",
          };
        }
        throw error;
      }
    },
    enabled: !!client && !!engagement && viewMode === "grid", // Only fetch for Grid View
    staleTime: 30000,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });

  // Transform imported data into AG Grid format
  const importedData: ImportedDataRecord[] = React.useMemo(() => {
    if (!importResponse || !importResponse.success) {
      return [];
    }

    return (importResponse.data || []).map(
      (rawRecord: unknown, index: number) => ({
        id: `record_${index}`,
        raw_data: rawRecord as Record<string, unknown>,
        is_processed: true,
        is_valid: true,
      }),
    );
  }, [importResponse]);

  // ============================================================================
  // BULK ACTIONS HANDLERS (for Grid View)
  // ============================================================================

  const handleApproveSelected = useCallback(async () => {
    // Approve selected field mappings
    const selectedMappings = fieldMappings.filter((m) =>
      selectedSourceFields.includes(m.source_field),
    );

    console.log(
      "🔍 Approve Selected - Found mappings:",
      selectedMappings.length,
    );
    console.log("🔍 Selected source fields:", selectedSourceFields);

    if (selectedMappings.length === 0) {
      console.warn("⚠️ No mappings selected to approve");
      return;
    }

    for (const mapping of selectedMappings) {
      try {
        // If unmapped, default to custom_attributes
        if (!mapping.target_field || mapping.target_field.trim() === "") {
          console.log(
            `📝 Mapping ${mapping.source_field} to custom_attributes (was unmapped)`,
          );
          onMappingChange(mapping.id, "custom_attributes");
        }

        console.log(
          `✅ Approving mapping: ${mapping.source_field} → ${mapping.target_field || "custom_attributes"}`,
        );
        onMappingAction(mapping.id, "approve");
      } catch (error) {
        console.error(`Failed to approve mapping ${mapping.id}:`, error);
      }
    }

    // Clear selection and refresh data
    setSelectedSourceFields([]);
    queryClient.invalidateQueries({ queryKey: ["field-mappings"] });
    if (onRefresh) {
      onRefresh();
    }
  }, [
    fieldMappings,
    selectedSourceFields,
    onMappingAction,
    onMappingChange,
    onRefresh,
    queryClient,
  ]);

  const handleRejectSelected = useCallback(async () => {
    // Reject selected field mappings
    const selectedMappings = fieldMappings.filter((m) =>
      selectedSourceFields.includes(m.source_field),
    );

    console.log(
      "🔍 Reject Selected - Found mappings:",
      selectedMappings.length,
    );

    if (selectedMappings.length === 0) {
      console.warn("⚠️ No mappings selected to reject");
      return;
    }

    for (const mapping of selectedMappings) {
      try {
        console.log(`❌ Rejecting mapping: ${mapping.source_field}`);
        onMappingAction(mapping.id, "reject");
      } catch (error) {
        console.error(`Failed to reject mapping ${mapping.id}:`, error);
      }
    }

    // Clear selection and refresh data
    setSelectedSourceFields([]);
    queryClient.invalidateQueries({ queryKey: ["field-mappings"] });
    if (onRefresh) {
      onRefresh();
    }
  }, [
    fieldMappings,
    selectedSourceFields,
    onMappingAction,
    onRefresh,
    queryClient,
  ]);

  const handleReset = useCallback(async () => {
    // Reset all mappings to AI suggestions
    // This would typically call a backend endpoint to reset mappings
    console.log("Reset mappings to AI suggestions");

    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ["field-mappings"] });
    if (onRefresh) {
      onRefresh();
    }
  }, [onRefresh, queryClient]);

  const handleExport = useCallback(() => {
    // Export will be handled by BulkMappingActions component's built-in CSV export
    console.log("Export mappings to CSV");
  }, []);

  // ============================================================================
  // AG GRID MAPPING HANDLERS
  // ============================================================================

  const handleMappingChangeForGrid = useCallback(
    (source_field: string, target_field: string) => {
      // Find the mapping by source field
      const mapping = fieldMappings.find(
        (m) => m.source_field === source_field,
      );
      if (mapping && onMappingChange) {
        onMappingChange(mapping.id, target_field);
      }
    },
    [fieldMappings, onMappingChange],
  );

  const handleApproveMappingForGrid = useCallback(
    (mapping_id: string) => {
      onMappingAction(mapping_id, "approve");
    },
    [onMappingAction],
  );

  const handleRejectMappingForGrid = useCallback(
    (mapping_id: string) => {
      onMappingAction(mapping_id, "reject");
    },
    [onMappingAction],
  );

  // ============================================================================
  // LOADING & ERROR STATES
  // ============================================================================

  // Filter mappings based on visible statuses - with safety check
  const safeFieldMappings = Array.isArray(fieldMappings) ? fieldMappings : [];

  if (isAnalyzing || fieldsLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Analyzing field mappings...</p>
          <p className="text-sm text-gray-500 mt-2">
            AI agents are determining the best field mappings for your data
          </p>
        </div>
      </div>
    );
  }

  if (!safeFieldMappings || safeFieldMappings.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-2">No field mappings available</p>
        <p className="text-sm text-gray-500">
          Complete the data import to see AI-generated field mappings
        </p>
      </div>
    );
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-4">
      {/* View Toggle */}
      <div className="flex items-center justify-end">
        <ViewToggle
          viewMode={viewMode}
          onViewModeChange={handleViewModeChange}
        />
      </div>

      {/* Conditional View Rendering */}
      {viewMode === "grid" ? (
        <>
          {/* Bulk Actions Toolbar */}
          <BulkMappingActions
            flow_id={flow_id || ""}
            field_mappings={safeFieldMappings}
            selectedSourceFields={selectedSourceFields}
            onApproveSelected={handleApproveSelected}
            onRejectSelected={handleRejectSelected}
            onReset={handleReset}
            onExport={handleExport}
          />

          {/* AG Grid View */}
          {importDataLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-600 mr-2" />
              <span className="text-gray-600">Loading imported data...</span>
            </div>
          ) : importDataError ? (
            <div className="text-center py-8">
              <p className="text-red-600 mb-2">Failed to load imported data</p>
              <p className="text-sm text-gray-500">
                Please refresh the page or contact support
              </p>
            </div>
          ) : (
            <AttributeMappingAGGrid
              flowId={flow_id || ""}
              field_mappings={safeFieldMappings}
              imported_data={importedData}
              available_target_fields={availableFields.map((f) => f.name)}
              onMappingChange={handleMappingChangeForGrid}
              onApproveMapping={handleApproveMappingForGrid}
              onRejectMapping={handleRejectMappingForGrid}
              onSelectionChange={setSelectedSourceFields}
              isLoading={false}
            />
          )}
        </>
      ) : (
        <>
          {/* Tabbed View */}
          <ThreeColumnFieldMapper
          fieldMappings={safeFieldMappings}
          availableFields={availableFields}
          onMappingAction={onMappingAction}
          onRemoveMapping={onRemoveMapping}
          onMappingChange={onMappingChange}
          onRefresh={onRefresh}
          onApproveMappingWithLearning={onApproveMappingWithLearning}
          onRejectMappingWithLearning={onRejectMappingWithLearning}
          onBulkLearnMappings={onBulkLearnMappings}
          learnedMappings={learnedMappings}
          clientAccountId={clientAccountId}
          engagementId={engagementId}
          // Continue to data cleansing props
          canContinueToDataCleansing={canContinueToDataCleansing}
          onContinueToDataCleansing={onContinueToDataCleansing}
        />
        </>
      )}
    </div>
  );
};

export default FieldMappingsTab;
