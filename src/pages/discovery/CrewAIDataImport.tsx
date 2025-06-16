import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useQuery, useQueryClient } from '@tanstack/react-query';
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
  Workflow
} from 'lucide-react';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentFeedbackPanel from './components/CMDBImport/AgentFeedbackPanel';
import { Button } from '@/components/ui/button';
import { UploadArea } from './components/CMDBImport/UploadArea';
import { FileAnalysis } from './components/CMDBImport/FileAnalysis';

// Hooks
import { useFileUpload, useDiscoveryFlowStatus, type UploadedFile } from './hooks/useCMDBImport';

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

// Upload areas configuration for CrewAI flow
const uploadAreas: UploadAreaType[] = [
  {
    id: 'cmdb',
    title: 'CMDB Data',
    description: 'Configuration Management Database exports processed by specialized CrewAI agents',
    icon: Database,
    color: 'bg-blue-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['ServiceNow exports', 'BMC Remedy data', 'Custom CMDB files']
  },
  {
    id: 'app-scan',
    title: 'Application Scan Data',
    description: 'Application discovery data analyzed by Asset Classification Expert agents',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['Appdynamics exports', 'Dynatrace data', 'New Relic reports']
  },
  {
    id: 'migration-discovery',
    title: 'Migration Discovery Data',
    description: 'Migration assessments processed by Field Mapping and Quality Assessment crews',
    icon: Activity,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['AWS Migration Hub', 'Azure Migrate data', 'Migration assessments']
  },
  {
    id: 'documentation',
    title: 'Documentation',
    description: 'Technical documentation analyzed by Pattern Recognition agents',
    icon: FileText,
    color: 'bg-orange-500',
    acceptedTypes: ['.pdf', '.doc', '.docx', '.md'],
    examples: ['Architecture docs', 'Runbooks', 'Technical specifications']
  },
  {
    id: 'monitoring',
    title: 'Application Monitoring Data',
    description: 'Performance metrics processed by Data Quality and Consistency crews',
    icon: Activity,
    color: 'bg-red-500',
    acceptedTypes: ['.csv', '.json', '.log'],
    examples: ['Splunk exports', 'Prometheus data', 'CloudWatch logs']
  }
];

const CrewAIDataImport: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedUploadType, setSelectedUploadType] = useState<string>('');
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [workflowStarted, setWorkflowStarted] = useState(false);

  // Use the useFileUpload hook
  const { mutate: uploadFiles, isPending: isUploading } = useFileUpload();

  // Get uploaded files from the query cache
  const { data: uploadedFiles = [] } = useQuery<UploadedFile[]>({
    queryKey: ['uploadedFiles'],
    queryFn: () => {
      return queryClient.getQueryData<UploadedFile[]>(['uploadedFiles']) || [];
    },
    initialData: []
  });

  // Get discovery flow status for the first uploaded file
  const firstFile = uploadedFiles[0];
  const { data: statusData } = useDiscoveryFlowStatus(firstFile?.sessionId || null);

  // Handle file drop - triggers CrewAI workflow
  const handleDrop = useCallback((acceptedFiles: File[], type: string) => {
    setShowUploadSuccess(true);
    setWorkflowStarted(true);
    setTimeout(() => setShowUploadSuccess(false), 3000);
    
    // Generate unique IDs for each file
    const filesWithIds = acceptedFiles.map(file => ({
      file,
      type,
      id: uuidv4()
    }));
    
    // Trigger the file upload mutation which will start the CrewAI workflow
    uploadFiles(filesWithIds);
  }, [uploadFiles]);

  // Handle file upload click
  const handleUploadClick = (type: string) => {
    setSelectedUploadType(type);
  };

  // Handle navigation to a route
  const handleNavigate = (path: string, state?: any) => {
    navigate(path, { state });
  };

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
                <h1 className="text-3xl font-bold text-gray-900">CrewAI Discovery Flow</h1>
                <div className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                  Redesigned
                </div>
              </div>
              <p className="mt-2 text-gray-600">
                Upload data files and watch specialized CrewAI agents work collaboratively to process, classify, and analyze your migration data
              </p>
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Brain className="h-6 w-6 text-blue-600" />
                  <div>
                    <p className="text-sm text-blue-800">
                      <strong>CrewAI Orchestration:</strong> Five specialized crews with collaborative agents work in sequence: Data Ingestion → Asset Analysis → Field Mapping → Quality Assessment → Database Integration
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Upload Success Toast */}
            {showUploadSuccess && (
              <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                <CheckCircle className="h-5 w-5" />
                <span>File uploaded! CrewAI agents starting...</span>
              </div>
            )}

            {/* Upload Areas */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Data for CrewAI Processing</h2>
              <p className="text-sm text-gray-600 mb-6">
                Upload any migration-related data file. Our specialized CrewAI agents will collaborate to analyze, classify, and process the data automatically.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {uploadAreas.map((area) => (
                  <UploadArea
                    key={area.id}
                    area={area}
                    onDrop={handleDrop}
                    isSelected={selectedUploadType === area.id}
                  />
                ))}
              </div>
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="space-y-6">
                {uploadedFiles.map((uploadedFile) => (
                  <FileAnalysis
                    key={uploadedFile.id}
                    file={uploadedFile.file}
                    type={uploadedFile.type}
                    onNavigate={handleNavigate}
                    showCrewAIWorkflow={true}
                  />
                ))}
              </div>
            )}

            {/* Agent Feedback Panel - Shows when workflow starts */}
            {(workflowStarted || uploadedFiles.length > 0) && uploadedFiles.length > 0 && (
              <div className="mt-8">
                <AgentFeedbackPanel 
                  sessionId={uploadedFiles[0].sessionId || "unknown-session"}
                  statusData={statusData}
                />
              </div>
            )}

            {/* Getting Started Guide */}
            {uploadedFiles.length === 0 && !workflowStarted && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">CrewAI Discovery Flow Guide</h2>
                <div className="prose max-w-none text-gray-600">
                  <p>
                    This redesigned Discovery Flow uses CrewAI's "Flows orchestrating multiple Crews" pattern for High Complexity + High Precision use cases:
                  </p>
                  <ol>
                    <li>
                      <strong>Upload Data:</strong> Upload any migration data file. The system automatically triggers the CrewAI Discovery Flow.
                    </li>
                    <li>
                      <strong>Watch Crews Work:</strong> Five specialized crews execute in sequence with real-time progress tracking:
                      <ul>
                        <li><strong>Data Ingestion Crew:</strong> Data Validation Specialist + Format Standardizer</li>
                        <li><strong>Asset Analysis Crew:</strong> Asset Classification Expert + Dependency Analyzer</li>
                        <li><strong>Field Mapping Crew:</strong> Field Mapping Specialist + Pattern Recognition Agent</li>
                        <li><strong>Quality Assessment Crew:</strong> Data Quality Analyst + Consistency Validator</li>
                        <li><strong>Database Integration:</strong> Structured persistence with validation</li>
                      </ul>
                    </li>
                    <li>
                      <strong>Agent Orchestration Panel:</strong> Monitor crew progress, agent activities, and results in real-time.
                    </li>
                    <li>
                      <strong>View Results:</strong> Access processed assets in the Inventory or proceed to Attribute Mapping for refinement.
                    </li>
                  </ol>
                  <div className="mt-6 flex items-center space-x-3 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200">
                    <Workflow className="h-6 w-6 text-blue-600" />
                    <div>
                      <p className="text-sm text-blue-800">
                        <strong>CrewAI Architecture:</strong> This implementation follows CrewAI best practices with @start/@listen decorators, native state persistence, and collaborative agent workflows designed for complex migration analysis.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center space-x-3 bg-green-50 p-3 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <p className="text-sm text-green-800">
                      <strong>Expected Results:</strong> Processed assets are automatically saved to the database with full metadata, ready for 6R treatment analysis in subsequent flows.
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

export default CrewAIDataImport; 