import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AgGridReact } from 'ag-grid-react';
import type { ColDef, CellEditingStoppedEvent } from 'ag-grid-community';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

// Register modules once (safe to call multiple times; AG Grid guards internally)
ModuleRegistry.registerModules([AllCommunityModule]);

interface QualityIssueGridModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedRows: Record<string, unknown>[]) => void;
  onUpdateFields?: (updatedRows: Record<string, unknown>[]) => void;
  issue: {
    id: string;
    field_name: string;
    description?: string;
    severity?: 'low' | 'medium' | 'high' | 'critical';
    affected_records?: number;
  } | null;
  rows: Record<string, unknown>[];
}

export const QualityIssueGridModal: React.FC<QualityIssueGridModalProps> = ({
  isOpen,
  onClose,
  onSave,
  onUpdateFields,
  issue,
  rows,
}) => {
  const [rowData, setRowData] = useState<Record<string, unknown>[]>(rows || []);

  useEffect(() => {
    // Initialize with rows and auto-populate suggestions for empty issue field values
    const initializeWithSuggestions = (incoming: Record<string, unknown>[], issueFieldLabel?: string) => {
      const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
      const resolveIssueKey = (sample: Record<string, unknown>, label?: string): string | null => {
        if (!label) return null;
        const keys = Object.keys(sample || {});
        // Exact match
        if (label in sample) return label;
        // Normalized equality
        const labelNorm = norm(label);
        for (const k of keys) {
          if (norm(k) === labelNorm) return k;
        }
        // Common aliases
        const aliases: Record<string, string[]> = {
          os: ['operating_system', 'os', 'os_name'],
          ip: ['ip', 'ip_address', 'ipaddr', 'ipaddress'],
        };
        for (const [alias, candidates] of Object.entries(aliases)) {
          if (labelNorm === alias || candidates.some((c) => norm(c) === labelNorm)) {
            const found = candidates.find((c) => c in sample);
            if (found) return found;
          }
        }
        // snake_case guess
        const snake = label.replace(/\s+/g, '_').replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
        if (snake in sample) return snake;
        return label;
      };
      const getSuggestion = (fieldKey: string, record: Record<string, unknown>): unknown => {
        const fieldNorm = norm(fieldKey);
        // Simple heuristics; can be replaced by backend agent suggestions later
        if (fieldNorm.includes('operatingsystem') || fieldNorm === 'os' || fieldNorm === 'os_name') {
          return 'Windows Server 2019';
        }
        if (fieldNorm.includes('ip') && fieldNorm.includes('address')) {
          return '192.168.1.100';
        }
        if (fieldNorm === 'hostname' || fieldNorm.includes('host')) {
          const id = record['id'] ?? record['ID'] ?? '';
          return `server-${String(id || '001')}`;
        }
        if (fieldNorm === 'cpu' || fieldNorm === 'cpucores') {
          return record['cpu_cores'] ?? 4;
        }
        if (fieldNorm === 'memory' || fieldNorm === 'memorygb') {
          return record['memory_gb'] ?? 8;
        }
        return 'Unknown';
      };
      if (!incoming || incoming.length === 0) return incoming || [];
      const sample = incoming[0] || {};
      const issueKey = resolveIssueKey(sample, issueFieldLabel);
      if (!issueKey) return incoming;
      return incoming.map((rec) => {
        const value = rec[issueKey];
        const isEmpty =
          value === null ||
          value === undefined ||
          (typeof value === 'string' && value.trim() === '');
        if (!isEmpty) return rec;
        const suggested = getSuggestion(issueKey, rec);
        return {
          ...rec,
          [issueKey]: suggested,
        };
      });
    };
    setRowData(initializeWithSuggestions(rows || [], issue?.field_name));
  }, [rows, isOpen]);

  // Derive columns from data keys; ensure common quality fields are present
  const allKeys = useMemo(() => {
    const keys = new Set<string>();
    rowData.forEach((r) => Object.keys(r || {}).forEach((k) => keys.add(k)));
    // Ensure typical quality issue fields appear even if missing in sample
    ['ip_address', 'hostname', 'cpu', 'cpu_cores', 'memory_gb'].forEach((k) => keys.add(k));
    return Array.from(keys);
  }, [rowData]);

  const columnDefs = useMemo<ColDef<Record<string, unknown>>[]>(() => {
    return allKeys.map((key) => {
      const header =
        key
          .split('_')
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
          .join(' ');
      const isIssueField = issue?.field_name === key;
      return {
        field: key,
        headerName: header,
        editable: true,
        resizable: true,
        sortable: true,
        filter: true,
        cellClass: isIssueField ? 'bg-yellow-50' : undefined,
      } as ColDef<Record<string, unknown>>;
    });
  }, [allKeys, issue?.field_name]);

  const defaultColDef = useMemo<ColDef>(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
    }),
    []
  );

  const handleCellEditingStopped = useCallback(
    (event: CellEditingStoppedEvent<Record<string, unknown>>) => {
      if (event.rowIndex == null || !event.colDef.field) return;
      const idx = event.rowIndex;
      const field = String(event.colDef.field);
      const newValue = event.newValue;
      setRowData((prev) => {
        const updated = [...prev];
        const existing = { ...(updated[idx] || {}) };
        existing[field] = newValue;
        updated[idx] = existing;
        return updated;
      });
    },
    []
  );

  const handleAddRow = () => {
    // Create an empty row with known keys
    const newRow: Record<string, unknown> = {};
    allKeys.forEach((k) => {
      newRow[k] = '';
    });
    setRowData((prev) => [newRow, ...prev]);
  };

  const handleSave = () => {
    onSave(rowData);
  };
  const handleUpdateFields = () => {
    if (onUpdateFields) onUpdateFields(rowData);
  };

  if (!issue) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Resolve Quality Issue
            {issue.severity && (
              <Badge variant="outline" className={
                issue.severity === 'critical' ? 'text-red-700 border-red-300' :
                issue.severity === 'high' ? 'text-red-600 border-red-300' :
                issue.severity === 'medium' ? 'text-amber-600 border-amber-300' :
                'text-blue-600 border-blue-300'
              }>
                {issue.severity.toUpperCase()}
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            Edit the highlighted field values directly in the grid. Use Update Fields to store edits for review, or Save and Mark Resolved to resolve this issue.
          </DialogDescription>
          <div className="text-sm text-gray-600">
            Field: <span className="font-medium">{issue.field_name}</span>
            {typeof issue.affected_records === 'number' && (
              <span className="ml-2 text-gray-500">({issue.affected_records} affected)</span>
            )}
            {issue.description && <div className="mt-1">{issue.description}</div>}
          </div>
        </DialogHeader>

        <div className="flex items-center justify-between mb-3">
          <div className="text-sm text-muted-foreground">
            Edit cells directly. Add rows as needed. The highlighted column corresponds to the selected issue.
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleAddRow}>
              Add Row
            </Button>
            <Button size="sm" onClick={handleUpdateFields} data-testid="update-fields-button-top">
              Update Fields
            </Button>
          </div>
        </div>

        <div className="flex-1 min-h-0">
          <div className="ag-theme-quartz" style={{ height: 520, width: '100%' }}>
            <AgGridReact<Record<string, unknown>>
              theme="legacy"
              rowData={rowData}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              onCellEditingStopped={handleCellEditingStopped}
              rowSelection="single"
              ensureDomOrder
              enableCellTextSelection
            />
          </div>
        </div>

        <DialogFooter className="border-t pt-4 mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleUpdateFields} data-testid="update-fields-button">
            Update Fields
          </Button>
          <Button onClick={handleSave}>
            Save and Mark Resolved
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default QualityIssueGridModal;

