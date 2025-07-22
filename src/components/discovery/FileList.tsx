import React from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  X, 
  Loader, 
  Eye, 
  Edit3, 
  Brain,
  FileText,
  FileSpreadsheet,
  Download,
  Clock,
  File,
  Database
} from 'lucide-react';

export interface AnalysisResult {
  status: 'analyzing' | 'completed' | 'error';
  dataQuality: {
    score: number;
    issues: string[];
    recommendations: string[];
  };
  coverage: {
    applications: number;
    servers: number;
    databases: number;
    dependencies: number;
  };
  missingFields: string[];
  requiredProcessing: string[];
  readyForImport: boolean;
  rawData?: unknown[];
}

export interface FileUpload {
  file: File;
  id: string;
  status: 'uploaded' | 'analyzing' | 'processed' | 'error';
  analysis?: AnalysisResult;
  preview?: unknown[];
  editableData?: unknown[];
}

interface FileListProps {
  files: FileUpload[];
  onAnalyzeFile: (file: FileUpload) => void;
  onViewAnalysis: (file: FileUpload) => void;
  onEditData: (file: FileUpload) => void;
}

const FileList: React.FC<FileListProps> = ({ 
  files, 
  onAnalyzeFile, 
  onViewAnalysis, 
  onEditData 
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <FileText className="h-5 w-5 text-gray-500" />;
      case 'analyzing':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <X className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Uploaded Files</h2>
      
      <div className="space-y-4">
        {files.map((fileUpload) => (
          <div key={fileUpload.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {getStatusIcon(fileUpload.status)}
                <div>
                  <h3 className="font-medium text-gray-900">{fileUpload.file.name}</h3>
                  <p className="text-sm text-gray-500">
                    {(fileUpload.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {fileUpload.status === 'processed' && (
                  <>
                    <button
                      onClick={() => onViewAnalysis(fileUpload)}
                      className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      <Eye className="h-4 w-4 inline mr-1" />
                      View Analysis
                    </button>
                    <button
                      onClick={() => onEditData(fileUpload)}
                      className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors"
                    >
                      <Edit3 className="h-4 w-4 inline mr-1" />
                      Edit Data
                    </button>
                  </>
                )}
                {fileUpload.status === 'uploaded' && (
                  <button
                    onClick={() => onAnalyzeFile(fileUpload)}
                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
                  >
                    <Brain className="h-4 w-4 inline mr-1" />
                    Analyze
                  </button>
                )}
              </div>
            </div>

            {fileUpload.analysis && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getQualityColor(fileUpload.analysis.dataQuality.score)}`}>
                    Data Quality: {fileUpload.analysis.dataQuality.score}%
                  </div>
                </div>
                <div className="text-center">
                  <span className="text-sm text-gray-600">Applications: </span>
                  <span className="font-medium">{fileUpload.analysis.coverage.applications}</span>
                </div>
                <div className="text-center">
                  <span className="text-sm text-gray-600">Servers: </span>
                  <span className="font-medium">{fileUpload.analysis.coverage.servers}</span>
                </div>
                <div className="text-center">
                  <span className="text-sm text-gray-600">Ready: </span>
                  {fileUpload.analysis.readyForImport ? (
                    <CheckCircle className="h-4 w-4 text-green-500 inline" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-500 inline" />
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileList; 