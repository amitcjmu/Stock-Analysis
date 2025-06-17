import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Brain, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  ArrowRight, 
  Zap, 
  Users, 
  Eye, 
  Loader2, 
  Clock, 
  Bot, 
  FileCheck, 
  AlertCircle, 
  Lightbulb,
  ExternalLink,
  Database,
  Monitor,
  Activity,
  FileText,
  FileSpreadsheet,
  Workflow,
  Upload
} from 'lucide-react';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

// Types
interface UploadAreaType {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  acceptedTypes: string[];
  examples: string[];
}

interface FileUploadData {
  headers: string[];
  sample_data: Record<string, any>[];
  filename: string;
}

interface UploadResponse {
  session_id: string;
  status: string;
  message: string;
  flow_id?: string;
  current_phase?: string;
}

interface WorkflowStatus {
  session_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'in_progress';
  current_phase: string;
  progress_percentage: number;
  message: string;
  file_processed?: string;
  records_processed?: number;
  completed_at?: string;
  workflow_details?: {
    workflow_id: string;
    created_at: string;
  };
}

interface UploadedFile {
  id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  session_id?: string;
  record_count: number;
  workflow_status?: WorkflowStatus;
  error_message?: string;
}

// Styles
const styles = `
  @keyframes slide-in-right {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .animate-slide-in-right { animation: slide-in-right 0.3s ease-out; }
  .animate-fade-in { animation: fade-in 0.5s ease-out; }
`;

// Upload areas configuration
const uploadAreas: UploadAreaType[] = [
  {
    id: 'cmdb',
    title: 'CMDB Data',
    description: 'Configuration Management Database exports with asset information',
    icon: Database,
    color: 'bg-blue-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files']
  },
  {
    id: 'app-scan',
    title: 'Application Scan Data',
    description: 'Application discovery and dependency scan results',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['Appdynamics exports', 'Dynatrace data', 'New Relic reports']
  },
  {
    id: 'migration-discovery',
    title: 'Migration Discovery Data',
    description: 'Migration readiness assessments and infrastructure details',
    icon: Activity,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['AWS Migration Hub', 'Azure Migrate data', 'Migration assessments']
  },
  {
    id: 'documentation',
    title: 'Documentation',
    description: 'Technical documentation, architecture diagrams, and runbooks',
    icon: FileText,
    color: 'bg-orange-500',
    acceptedTypes: ['.pdf', '.doc', '.docx', '.md'],
    examples: ['Architecture docs', 'Runbooks', 'Technical specifications']
  },
  {
    id: 'monitoring',
    title: 'Application Monitoring Data',
    description: 'Performance metrics, logs, and monitoring tool exports',
    icon: Activity,
    color: 'bg-red-500',
    acceptedTypes: ['.csv', '.json', '.log'],
    examples: ['Splunk exports', 'Prometheus data', 'CloudWatch logs']
  }
];

// Helper function to parse CSV file
const parseCSVFile = (file: File): Promise<FileUploadData> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length === 0) {
          reject(new Error('File is empty'));
          return;
        }
        
        // Parse headers
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        
        // Parse data rows (first 10 for sample)
        const sample_data: Record<string, any>[] = [];
        for (let i = 1; i < Math.min(lines.length, 11); i++) {
          const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
          const row: Record<string, any> = {};
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          sample_data.push(row);
        }
        
        resolve({ 
          headers, 
          sample_data, 
          filename: file.name 
        });
      } catch (error) {
        reject(new Error('Failed to parse CSV file'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};

// Custom hooks for clean API separation
const useFileUpload = () => {
  const { user, client, engagement } = useAuth();
  
  return useMutation<UploadResponse, Error, { file: File; type: string }>({
    mutationFn: async ({ file, type }) => {
      // Validate authentication context
      if (!user || !client || !engagement) {
        throw new Error('Authentication context required (user, client, engagement)');
      }
      
      // Parse file data
      const fileData = await parseCSVFile(file);
      
      // Call clean upload endpoint - NO SESSION ID REQUIRED
      const response = await apiCall('/api/v1/data-import/data-imports', {
        method: 'POST',
        headers: {
          'X-Client-Account-ID': client.id,
          'X-Engagement-ID': engagement.id,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...fileData,
          upload_type: type,
          user_id: user.id
        })
      }) as UploadResponse;
      
      return response;
    }
  });
};

const useWorkflowStatus = (sessionId: string | null) => {
  const { user, client, engagement } = useAuth();
  
  return useQuery<WorkflowStatus, Error>({
    queryKey: ['workflowStatus', sessionId],
    queryFn: async () => {
      if (!sessionId || !user || !client || !engagement) {
        throw new Error('Session ID and authentication context required');
      }
      
      // Call clean status endpoint - WITH SESSION ID
      const response = await apiCall(`/api/v1/data-import/data-imports/${sessionId}/status`, {
        method: 'GET',
        headers: {
          'X-Client-Account-ID': client.id,
          'X-Engagement-ID': engagement.id,
          'Content-Type': 'application/json'
        }
      }) as WorkflowStatus;
      
      return response;
    },
    enabled: !!sessionId && !!user && !!client && !!engagement,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling when workflow is complete
      const shouldStopPolling = data?.status === 'completed' || 
                              data?.status === 'failed';
      
      // Poll every 3 seconds if still running
      return shouldStopPolling ? false : 3000;
    },
    retry: (failureCount, error) => {
      // Only retry on network errors, not authentication errors
      return failureCount < 3 && !error.message.includes('authentication');
    }
  });
};

// Upload Area Component
interface UploadAreaProps {
  area: UploadAreaType;
  onDrop: (files: File[], type: string) => void;
  isSelected: boolean;
}

const UploadArea: React.FC<UploadAreaProps> = ({ area, onDrop, isSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onDrop(files, area.id);
    }
  }, [onDrop, area.id]);
  
  const handleClick = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = area.acceptedTypes.join(',');
    input.multiple = true;
    input.onchange = (e) => {
      const files = Array.from((e.target as HTMLInputElement).files || []);
      if (files.length > 0) {
        onDrop(files, area.id);
      }
    };
    input.click();
  }, [onDrop, area.id]);
  
  const IconComponent = area.icon;
  
  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200
        ${isDragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg ${area.color} mb-4`}>
        <IconComponent className="h-6 w-6 text-white" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{area.title}</h3>
      <p className="text-sm text-gray-600 mb-4">{area.description}</p>
      
      <div className="space-y-2">
        <p className="text-xs text-gray-500">
          Supported: {area.acceptedTypes.join(', ')}
        </p>
        <div className="text-xs text-gray-400">
          {area.examples.map((example, index) => (
            <div key={index}>{example}</div>
          ))}
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-center text-sm text-blue-600">
        <Upload className="h-4 w-4 mr-2" />
        Click or drag files here
      </div>
    </div>
  );
};

// File Analysis Component
interface FileAnalysisProps {
  file: UploadedFile;
  onNavigate: (path: string) => void;
}

const FileAnalysis: React.FC<FileAnalysisProps> = ({ file, onNavigate }) => {
  const { data: status, error: statusError, isLoading } = useWorkflowStatus(file.session_id || null);
  
  // Derive actual status from workflow status if available
  const getActualStatus = () => {
    if (status) {
      // Use backend workflow status as source of truth
      switch (status.status) {
        case 'running':
        case 'in_progress':
          return 'processing';
        case 'completed':
          return 'completed';
        case 'failed':
          return 'failed';
        default:
          return file.status;
      }
    }
    return file.status;
  };
  
  const actualStatus = getActualStatus();
  
  const getStatusIcon = () => {
    switch (actualStatus) {
      case 'uploading':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processing':
        return <Bot className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };
  
  const getStatusColor = () => {
    switch (actualStatus) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'processing':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };
  
  const getStatusText = () => {
    if (statusError) {
      return "Unable to check status";
    }
    
    if (isLoading && file.session_id) {
      return "Checking status...";
    }
    
    if (status) {
      return status.message || `Processing: ${status.current_phase}`;
    }
    
    switch (actualStatus) {
      case 'uploading':
        return 'Uploading file...';
      case 'processing':
        return 'Processing data...';
      case 'completed':
        return 'Processing completed successfully';
      case 'failed':
        return 'Processing failed';
      default:
        return 'Waiting to process';
    }
  };
  
  return (
    <div className={`border rounded-lg p-6 ${getStatusColor()}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{file.filename}</h3>
            <p className="text-sm text-gray-600">
              {status?.records_processed || file.record_count} records
              {file.session_id && (
                <span className="ml-2 text-xs text-gray-400">
                  Session: {file.session_id.substring(0, 8)}...
                </span>
              )}
            </p>
          </div>
        </div>
        
        {status && (
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">
              {status.progress_percentage}% Complete
            </div>
            <div className="text-sm text-gray-600 capitalize">
              {status.current_phase?.replace(/_/g, ' ')}
            </div>
          </div>
        )}
      </div>
      
      {status && actualStatus === 'processing' && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{status.progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${status.progress_percentage}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">{getStatusText()}</p>
        </div>
      )}
      
      {!status && actualStatus === 'processing' && file.session_id && (
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse w-1/3"></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {isLoading ? "Checking workflow status..." : "Processing started..."}
          </p>
        </div>
      )}
      
      {actualStatus === 'completed' && (
        <div className="mb-4">
          <div className="flex items-center space-x-2 text-green-600 mb-2">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Processing Complete</span>
          </div>
          <p className="text-sm text-gray-600">{getStatusText()}</p>
          <div className="flex space-x-3 mt-4">
            <Button
              onClick={() => onNavigate('/discovery/inventory')}
              className="flex items-center space-x-2"
            >
              <Eye className="h-4 w-4" />
              <span>View Inventory</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => onNavigate('/discovery/attribute-mapping')}
              className="flex items-center space-x-2"
            >
              <ArrowRight className="h-4 w-4" />
              <span>Attribute Mapping</span>
            </Button>
          </div>
        </div>
      )}
      
      {(file.error_message || (actualStatus === 'failed' && status?.message)) && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2 text-red-600 mb-1">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Processing Failed</span>
          </div>
          <p className="text-sm text-red-600">
            {file.error_message || status?.message || "Unknown error occurred"}
          </p>
        </div>
      )}
      
      {statusError && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center space-x-2 text-yellow-600 mb-1">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">Status Check Failed</span>
          </div>
          <p className="text-sm text-yellow-600">
            Unable to check workflow status. The process may still be running.
          </p>
        </div>
      )}
    </div>
  );
};

// Main Component
const CMDBImport: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  
  const uploadMutation = useFileUpload();
  
  // Handle file drop
  const handleDrop = useCallback(async (files: File[], type: string) => {
    setShowUploadSuccess(true);
    setTimeout(() => setShowUploadSuccess(false), 3000);
    
    for (const file of files) {
      // Create optimistic file entry
      const tempFile: UploadedFile = {
        id: `temp-${Date.now()}-${Math.random()}`,
        filename: file.name,
        status: 'uploading',
        record_count: 0
      };
      
      setUploadedFiles(prev => [...prev, tempFile]);
      
      try {
        // Parse file to get record count
        const fileData = await parseCSVFile(file);
        
        // Update with actual record count
        setUploadedFiles(prev => 
          prev.map(f => f.id === tempFile.id ? 
            { ...f, record_count: fileData.sample_data.length, status: 'processing' } : f
          )
        );
        
        // Upload file
        const result = await uploadMutation.mutateAsync({ file, type });
        
        // Update with backend session ID
        setUploadedFiles(prev => 
          prev.map(f => f.id === tempFile.id ? 
            { 
              ...f, 
              session_id: result.session_id,
              status: 'processing'
            } : f
          )
        );
        
      } catch (error) {
        console.error('Upload failed:', error);
        setUploadedFiles(prev => 
          prev.map(f => f.id === tempFile.id ? 
            { 
              ...f, 
              status: 'failed',
              error_message: (error as Error).message
            } : f
          )
        );
      }
    }
  }, [uploadMutation]);
  
  // Handle navigation
  const handleNavigate = useCallback((path: string) => {
    navigate(path);
  }, [navigate]);
  
  return (
    <>
      <style>{styles}</style>
      <div className="flex min-h-screen bg-gray-50">
        {/* Sidebar */}
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-6xl">
            {/* Context Breadcrumbs */}
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Workflow className="h-8 w-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Data Import & Analysis</h1>
              </div>
              <p className="mt-2 text-gray-600">
                Upload migration data files for intelligent analysis by our CrewAI-powered processing engine
              </p>
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Brain className="h-6 w-6 text-blue-600" />
                  <div>
                    <p className="text-sm text-blue-800">
                      <strong>CrewAI Processing:</strong> Specialized agent crews automatically process your data through field mapping, quality assessment, asset classification, and dependency analysis workflows.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Upload Success Toast */}
            {showUploadSuccess && (
              <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                <CheckCircle className="h-5 w-5" />
                <span>Files uploaded! Processing started...</span>
              </div>
            )}

            {/* Upload Areas */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Data Files</h2>
              <p className="text-sm text-gray-600 mb-6">
                Choose the appropriate category for your data files. Our AI agents will automatically detect and process the content.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {uploadAreas.map((area) => (
                  <UploadArea
                    key={area.id}
                    area={area}
                    onDrop={handleDrop}
                    isSelected={false}
                  />
                ))}
              </div>
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Processing Status</h2>
                  {uploadMutation.isPending && (
                    <div className="flex items-center space-x-2 text-blue-600">
                      <Bot className="h-5 w-5 animate-pulse" />
                      <span className="text-sm font-medium">CrewAI agents active</span>
                    </div>
                  )}
                </div>
                
                <div className="space-y-6">
                  {uploadedFiles.map((file) => (
                    <FileAnalysis
                      key={file.id}
                      file={file}
                      onNavigate={handleNavigate}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Getting Started Guide */}
            {uploadedFiles.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Getting Started</h2>
                <div className="prose max-w-none text-gray-600">
                  <p>Welcome to the Data Import & Analysis module. Here's how it works:</p>
                  <ol>
                    <li><strong>Upload Files:</strong> Drag and drop or click to upload CMDB exports, application scans, or migration data files.</li>
                    <li><strong>Automatic Processing:</strong> CrewAI agents automatically analyze file structure, validate data quality, and classify assets.</li>
                    <li><strong>Real-time Progress:</strong> Watch as specialized crews process your data through multiple analysis phases.</li>
                    <li><strong>Review Results:</strong> Access processed assets in the Inventory or proceed to Attribute Mapping for refinement.</li>
                  </ol>
                  
                  <div className="mt-6 flex items-center space-x-3 bg-blue-50 p-3 rounded-lg">
                    <Lightbulb className="h-5 w-5 text-blue-600" />
                    <p className="text-sm text-blue-800">
                      <strong>Tip:</strong> The system automatically detects file types and content, so don't worry about perfect categorization.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default CMDBImport;
