/**
 * Bulk Data Grid Component
 * 
 * Grid interface for bulk data entry across multiple applications
 * Agent Team B3 - Task B3.2 Frontend Implementation
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Upload, 
  Download, 
  Plus, 
  Trash2, 
  Copy, 
  Save, 
  AlertCircle,
  CheckCircle,
  Filter,
  MoreHorizontal
} from 'lucide-react';
import { cn } from '@/lib/utils';

import { BulkUpload } from './components/BulkUpload';
import type { BulkDataGridProps, ApplicationSummary, FormField, CollectionFormData } from './types';

interface GridRow {
  applicationId: string;
  applicationName: string;
  data: CollectionFormData;
  validationStatus: 'valid' | 'invalid' | 'warning' | 'pending';
  completionPercentage: number;
  isSelected: boolean;
}

export const BulkDataGrid: React.FC<BulkDataGridProps> = ({
  applications,
  fields,
  onDataChange,
  onBulkUpload,
  templateOptions = [],
  className
}) => {
  const [gridData, setGridData] = useState<Map<string, GridRow>>(
    new Map(
      applications.map(app => [
        app.id,
        {
          applicationId: app.id,
          applicationName: app.name,
          data: {},
          validationStatus: 'pending',
          completionPercentage: 0,
          isSelected: false
        }
      ])
    )
  );

  const [selectedFields, setSelectedFields] = useState<Set<string>>(
    new Set(fields.slice(0, 5).map(f => f.id)) // Show first 5 fields by default
  );
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [filterText, setFilterText] = useState('');

  // Get visible fields based on selection
  const visibleFields = useMemo(() => 
    fields.filter(field => selectedFields.has(field.id)),
    [fields, selectedFields]
  );

  // Get filtered rows
  const filteredRows = useMemo(() => {
    const rows = Array.from(gridData.values());
    if (!filterText) return rows;
    
    return rows.filter(row => 
      row.applicationName.toLowerCase().includes(filterText.toLowerCase()) ||
      Object.values(row.data).some(value => 
        String(value).toLowerCase().includes(filterText.toLowerCase())
      )
    );
  }, [gridData, filterText]);

  // Handle cell value change
  const handleCellChange = useCallback((applicationId: string, fieldId: string, value: any) => {
    setGridData(prev => {
      const newData = new Map(prev);
      const row = newData.get(applicationId);
      if (row) {
        const updatedData = { ...row.data, [fieldId]: value };
        const completionPercentage = (Object.keys(updatedData).length / visibleFields.length) * 100;
        
        newData.set(applicationId, {
          ...row,
          data: updatedData,
          completionPercentage,
          validationStatus: value ? 'valid' : 'pending' // Simplified validation
        });
      }
      return newData;
    });
    
    onDataChange(applicationId, fieldId, value);
  }, [onDataChange, visibleFields.length]);

  // Handle row selection
  const handleRowSelection = useCallback((applicationId: string, selected: boolean) => {
    setGridData(prev => {
      const newData = new Map(prev);
      const row = newData.get(applicationId);
      if (row) {
        newData.set(applicationId, { ...row, isSelected: selected });
      }
      return newData;
    });
  }, []);

  // Handle select all/none
  const handleSelectAll = useCallback((selected: boolean) => {
    setGridData(prev => {
      const newData = new Map(prev);
      for (const [id, row] of newData) {
        newData.set(id, { ...row, isSelected: selected });
      }
      return newData;
    });
  }, []);

  // Handle bulk operations
  const handleBulkCopy = useCallback(() => {
    const selectedRows = Array.from(gridData.values()).filter(row => row.isSelected);
    if (selectedRows.length === 0) return;
    
    const sourceRow = selectedRows[0];
    const targetRows = selectedRows.slice(1);
    
    setGridData(prev => {
      const newData = new Map(prev);
      targetRows.forEach(targetRow => {
        newData.set(targetRow.applicationId, {
          ...targetRow,
          data: { ...sourceRow.data },
          completionPercentage: sourceRow.completionPercentage,
          validationStatus: sourceRow.validationStatus
        });
      });
      return newData;
    });
  }, [gridData]);

  const handleBulkClear = useCallback(() => {
    const selectedRows = Array.from(gridData.values()).filter(row => row.isSelected);
    
    setGridData(prev => {
      const newData = new Map(prev);
      selectedRows.forEach(row => {
        newData.set(row.applicationId, {
          ...row,
          data: {},
          completionPercentage: 0,
          validationStatus: 'pending'
        });
      });
      return newData;
    });
  }, [gridData]);

  // Render cell based on field type
  const renderCell = (row: GridRow, field: FormField) => {
    const value = row.data[field.id];
    const cellId = `${row.applicationId}-${field.id}`;

    switch (field.fieldType) {
      case 'select':
        return (
          <Select
            value={value || ''}
            onValueChange={(newValue) => handleCellChange(row.applicationId, field.id, newValue)}
          >
            <SelectTrigger className="h-8 min-w-[120px]">
              <SelectValue placeholder="Select..." />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
        
      case 'checkbox':
        return (
          <Checkbox
            checked={Boolean(value)}
            onCheckedChange={(checked) => handleCellChange(row.applicationId, field.id, checked)}
          />
        );
        
      case 'textarea':
        return (
          <Input
            value={value || ''}
            onChange={(e) => handleCellChange(row.applicationId, field.id, e.target.value)}
            placeholder={field.placeholder}
            className="h-8 min-w-[200px]"
          />
        );
        
      default:
        return (
          <Input
            value={value || ''}
            onChange={(e) => handleCellChange(row.applicationId, field.id, e.target.value)}
            placeholder={field.placeholder}
            className="h-8 min-w-[120px]"
          />
        );
    }
  };

  const selectedRowCount = Array.from(gridData.values()).filter(row => row.isSelected).length;
  const totalRows = gridData.size;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header Controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Bulk Data Entry</CardTitle>
              <CardDescription>
                Enter data for multiple applications. Use bulk operations to speed up data entry.
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Template Selection */}
              {templateOptions.length > 0 && (
                <Select onValueChange={(templateId) => console.log('Apply template:', templateId)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Apply template..." />
                  </SelectTrigger>
                  <SelectContent>
                    {templateOptions.map(template => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              
              {/* Upload Dialog */}
              <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload CSV
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Upload Bulk Data</DialogTitle>
                    <DialogDescription>
                      Upload a CSV file with application data. The file should include columns matching the form fields.
                    </DialogDescription>
                  </DialogHeader>
                  <BulkUpload
                    fields={fields}
                    onUpload={async (file) => {
                      if (onBulkUpload) {
                        await onBulkUpload(file);
                      }
                      setShowUploadDialog(false);
                    }}
                    templateOptions={templateOptions}
                  />
                </DialogContent>
              </Dialog>
              
              {/* Export Data */}
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
          
          {/* Field Selection and Filters */}
          <div className="flex items-center gap-4 pt-3 border-t">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Filter applications..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="h-8 w-[200px]"
              />
            </div>
            
            <Select
              value={Array.from(selectedFields).join(',')}
              onValueChange={(value) => {
                const fieldIds = value ? value.split(',') : [];
                setSelectedFields(new Set(fieldIds));
              }}
            >
              <SelectTrigger className="w-[200px] h-8">
                <SelectValue placeholder="Select fields to show..." />
              </SelectTrigger>
              <SelectContent>
                {fields.map(field => (
                  <SelectItem key={field.id} value={field.id}>
                    {field.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {selectedRowCount > 0 && (
              <div className="flex items-center gap-2 ml-auto">
                <Badge variant="outline">
                  {selectedRowCount} selected
                </Badge>
                
                <Button variant="outline" size="sm" onClick={handleBulkCopy}>
                  <Copy className="h-4 w-4 mr-1" />
                  Copy Data
                </Button>
                
                <Button variant="outline" size="sm" onClick={handleBulkClear}>
                  <Trash2 className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Data Grid */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-auto max-h-[600px]">
            <Table>
              <TableHeader className="sticky top-0 bg-background border-b">
                <TableRow>
                  <TableHead className="w-[50px] sticky left-0 bg-background border-r">
                    <Checkbox
                      checked={selectedRowCount === totalRows && totalRows > 0}
                      indeterminate={selectedRowCount > 0 && selectedRowCount < totalRows}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead className="min-w-[200px] sticky left-[50px] bg-background border-r">
                    Application Name
                  </TableHead>
                  <TableHead className="w-[100px]">Progress</TableHead>
                  {visibleFields.map(field => (
                    <TableHead key={field.id} className="min-w-[150px]">
                      <div className="flex items-center gap-1">
                        {field.label}
                        {field.validation?.required && (
                          <span className="text-red-500">*</span>
                        )}
                        {field.businessImpactScore >= 0.05 && (
                          <Badge variant="secondary" className="text-xs">
                            High Impact
                          </Badge>
                        )}
                      </div>
                    </TableHead>
                  ))}
                  <TableHead className="w-[50px]">
                    <MoreHorizontal className="h-4 w-4" />
                  </TableHead>
                </TableRow>
              </TableHeader>
              
              <TableBody>
                {filteredRows.map(row => (
                  <TableRow 
                    key={row.applicationId}
                    className={cn(row.isSelected && 'bg-muted/50')}
                  >
                    <TableCell className="sticky left-0 bg-background border-r">
                      <Checkbox
                        checked={row.isSelected}
                        onCheckedChange={(checked) => 
                          handleRowSelection(row.applicationId, Boolean(checked))
                        }
                      />
                    </TableCell>
                    
                    <TableCell className="font-medium sticky left-[50px] bg-background border-r">
                      <div className="flex items-center gap-2">
                        {row.validationStatus === 'valid' && (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        )}
                        {row.validationStatus === 'invalid' && (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        {row.applicationName}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 transition-all"
                            style={{ width: `${row.completionPercentage}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(row.completionPercentage)}%
                        </span>
                      </div>
                    </TableCell>
                    
                    {visibleFields.map(field => (
                      <TableCell key={field.id}>
                        {renderCell(row, field)}
                      </TableCell>
                    ))}
                    
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div>
          Showing {filteredRows.length} of {totalRows} applications
        </div>
        
        <div className="flex items-center gap-4">
          <div>
            {selectedRowCount > 0 && `${selectedRowCount} selected`}
          </div>
          
          <Button variant="outline" size="sm">
            <Save className="h-4 w-4 mr-2" />
            Save Progress
          </Button>
        </div>
      </div>
    </div>
  );
};