import React, { useCallback, useState, useEffect } from 'react';
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
  Upload,
  Network,
  Server,
  Settings
} from 'lucide-react';

// CrewAI Discovery Flow Integration
import useDiscoveryWebSocket from '../../hooks/useDiscoveryWebSocket';
import { useDiscoveryFlowState } from '../../hooks/useDiscoveryFlowState';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
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
  flow_session_id?: string; // Discovery Flow session ID
}

// Discovery Flow Phases Configuration
const DISCOVERY_FLOW_PHASES = [
  {
    id: 'field_mapping',
    name: 'Field Mapping',
    description: 'Map data fields to standard migration attributes',
    icon: Database,
    crew: 'Field Mapping Crew',
    agents: ['Field Mapping Manager', 'Schema Analysis Expert', 'Attribute Mapping Specialist'],
    color: 'bg-blue-500'
  },
  {
    id: 'data_cleansing',
    name: 'Data Cleansing',
    description: 'Validate and standardize data quality',
    icon: RefreshCw,
    crew: 'Data Cleansing Crew',
    agents: ['Data Quality Manager', 'Data Validation Expert', 'Data Standardization Specialist'],
    color: 'bg-green-500'
  },
  {
    id: 'inventory_building',
    name: 'Inventory Building',
    description: 'Classify assets across multiple domains',
    icon: Server,
    crew: 'Inventory Building Crew',
    agents: ['Inventory Manager', 'Server Classification Expert', 'Application Discovery Expert', 'Device Classification Expert'],
    color: 'bg-purple-500'
  },
  {
    id: 'app_server_dependencies',
    name: 'App-Server Dependencies',
    description: 'Map application hosting relationships',
    icon: Network,
    crew: 'App-Server Dependency Crew',
    agents: ['Dependency Manager', 'Application Topology Expert', 'Infrastructure Relationship Analyst'],
    color: 'bg-orange-500'
  },
  {
    id: 'app_app_dependencies',
    name: 'App-App Dependencies',
    description: 'Analyze application integration patterns',
    icon: Activity,
    crew: 'App-App Dependency Crew',
    agents: ['Integration Manager', 'Application Integration Expert', 'API Dependency Analyst'],
    color: 'bg-red-500'
  },
  {
    id: 'technical_debt',
    name: 'Technical Debt Assessment',
    description: 'Evaluate modernization readiness for 6R strategy',
    icon: Settings,
    crew: 'Technical Debt Crew',
    agents: ['Technical Debt Manager', 'Legacy Technology Analyst', 'Modernization Strategy Expert', 'Risk Assessment Specialist'],
    color: 'bg-indigo-500'
  }
];

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

// Custom hooks for clean API separation with Discovery Flow integration
const useFileUpload = () => {
  const { user, client, engagement } = useAuth();
  const { toast } = useToast();
  const { initializeFlow } = useDiscoveryFlowState();
  
  return useMutation<UploadResponse, Error, { file: File; type: string }>({
    mutationFn: async ({ file, type }) => {
      // Validate authentication context
      if (!user || !client || !engagement) {
        throw new Error('Authentication context required for file upload');
      }

      // Parse file to get data
      const fileData = await parseCSVFile(file);
      
      // Initialize Discovery Flow directly with the data
      const flowResponse = await initializeFlow({
        client_account_id: client.id,
        engagement_id: engagement.id,
        user_id: user.id,
        raw_data: fileData.sample_data,
        metadata: {
          source: 'cmdb_import',
          filename: file.name,
          upload_type: type,
          headers: fileData.headers,
          original_file_size: file.size
        }
      });

      return {
        session_id: flowResponse.session_id,
        flow_id: flowResponse.session_id,
        status: 'flow_initialized',
        message: 'Discovery Flow initialized successfully',
        current_phase: 'initialization'
      };
    },
    onSuccess: (data, variables) => {
      toast({
        title: "🚀 Discovery Flow Initialized",
        description: `File "${variables.file.name}" uploaded and Discovery Flow started with all 6 crews.`,
      });
    },
    onError: (error) => {
      toast({
        title: "Upload Failed",
        description: error.message,
        variant: "destructive"
      });
    }
  });
};

// Enhanced workflow status with Discovery Flow integration
const useWorkflowStatus = (sessionId: string | null) => {
  const { flowState } = useDiscoveryFlowState();
  
  return useQuery({
    queryKey: ['workflow-status', sessionId],
    queryFn: async () => {
      if (!sessionId) return null;
      
      // If we have a Discovery Flow state, use it
      if (flowState?.session_id === sessionId) {
        return {
          session_id: sessionId,
          status: flowState.current_phase === 'completed' ? 'completed' : 'in_progress',
          current_phase: flowState.current_phase,
          progress_percentage: Object.values(flowState.phase_completion || {}).filter(Boolean).length / 6 * 100,
          message: `Discovery Flow: ${flowState.current_phase}`,
          workflow_details: {
            workflow_id: flowState.session_id,
            created_at: new Date().toISOString()
          }
        } as WorkflowStatus;
      }
      
      // Fallback to traditional status check
      try {
        const response = await apiCall(`/api/v1/discovery/flow/${sessionId}/status`);
        return response as WorkflowStatus;
      } catch (error) {
        console.warn('Traditional workflow status failed, this may be a Discovery Flow session');
        return null;
      }
    },
    enabled: !!sessionId,
    refetchInterval: (data) => {
      return data?.status === 'in_progress' ? 5000 : false;
    }
  });
};

// Discovery Flow Phase Card Component
interface PhaseCardProps {
  phase: typeof DISCOVERY_FLOW_PHASES[0];
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  flowState?: any;
}

const PhaseCard: React.FC<PhaseCardProps> = ({ phase, status, progress = 0, flowState }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'in_progress': return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'failed': return <AlertCircle className="h-5 w-5 text-red-600" />;
      default: return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };
  
  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'border-green-200 bg-green-50';
      case 'in_progress': return 'border-blue-200 bg-blue-50';
      case 'failed': return 'border-red-200 bg-red-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const crewStatus = flowState?.crew_status?.[phase.id];
  
  return (
    <div className={`border rounded-lg p-4 ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <phase.icon className="h-5 w-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">{phase.name}</h3>
        </div>
        {getStatusIcon()}
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{phase.description}</p>
      
      {/* Progress Bar */}
      {status === 'in_progress' && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      
      {/* Crew Information */}
      <div className="text-xs text-gray-500">
        <div className="font-medium mb-1">{phase.crew}</div>
        <div className="flex flex-wrap gap-1">
          {phase.agents.map((agent, index) => (
            <span 
              key={index}
              className={`px-2 py-1 rounded-full text-xs ${
                crewStatus?.active_agents?.includes(agent) 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {agent}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

// Upload Area Component
interface UploadAreaProps {
  area: UploadAreaType;
  onDrop: (files: File[], type: string) => void;
  isSelected: boolean;
}

const UploadArea: React.FC<UploadAreaProps> = ({ area, onDrop, isSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onDrop(files, area.id);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onDrop(files, area.id);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200
        ${isDragOver ? 'border-blue-400 bg-blue-50 scale-[1.02]' : 'border-gray-300 hover:border-gray-400'}
        ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''}
      `}
    >
      <input
        type="file"
        multiple
        accept={area.acceptedTypes.join(',')}
        onChange={handleFileSelect}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      
      <div className={`w-12 h-12 mx-auto mb-4 rounded-lg ${area.color} flex items-center justify-center`}>
        <area.icon className="h-6 w-6 text-white" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{area.title}</h3>
      <p className="text-sm text-gray-600 mb-4">{area.description}</p>
      
      <div className="text-xs text-gray-500">
        <p className="mb-2">Accepted formats: {area.acceptedTypes.join(', ')}</p>
        <div className="flex flex-wrap justify-center gap-1">
          {area.examples.map((example, index) => (
            <span key={index} className="bg-gray-100 px-2 py-1 rounded">
              {example}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

// File Analysis Component with Discovery Flow Integration
interface FileAnalysisProps {
  file: UploadedFile;
  onNavigate: (path: string) => void;
}

const FileAnalysis: React.FC<FileAnalysisProps> = ({ file, onNavigate }) => {
  const { data: workflowStatus } = useWorkflowStatus(file.session_id || null);
  const { flowState } = useDiscoveryFlowState();

  const getActualStatus = () => {
    if (file.flow_session_id && flowState?.session_id === file.flow_session_id) {
      return flowState.current_phase === 'completed' ? 'completed' : 'processing';
    }
    return workflowStatus?.status === 'completed' ? 'completed' : 
           workflowStatus?.status === 'failed' ? 'failed' : 
           file.status;
  };

  const getStatusIcon = () => {
    const status = getActualStatus();
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'processing': return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'failed': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default: return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    const status = getActualStatus();
    switch (status) {
      case 'completed': return 'border-green-200 bg-green-50';
      case 'processing': return 'border-blue-200 bg-blue-50';
      case 'failed': return 'border-red-200 bg-red-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getStatusText = () => {
    const status = getActualStatus();
    if (file.flow_session_id && flowState?.session_id === file.flow_session_id) {
      const completedPhases = Object.values(flowState.phase_completion || {}).filter(Boolean).length;
      return `Discovery Flow: Phase ${completedPhases}/6 - ${flowState.current_phase}`;
    }
    
    switch (status) {
      case 'completed': return 'Analysis Complete';
      case 'processing': return workflowStatus?.message || 'Processing with CrewAI agents...';
      case 'failed': return file.error_message || 'Processing failed';
      default: return 'Queued for processing';
    }
  };

  const canNavigateToMapping = () => {
    return getActualStatus() === 'completed' || 
           (flowState?.phase_completion?.field_mapping && flowState.session_id === file.flow_session_id);
  };

  const handleNavigateToMapping = () => {
    if (file.flow_session_id && flowState?.session_id === file.flow_session_id) {
      // Navigate with Discovery Flow state
      onNavigate('/discovery/attribute-mapping');
    } else {
      // Legacy navigation
      onNavigate('/discovery/attribute-mapping');
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <FileSpreadsheet className="h-8 w-8 text-gray-600" />
          <div>
            <h3 className="font-semibold text-gray-900">{file.filename}</h3>
            <p className="text-sm text-gray-600">{file.record_count} records processed</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      {/* Discovery Flow Progress */}
      {file.flow_session_id && flowState?.session_id === file.flow_session_id && (
        <div className="mb-4">
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {DISCOVERY_FLOW_PHASES.map((phase) => {
              const isCompleted = flowState.phase_completion?.[phase.id];
              const isCurrent = flowState.current_phase === phase.id;
              const status = isCompleted ? 'completed' : isCurrent ? 'in_progress' : 'pending';
              
              return (
                <PhaseCard
                  key={phase.id}
                  phase={phase}
                  status={status}
                  progress={isCurrent ? 50 : isCompleted ? 100 : 0}
                  flowState={flowState}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2">
        {canNavigateToMapping() && (
          <Button
            onClick={handleNavigateToMapping}
            className="flex items-center space-x-2"
          >
            <span>View Attribute Mapping</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
        
        {getActualStatus() === 'processing' && (
          <Button variant="outline" disabled className="flex items-center space-x-2">
            <Bot className="h-4 w-4 animate-pulse" />
            <span>CrewAI Agents Active</span>
          </Button>
        )}
      </div>
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
  const { flowState, isLoading: isFlowStateLoading } = useDiscoveryFlowState();
  const { isConnected: isWebSocketConnected } = useDiscoveryWebSocket(flowState?.session_id);
  
  // Handle file drop with Discovery Flow integration
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
        
        // Upload file and initialize Discovery Flow
        const result = await uploadMutation.mutateAsync({ file, type });
        
        // Update with Discovery Flow session ID
        setUploadedFiles(prev => 
          prev.map(f => f.id === tempFile.id ? 
            { 
              ...f, 
              session_id: result.session_id,
              flow_session_id: result.flow_id,
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
                <h1 className="text-3xl font-bold text-gray-900">Data Import & Discovery Flow</h1>
              </div>
              <p className="mt-2 text-gray-600">
                Upload migration data files to initialize the comprehensive CrewAI Discovery Flow with 6 specialized crews
              </p>
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <Brain className="h-6 w-6 text-blue-600" />
                  <div>
                    <p className="text-sm text-blue-800">
                      <strong>Discovery Flow Architecture:</strong> Upload triggers the complete 6-phase CrewAI workflow with manager agents coordinating specialized crews through shared memory and knowledge bases.
                    </p>
                  </div>
                </div>
                {/* WebSocket Status */}
                <div className="flex items-center space-x-2 mt-2">
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                    isWebSocketConnected ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    <Activity className="h-4 w-4" />
                    <span>{isWebSocketConnected ? 'Real-time Monitoring Active' : 'Connecting to Monitoring...'}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Upload Success Toast */}
            {showUploadSuccess && (
              <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                <CheckCircle className="h-5 w-5" />
                <span>Discovery Flow Initialized! All 6 crews activated...</span>
              </div>
            )}

            {/* Enhanced Agent Orchestration Panel */}
            {flowState?.session_id && (
              <div className="mb-8">
                <EnhancedAgentOrchestrationPanel
                  sessionId={flowState.session_id}
                  flowState={flowState}
                />
              </div>
            )}

            {/* Upload Areas */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Data Files</h2>
              <p className="text-sm text-gray-600 mb-6">
                Choose the appropriate category for your data files. Upload will initialize the complete Discovery Flow with all 6 specialized crews.
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

            {/* Discovery Flow Progress */}
            {uploadedFiles.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Discovery Flow Progress</h2>
                  {uploadMutation.isPending && (
                    <div className="flex items-center space-x-2 text-blue-600">
                      <Bot className="h-5 w-5 animate-pulse" />
                      <span className="text-sm font-medium">Discovery Flow Initializing</span>
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
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Discovery Flow Overview</h2>
                <div className="prose max-w-none text-gray-600">
                  <p>Welcome to the comprehensive CrewAI Discovery Flow. Here's how the 6-phase process works:</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                    {DISCOVERY_FLOW_PHASES.map((phase, index) => (
                      <div key={phase.id} className="border rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className={`w-8 h-8 rounded-full ${phase.color} flex items-center justify-center text-white font-bold`}>
                            {index + 1}
                          </div>
                          <h3 className="font-semibold text-gray-900">{phase.name}</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{phase.description}</p>
                        <div className="text-xs text-gray-500">
                          <div className="font-medium">{phase.crew}</div>
                          <div>{phase.agents.length} specialized agents</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 flex items-center space-x-3 bg-blue-50 p-3 rounded-lg">
                    <Lightbulb className="h-5 w-5 text-blue-600" />
                    <p className="text-sm text-blue-800">
                      <strong>AI-Powered Intelligence:</strong> Each crew uses manager agents for coordination, shared memory for learning, and collaborative decision-making for superior migration analysis.
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

