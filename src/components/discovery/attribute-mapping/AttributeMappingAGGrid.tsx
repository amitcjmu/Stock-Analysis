/**
 * AG Grid Core Component for Attribute Mapping Redesign
 *
 * Issue #1077 - Unified attribute mapping interface with integrated data preview
 *
 * Features:
 * - Dynamic column generation from imported data structure
 * - Three row types:
 *   1. Mapping Row: Editable mapping cells with status indicators
 *   2. Header Row: Source CSV/JSON column headers
 *   3. Data Preview Rows: Top 8 rows of imported data
 * - AG Grid professional appearance with ag-theme-quartz
 * - Performance optimized with useMemo hooks
 * - Type-safe props interface
 *
 * Architecture Pattern: AI Grid (per Serena memory ai-grid-inventory-editing-pattern-2025-01)
 * Reference Implementation: AGGridAssetTable.tsx
 */

import React, { useMemo, useCallback, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type {
  ColDef,
  GridReadyEvent,
  RowClassParams,
} from 'ag-grid-community';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import type { FieldMappingItem } from '@/types/api/discovery/field-mapping-types';

// Import custom cell renderers
import { MappingCellRenderer } from './renderers/MappingCellRenderer';
import { ColumnHeaderRenderer } from './renderers/ColumnHeaderRenderer';
import { DataCellRenderer } from './renderers/DataCellRenderer';

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
type RowType = 'mapping' | 'header' | 'data';

/**
 * Grid row data structure (3 types of rows)
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

  /** Available target fields for mapping dropdown */
  available_target_fields: string[];

  /** Callback when user changes a field mapping */
  onMappingChange: (source_field: string, target_field: string) => void;

  /** Callback when user approves a mapping */
  onApproveMapping: (mapping_id: string) => void;

  /** Callback when user rejects a mapping */
  onRejectMapping: (mapping_id: string) => void;

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
  onMappingChange,
  onApproveMapping,
  onRejectMapping,
  isLoading = false,
}) => {
  // Add custom AG Grid tooltip styling (from AGGridAssetTable.tsx:102-122)
  useEffect(() => {
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

    // Create column definition for each source field
    return sourceFields.map((source_field) => {
      const colDef: ColDef<GridRowData> = {
        field: source_field,
        headerName: '', // No default header (custom header via Row 2)
        width: 200,
        resizable: true,
        sortable: false, // Disable sorting (not meaningful for mapping interface)
        filter: false,   // Disable filtering (not meaningful for mapping interface)

        // Enable editing for mapping row only
        editable: (params) => params.data?.rowType === 'mapping',

        // Custom cell renderer based on row type
        cellRenderer: (params) => {
          if (!params.data) return null;

          // Row 1: Mapping row - use MappingCellRenderer
          if (params.data.rowType === 'mapping') {
            const mappingData = params.value as MappingCellData;
            return (
              <MappingCellRenderer
                {...params}
                value={mappingData}
                sourceField={source_field}
                availableTargetFields={available_target_fields}
                onSelect={onMappingChange}
                onApprove={mappingData?.mapping_id ? onApproveMapping : undefined}
                onReject={mappingData?.mapping_id ? onRejectMapping : undefined}
              />
            );
          }

          // Row 2: Header row - use ColumnHeaderRenderer
          if (params.data.rowType === 'header') {
            return <ColumnHeaderRenderer {...params} value={params.value as string} />;
          }

          // Rows 3-10: Data preview - use DataCellRenderer
          if (params.data.rowType === 'data') {
            return <DataCellRenderer {...params} value={params.value} />;
          }

          return null;
        },

        // Tooltip for full value display
        tooltipValueGetter: (params) => {
          if (params.data?.rowType === 'data') {
            const value = params.value;
            if (value === null || value === undefined) return '';
            if (typeof value === 'object') return JSON.stringify(value, null, 2);
            return String(value);
          }
          return '';
        },
      };

      return colDef;
    });
  }, [imported_data]);

  // ============================================================================
  // ROW DATA TRANSFORMATION
  // ============================================================================

  /**
   * Transform field mappings and imported data into 3 row types
   * Row 1: Mapping row (editable)
   * Row 2: Header row (source field names)
   * Rows 3-10: Data preview (top 8 records)
   */
  const gridData = useMemo<GridRowData[]>(() => {
    // Handle empty data case
    if (!imported_data || imported_data.length === 0) {
      return [];
    }

    const sourceFields = Object.keys(imported_data[0].raw_data);

    // ROW 1: Mapping row
    const mappingRow: GridRowData = {
      rowType: 'mapping',
      id: 'mapping-row',
    };

    // Populate mapping row with field mapping data
    sourceFields.forEach((source_field) => {
      const mapping = field_mappings.find(
        (m) => m.source_field === source_field
      );

      mappingRow[source_field] = {
        target_field: mapping?.target_field || null,
        status: mapping?.status || 'unmapped',
        confidence_score: mapping?.confidence_score || 0,
        mapping_id: mapping?.id,
      } as MappingCellData;
    });

    // ROW 2: Header row (source field names)
    const headerRow: GridRowData = {
      rowType: 'header',
      id: 'header-row',
    };

    sourceFields.forEach((header) => {
      headerRow[header] = header;
    });

    // ROWS 3-10: Data preview (top 8 records)
    const dataRows: GridRowData[] = imported_data
      .slice(0, 8)
      .map((record, idx) => ({
        rowType: 'data' as RowType,
        id: `data-${idx}`,
        ...record.raw_data,
      }));

    return [mappingRow, headerRow, ...dataRows];
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
    if (params.data.rowType === 'mapping') {
      return {
        backgroundColor: '#f3f4f6',
        fontWeight: 600,
        height: '50px',
      };
    }

    // Header row: Gray background, italic
    if (params.data.rowType === 'header') {
      return {
        backgroundColor: '#e5e7eb',
        fontStyle: 'italic',
        height: '40px',
      };
    }

    // Data rows: Normal styling
    return {
      height: '40px',
    };
  }, []);

  /**
   * Get row height based on row type
   */
  const getRowHeight = useCallback((params: { data: GridRowData }) => {
    if (!params.data) return 40;

    // Mapping row: 50px (taller for status badges)
    if (params.data.rowType === 'mapping') return 50;

    // All other rows: 40px
    return 40;
  }, []);

  // ============================================================================
  // GRID CALLBACKS
  // ============================================================================

  const onGridReady = useCallback((params: GridReadyEvent<GridRowData>) => {
    // Auto-size columns on initial load
    params.api.sizeColumnsToFit();
  }, []);

  // ============================================================================
  // DEFAULT COLUMN DEFINITION
  // ============================================================================

  const defaultColDef = useMemo<ColDef<GridRowData>>(
    () => ({
      sortable: false,
      filter: false,
      resizable: true,
      suppressMovable: false,
    }),
    []
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
      <div
        className="ag-theme-quartz"
        style={{ height: 600, width: '100%' }}
      >
        <AgGridReact<GridRowData>
          theme="legacy"
          rowData={gridData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          headerHeight={0} // No default header (Row 2 serves as header)
          getRowHeight={getRowHeight}
          getRowStyle={getRowStyle}
          onGridReady={onGridReady}
          getRowId={(params) => params.data.id}
          enableCellTextSelection={true}
          ensureDomOrder={true}
          suppressRowHoverHighlight={false}
          suppressCellFocus={false}
          animateRows={false}
        />
      </div>
    </div>
  );
};

export default AttributeMappingAGGrid;
