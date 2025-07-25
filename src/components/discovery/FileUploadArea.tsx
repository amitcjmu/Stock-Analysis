import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, FileText, Database } from 'lucide-react';

interface FileUploadAreaProps {
  onFilesUploaded: (files: File[]) => void;
  isAnalyzing: boolean;
}

const FileUploadArea: React.FC<FileUploadAreaProps> = ({ onFilesUploaded, isAnalyzing }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFilesUploaded,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json']
    },
    multiple: true,
    disabled: isAnalyzing
  });

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload CMDB Files</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : isAnalyzing
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`h-12 w-12 mx-auto mb-4 ${isAnalyzing ? 'text-gray-300' : 'text-gray-400'}`} />
        {isDragActive ? (
          <p className="text-lg text-blue-600">Drop the files here...</p>
        ) : isAnalyzing ? (
          <p className="text-lg text-gray-500">Analysis in progress...</p>
        ) : (
          <div>
            <p className="text-lg text-gray-600 mb-2">
              Drag & drop CMDB files here, or click to select
            </p>
            <p className="text-sm text-gray-500">
              Supports CSV, Excel (.xlsx, .xls), and JSON formats
            </p>
          </div>
        )}
      </div>

      {/* Supported Formats */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <FileSpreadsheet className="h-4 w-4" />
          <span>CSV Files</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <FileSpreadsheet className="h-4 w-4" />
          <span>Excel Files</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <FileText className="h-4 w-4" />
          <span>JSON Files</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Database className="h-4 w-4" />
          <span>CMDB Exports</span>
        </div>
      </div>
    </div>
  );
};

export default FileUploadArea;
