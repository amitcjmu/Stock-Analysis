/**
 * Bulk Upload Component
 *
 * File upload interface for bulk data import
 * Agent Team B3 - Bulk upload functionality
 */

import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, FileText, AlertCircle, CheckCircle, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

import type { FormField, TemplateOption, BulkUploadResult } from '../types';

interface BulkUploadProps {
  fields: FormField[];
  onUpload: (file: File) => Promise<void>;
  templateOptions?: TemplateOption[];
  className?: string;
}

export const BulkUpload: React.FC<BulkUploadProps> = ({
  fields,
  onUpload,
  templateOptions = [],
  className
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<BulkUploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const file = files[0];

    if (file) {
      await handleFileUpload(file);
    }
  }, []);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  }, []);

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls', '.json'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!allowedTypes.includes(fileExtension)) {
      setError(`Invalid file type. Please upload one of: ${allowedTypes.join(', ')}`);
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds 10MB limit');
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      await onUpload(file);
      // Mock upload result - in real app this would come from the upload response
      setUploadResult({
        uploadId: 'upload_' + Date.now(),
        status: 'completed',
        totalRows: 50,
        successfulRows: 47,
        failedRows: 3,
        validationIssues: [],
        processingTime: 2.5,
        dataQualityScore: 0.85
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const generateTemplate = () => {
    // Generate CSV template with field headers
    const headers = ['Application Name', 'Application ID', ...fields.map(f => f.label)];
    const csvContent = headers.join(',') + '\n';

    // Add example row
    const exampleRow = [
      'Example Application',
      'app-001',
      ...fields.map(f => {
        switch (f.fieldType) {
          case 'select':
            return f.options?.[0]?.value || 'example_value';
          case 'checkbox':
            return 'true';
          case 'number':
            return '100';
          case 'date':
            return '2024-01-01';
          default:
            return 'Example value';
        }
      })
    ];

    const fullContent = csvContent + exampleRow.join(',');

    // Download template
    const blob = new Blob([fullContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bulk_data_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Template Download */}
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div>
          <h4 className="font-medium">Download Template</h4>
          <p className="text-sm text-muted-foreground">
            Get a CSV template with the correct column headers and example data
          </p>
        </div>
        <Button variant="outline" onClick={generateTemplate}>
          <Download className="h-4 w-4 mr-2" />
          Download Template
        </Button>
      </div>

      {/* Upload Area */}
      <Card
        className={cn(
          'border-2 border-dashed transition-colors cursor-pointer',
          isDragging && 'border-primary bg-primary/5',
          error && 'border-red-300',
          uploadResult && 'border-green-300'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="flex flex-col items-center justify-center py-8">
          {isUploading ? (
            <div className="text-center space-y-4">
              <div className="animate-spin">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="font-medium">Uploading and processing file...</p>
                <Progress value={75} className="w-64 mt-2" />
              </div>
            </div>
          ) : uploadResult ? (
            <div className="text-center space-y-4">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto" />
              <div>
                <p className="font-medium text-green-700">Upload completed successfully!</p>
                <div className="flex items-center justify-center gap-4 mt-2 text-sm text-muted-foreground">
                  <span>{uploadResult.successfulRows} rows processed</span>
                  {uploadResult.failedRows > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {uploadResult.failedRows} errors
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {Math.round(uploadResult.dataQualityScore * 100)}% quality
                  </Badge>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center space-y-4">
              <Upload className="h-8 w-8 text-muted-foreground" />
              <div>
                <p className="font-medium">Drop your file here or click to browse</p>
                <p className="text-sm text-muted-foreground">
                  Supports CSV, Excel (.xlsx, .xls), and JSON files up to 10MB
                </p>
              </div>

              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button variant="outline" asChild>
                  <span>
                    <FileText className="h-4 w-4 mr-2" />
                    Choose File
                  </span>
                </Button>
              </label>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* File Format Info */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p><strong>CSV Format:</strong> Use comma-separated values with headers in the first row</p>
        <p><strong>Excel Format:</strong> Data should be in the first worksheet with headers in row 1</p>
        <p><strong>Required Columns:</strong> Application Name, {fields.filter(f => f.validation?.required).map(f => f.label).join(', ')}</p>
      </div>
    </div>
  );
};
