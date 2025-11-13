/**
 * Dependency Management Table for Assessment Flow
 *
 * Allows users to manually add/edit dependencies for selected applications.
 * Reuses Discovery inventory's AG Grid components for consistency.
 */

import React, { useMemo, useCallback, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type {
  ColDef,
  GridReadyEvent,
  CellEditingStoppedEvent,
} from 'ag-grid-community';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { DependencyCellEditor } from '@/components/discovery/inventory/components/AssetTable/DependencyCellEditor';
import { DependencyCellRenderer } from '@/components/discovery/inventory/components/AssetTable/DependencyCellRenderer';
import { Edit } from 'lucide-react';

interface Application {
  id: string;
  name: string;
  application_name?: string;
  asset_type?: string;
  business_criticality?: string;
  dependencies?: string; // Comma-separated asset IDs
}

interface DependencyManagementTableProps {
  applications: Application[];
  onUpdateDependencies: (applicationId: string, dependencies: string | null) => Promise<void>;
}

export const DependencyManagementTable: React.FC<DependencyManagementTableProps> = ({
  applications,
  onUpdateDependencies,
}) => {
  const gridApiRef = useRef<GridReadyEvent<Application>['api'] | null>(null);

  // Handle dependency updates
  const updateField = useCallback(
    async (params: { asset_id: string | number; field_name: string; field_value: any }) => {
      if (params.field_name === 'dependencies') {
        await onUpdateDependencies(params.asset_id.toString(), params.field_value);
      }
    },
    [onUpdateDependencies]
  );

  // Column definitions
  const columnDefs = useMemo<Array<ColDef<Application>>>(
    () => [
      {
        field: 'name',
        headerName: 'Application Name',
        sortable: true,
        filter: true,
        resizable: true,
        width: 250,
        pinned: 'left',
      },
      {
        field: 'application_name',
        headerName: 'Display Name',
        sortable: true,
        filter: true,
        resizable: true,
        width: 200,
      },
      {
        field: 'business_criticality',
        headerName: 'Criticality',
        sortable: true,
        filter: true,
        resizable: true,
        width: 150,
      },
      {
        field: 'dependencies',
        headerName: 'Dependencies',
        sortable: false,
        filter: false,
        resizable: true,
        editable: true,
        cellRenderer: DependencyCellRenderer,
        cellEditor: DependencyCellEditor,
        cellEditorPopup: true, // Show as popup for better UX
        cellEditorParams: {
          updateField, // Pass updateField function so cell editor can update directly
        },
        width: 350,
        tooltipValueGetter: () => 'Click to edit dependencies',
      },
    ],
    [updateField]
  );

  const defaultColDef = useMemo<ColDef<Application>>(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
    }),
    []
  );

  const onGridReady = useCallback((params: GridReadyEvent<Application>) => {
    gridApiRef.current = params.api;
    // Auto-size columns to fit content
    params.api.sizeColumnsToFit();
  }, []);

  // Handle cell editing (skip dependencies - handled by cell editor)
  const handleCellEditingStopped = useCallback(
    (event: CellEditingStoppedEvent<Application>) => {
      // Dependencies are handled by DependencyCellEditor, skip here
      if (event.colDef.field === 'dependencies') {
        return;
      }
    },
    []
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center">
          <Edit className="mr-2 h-5 w-5" />
          <CardTitle>Manage Dependencies</CardTitle>
        </div>
        <CardDescription>
          Click the Dependencies column to add or edit application dependencies.
          Select from available applications and servers.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="ag-theme-quartz" style={{ height: '500px', width: '100%' }}>
          <AgGridReact<Application>
            rowData={applications}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onCellEditingStopped={handleCellEditingStopped}
            rowSelection="multiple"
            suppressRowClickSelection={true}
            enableCellTextSelection={true}
            animateRows={true}
            pagination={true}
            paginationPageSize={20}
            paginationPageSizeSelector={[10, 20, 50, 100]}
          />
        </div>
      </CardContent>
    </Card>
  );
};
