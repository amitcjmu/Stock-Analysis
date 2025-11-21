/**
 * AG Grid Core Component for Attribute Mapping Redesign
 *
 * Issue #1077 - Unified attribute mapping interface with integrated data preview
 *
 * Features:
 * - Dynamic column generation from imported data structure
 * - Two row types:
 *   1. Mapping Row: Editable mapping cells with status indicators and green highlighting
 *   2. Data Preview Rows: Top 8 rows of imported data
 * - AG Grid professional appearance with ag-theme-quartz
 * - Performance optimized with useMemo hooks
 * - Type-safe props interface
 * - Visual feedback: Green highlighting for auto-mapped/approved columns
 *
 * Architecture Pattern: AI Grid (per Serena memory ai-grid-inventory-editing-pattern-2025-01)
 * Reference Implementation: AGGridAssetTable.tsx
 */

import React, { useMemo, useCallback, useEffect } from "react";
import { AgGridReact } from "ag-grid-react";
import type { ColDef, GridReadyEvent, RowClassParams } from "ag-grid-community";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import type { FieldMappingItem } from "@/types/api/discovery/field-mapping-types";
import type { TargetField } from "@/contexts/FieldOptionsContext";

// Import custom cell renderers
import { MappingCellRenderer } from "./renderers/MappingCellRenderer";
import { DataCellRenderer } from "./renderers/DataCellRenderer";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Imported data record structure (matches ImportedDataTab.tsx pattern)
 * Backend source: /api/v1/data-import/flows/{flow_id}/import-data
 */
export interface ImportedDataRecord {
  /** Internal ID for React keys */
  id: string;

  /** Original uploaded data - JSONB field with dynamic structure */
  raw_data: Record<string, unknown>;

  /** Processed data (optional) */
  processed_data?: Record<string, unknown>;

  /** Processing status */
  is_processed: boolean;

  /** Validation status */
  is_valid: boolean;

  /** Creation timestamp */
  created_at?: string;
}

/**
 * Mapping cell data structure for Row 1
 */
interface MappingCellData {
  /** Target field assigned to source field */
  target_field: string | null;

  /** Mapping approval status */
  status: string;

  /** AI confidence score [0.0-1.0] */
  confidence_score: number;

  /** Mapping ID for actions */
  mapping_id?: string;
}

/**
 * Row type discriminator
 */
type RowType = "mapping" | "data";

/**
 * Grid row data structure (2 types of rows)
 */
interface GridRowData {
  /** Row type discriminator */
  rowType: RowType;

  /** Unique row ID */
  id: string;

  /** Dynamic fields based on imported data columns */
  [key: string]: unknown;
}

/**
 * Component props interface
 */
export interface AttributeMappingAGGridProps {
  /** Discovery flow ID */
  flowId: string;

  /** Field mappings from backend */
  field_mappings: FieldMappingItem[];

  /** Imported data records */
  imported_data: ImportedDataRecord[];

  /** Available target fields for mapping dropdown (field names as strings) */
  available_target_fields: string[];

  /** Optional: Full target field objects for display_name lookup */
  available_target_fields_metadata?: TargetField[];

  /** Callback when user changes a field mapping */
  onMappingChange: (source_field: string, target_field: string) => void;

  /** Callback when user approves a mapping */
  onApproveMapping: (mapping_id: string) => void;

  /** Callback when user rejects a mapping */
  onRejectMapping: (mapping_id: string) => void;

  /** Callback when selection changes */
  onSelectionChange?: (selectedSourceFields: string[]) => void;

  /** Optional loading state */
  isLoading?: boolean;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const AttributeMappingAGGrid: React.FC<AttributeMappingAGGridProps> = ({
  flowId,
  field_mappings,
  imported_data,
  available_target_fields,
  available_target_fields_metadata,
  onMappingChange,
  onApproveMapping,
  onRejectMapping,
  onSelectionChange,
  isLoading = false,
}) => {
  const [gridApi, setGridApi] = React.useState<GridReadyEvent["api"] | null>(
    null,
  );
  const [selectedColumns, setSelectedColumns] = React.useState<Set<string>>(
    new Set(),
  );
  // Add custom AG Grid tooltip styling (from AGGridAssetTable.tsx:102-122)
  useEffect(() => {
    const style = document.createElement("style");
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

  // ============================================================================
  // DYNAMIC COLUMN GENERATION
  // ============================================================================

  /**
   * Generate AG Grid column definitions dynamically from imported data structure
   * Uses useMemo for performance optimization
   */
  const columnDefs = useMemo<Array<ColDef<GridRowData>>>(() => {
    // Handle empty data case
    if (!imported_data || imported_data.length === 0) {
      return [];
    }

    // Extract source fields from first record's raw_data
    const sourceFields = Object.keys(imported_data[0].raw_data);

    const cols: Array<ColDef<GridRowData>> = [];

    // Add Row Type Indicator Column with "Select All" checkbox (pinned left)
    cols.push({
      field: "rowType",
      width: 100,
      pinned: "left",
      sortable: false,
      filter: false,
      resizable: false,

      // Custom header with "Select All" checkbox
      headerComponent: () => {
        const allSelected = sourceFields.every((sf) => selectedColumns.has(sf));
        const someSelected =
          sourceFields.some((sf) => selectedColumns.has(sf)) && !allSelected;

        const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
          const newSelected = new Set(selectedColumns);
          if (e.target.checked) {
            // Select all source fields
            sourceFields.forEach((sf) => newSelected.add(sf));
          } else {
            // Deselect all source fields
            sourceFields.forEach((sf) => newSelected.delete(sf));
          }
          setSelectedColumns(newSelected);

          // Notify parent of selection change
          if (onSelectionChange) {
            onSelectionChange(Array.from(newSelected));
          }
        };

        return (
          <div className="flex items-center gap-2 w-full h-full">
            <input
              type="checkbox"
              checked={allSelected}
              ref={(input) => {
                if (input) {
                  input.indeterminate = someSelected;
                }
              }}
              onChange={handleSelectAll}
              className="w-4 h-4 cursor-pointer"
              title="Select All Columns"
            />
            <span className="font-semibold text-xs">Row Type</span>
          </div>
        );
      },

      cellRenderer: (params) => {
        if (!params.data) return null;

        const rowType = params.data.rowType;
        if (rowType === "mapping") {
          return (
            <div className="flex items-center h-full font-semibold text-blue-700">
              Map To:
            </div>
          );
        } else if (rowType === "data") {
          return (
            <div className="flex items-center h-full text-gray-500">Data:</div>
          );
        }
        return null;
      },
    });

    // Create column definition for each source field
    sourceFields.forEach((source_field) => {
      const colDef: ColDef<GridRowData> = {
        field: source_field,
        width: 200,
        resizable: true,
        sortable: true, // Enable sorting for better UX
        filter: true, // Enable filtering for data rows

        // Custom header component with checkbox
        headerComponent: () => {
          const isSelected = selectedColumns.has(source_field);

          const handleCheckboxChange = (
            e: React.ChangeEvent<HTMLInputElement>,
          ) => {
            const newSelected = new Set(selectedColumns);
            if (e.target.checked) {
              newSelected.add(source_field);
            } else {
              newSelected.delete(source_field);
            }
            setSelectedColumns(newSelected);

            // Notify parent of selection change
            if (onSelectionChange) {
              onSelectionChange(Array.from(newSelected));
            }
          };

          return (
            <div className="flex items-center gap-2 w-full h-full">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={handleCheckboxChange}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="font-semibold">{source_field}</span>
            </div>
          );
        },

        // Enable editing for mapping row only
        editable: (params) => params.data?.rowType === "mapping",

        // Value formatter for object/complex data types
        valueFormatter: (params) => {
          if (params.data?.rowType === "data") {
            const value = params.value;
            if (value === null || value === undefined) return "-";
            if (typeof value === "object") return JSON.stringify(value);
            return String(value);
          }
          return params.value;
        },

        // Value parser for object data types (required to prevent warning #48)
        valueParser: (params) => {
          // For data rows, parse JSON strings back to objects if needed
          if (
            params.data?.rowType === "data" &&
            typeof params.newValue === "string"
          ) {
            try {
              return JSON.parse(params.newValue);
            } catch {
              return params.newValue;
            }
          }
          return params.newValue;
        },

        // ✅ TASK 2: Green highlighting for auto-mapped/approved columns ONLY
        cellStyle: (params) => {
          // Only apply styling to mapping row cells
          if (params.data?.rowType === "mapping") {
            const mappingData = params.value as MappingCellData;

            // Safety check - ensure mappingData exists, has status, AND has a target field
            if (
              !mappingData ||
              !mappingData.status ||
              !mappingData.target_field
            ) {
              return {};
            }

            const status = mappingData.status;
            const hasValidTarget =
              mappingData.target_field &&
              mappingData.target_field.trim() !== "";

            // Green background ONLY for suggested/approved mappings WITH valid target fields
            if (
              hasValidTarget &&
              (status === "suggested" || status === "approved")
            ) {
              return {
                backgroundColor: "#d1fae5", // green-100
                borderLeft: "4px solid #10b981", // green-500
              };
            }

            // Yellow background for pending review WITH valid target fields
            if (hasValidTarget && status === "pending") {
              return {
                backgroundColor: "#fef3c7", // yellow-100
                borderLeft: "4px solid #f59e0b", // yellow-500
              };
            }
          }

          // Default: no special styling
          return {};
        },

        // Custom cell renderer based on row type
        cellRenderer: (params) => {
          if (!params.data) return null;

          // Row 1: Mapping row - use MappingCellRenderer
          if (params.data.rowType === "mapping") {
            const mappingData = params.value as MappingCellData;
            return (
              <MappingCellRenderer
                {...params}
                value={mappingData}
                sourceField={source_field}
                availableTargetFields={available_target_fields}
                availableTargetFieldsMetadata={available_target_fields_metadata}
                onSelect={onMappingChange}
                onApprove={
                  mappingData?.mapping_id ? onApproveMapping : undefined
                }
                onReject={mappingData?.mapping_id ? onRejectMapping : undefined}
              />
            );
          }

          // Rows 2-9: Data preview - use DataCellRenderer
          if (params.data.rowType === "data") {
            return <DataCellRenderer {...params} value={params.value} />;
          }

          return null;
        },

        // Tooltip for full value display
        tooltipValueGetter: (params) => {
          if (params.data?.rowType === "data") {
            const value = params.value;
            if (value === null || value === undefined) return "";
            if (typeof value === "object")
              return JSON.stringify(value, null, 2);
            return String(value);
          }
          return "";
        },
      };

      cols.push(colDef);
    });

    return cols;
  }, [
    imported_data,
    available_target_fields,
    available_target_fields_metadata,
    onMappingChange,
    onApproveMapping,
    onRejectMapping,
    selectedColumns,
    onSelectionChange,
  ]);

  // ============================================================================
  // ROW DATA TRANSFORMATION
  // ============================================================================

  /**
   * Transform field mappings and imported data into 2 row types
   * Row 1: Mapping row (editable with status-based highlighting)
   * Rows 2-9: Data preview (top 8 records)
   */
  const gridData = useMemo<GridRowData[]>(() => {
    // Handle empty data case
    if (!imported_data || imported_data.length === 0) {
      return [];
    }

    const sourceFields = Object.keys(imported_data[0].raw_data);

    // ROW 1: Mapping row
    const mappingRow: GridRowData = {
      rowType: "mapping",
      id: "mapping-row",
    };

    // Populate mapping row with field mapping data
    sourceFields.forEach((source_field) => {
      const mapping = field_mappings.find(
        (m) => m.source_field === source_field,
      );

      const cellData: MappingCellData = {
        target_field: mapping?.target_field || null,
        status: mapping?.status || "unmapped",
        confidence_score: mapping?.confidence_score || 0,
        mapping_id: mapping?.id,
      };

      console.log(`📊 Grid cell data for ${source_field}:`, cellData);

      mappingRow[source_field] = cellData;
    });

    // ROWS 2-9: Data preview (top 8 records)
    const dataRows: GridRowData[] = imported_data
      .slice(0, 8)
      .map((record, idx) => ({
        rowType: "data" as RowType,
        id: `data-${idx}`,
        ...record.raw_data,
      }));

    return [mappingRow, ...dataRows];
  }, [imported_data, field_mappings]);

  // ============================================================================
  // ROW STYLING
  // ============================================================================

  /**
   * Apply custom styling based on row type
   */
  const getRowStyle = useCallback((params: RowClassParams<GridRowData>) => {
    if (!params.data) return {};

    // Mapping row: Lighter background, bold text
    if (params.data.rowType === "mapping") {
      return {
        backgroundColor: "#f9fafb",
        fontWeight: 600,
      };
    }

    // Data rows: Alternating stripes for better readability
    if (params.data.rowType === "data") {
      const rowIndex = params.node.rowIndex || 0;
      return {
        backgroundColor: rowIndex % 2 === 0 ? "#ffffff" : "#f9fafb",
      };
    }

    return {};
  }, []);

  /**
   * Get row height based on row type
   */
  const getRowHeight = useCallback((params: { data: GridRowData }) => {
    if (!params.data) return 40;

    // Mapping row: 100px (taller for dropdown + status badges + action buttons to be fully visible)
    if (params.data.rowType === "mapping") return 100;

    // Data rows: 40px
    return 40;
  }, []);

  // ============================================================================
  // GRID CALLBACKS
  // ============================================================================

  const onGridReady = useCallback((params: GridReadyEvent<GridRowData>) => {
    // Store grid API reference
    setGridApi(params.api);

    // Auto-size columns to fit content (matches inventory pattern)
    params.api.autoSizeAllColumns(false);

    // If total width is less than container, fit to container
    const allColumnIds =
      params.api.getAllDisplayedColumns()?.map((col) => col.getColId()) || [];
    if (allColumnIds.length > 0) {
      params.api.sizeColumnsToFit();
    }
  }, []);

  // ============================================================================
  // DEFAULT COLUMN DEFINITION
  // ============================================================================

  const defaultColDef = useMemo<ColDef<GridRowData>>(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      minWidth: 150,
      tooltipValueGetter: (params) => {
        // Show tooltip for all cell values
        const value = params.value;
        if (value === null || value === undefined) return "";
        if (typeof value === "object") return JSON.stringify(value, null, 2);
        return String(value);
      },
    }),
    [],
  );

  // ============================================================================
  // RENDER
  // ============================================================================

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading mapping data...</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (!imported_data || imported_data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <p className="text-gray-600 text-lg">No imported data available</p>
          <p className="text-gray-500 text-sm mt-2">
            Upload a CSV or JSON file to begin field mapping
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      {/* Descriptive Header (matches inventory pattern) */}
      <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-sm font-semibold text-blue-900 mb-1">
          Attribute Mapping with Data Preview
        </h3>
        <p className="text-sm text-blue-700 leading-relaxed">
          <strong>Row 1 (Column Headers):</strong> Source field names from your
          imported CSV/JSON file.
          <br />
          <strong>Row 2 (Map To):</strong> Select target fields for each source
          column using dropdowns. Use checkboxes to select columns for bulk
          approval or rejection.
          <br />
          <strong>Rows 3-10 (Data Preview):</strong> First 8 records from your
          imported file to help verify your mapping selections.
          <br />
          <br />
          <strong>Color Legend:</strong>{" "}
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
            <span>Auto-Mapped</span>
          </span>
          {" • "}
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-500"></span>
            <span>Needs Review</span>
          </span>
          {" • "}
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
            <span>Approved</span>
          </span>
          {" • "}
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-gray-500"></span>
            <span>Unmapped</span>
          </span>
        </p>
      </div>

      <div className="ag-theme-quartz" style={{ height: 600, width: "100%" }}>
        <AgGridReact<GridRowData>
          theme="legacy"
          rowData={gridData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          headerHeight={40} // ✅ CRITICAL FIX: Enable column headers (was 0)
          getRowHeight={getRowHeight}
          getRowStyle={getRowStyle}
          onGridReady={onGridReady}
          getRowId={(params) => params.data.id}
          enableCellTextSelection={true}
          ensureDomOrder={true}
          suppressRowHoverHighlight={false}
          suppressCellFocus={false}
          animateRows={false}
          suppressMovableColumns={false} // Allow column reordering
        />
      </div>
    </div>
  );
};

export default AttributeMappingAGGrid;
