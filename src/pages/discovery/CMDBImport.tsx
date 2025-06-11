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
  FileSpreadsheet
} from 'lucide-react';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { Button } from '@/components/ui/button';
import { UploadArea } from './components/CMDBImport/UploadArea';
import { FileAnalysis } from './components/CMDBImport/FileAnalysis';

// Hooks
import { useFileUpload, type UploadedFile } from './hooks/useCMDBImport';

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

const CMDBImport: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedUploadType, setSelectedUploadType] = useState<string>('');
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  // Use the useFileUpload hook
  const { mutate: uploadFiles, isPending: isUploading } = useFileUpload();

  // Get uploaded files from the query cache
  const { data: uploadedFiles = [] } = useQuery<UploadedFile[]>({
    queryKey: ['uploadedFiles'],
    initialData: []
  });

  // Handle file drop
  const handleDrop = useCallback((acceptedFiles: File[], type: string) => {
    setShowUploadSuccess(true);
    setTimeout(() => setShowUploadSuccess(false), 3000);
    
    // Generate unique IDs for each file
    const filesWithIds = acceptedFiles.map(file => ({
      file,
      type,
      id: uuidv4()
    }));
    
    // Trigger the file upload mutation
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
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden ml-64">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
            <div className="flex h-full">
              {/* Main Content Area */}
              <div className="flex-1 overflow-y-auto">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-5xl">
                  {/* Context Breadcrumbs */}
                  <div className="mb-6">
                    <ContextBreadcrumbs />
                  </div>
                  
                  <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Intelligent Data Analysis</h1>
                    <p className="mt-2 text-gray-600">
                      Upload any data file and let our AI crew intelligently determine its type, value, and processing requirements
                    </p>
                    <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Brain className="h-6 w-6 text-blue-600" />
                        <div>
                          <p className="text-sm text-blue-800">
                            <strong>Smart AI Analysis:</strong> Our intelligent agents analyze any uploaded data to determine actual content type, assess quality and relevance, then recommend the optimal processing workflow for your migration journey.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Upload Success Toast */}
                  {showUploadSuccess && (
                    <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                      <CheckCircle className="h-5 w-5" />
                      <span>File uploaded successfully! AI analysis starting...</span>
                    </div>
                  )}

                  {/* Upload Areas */}
                  <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Your Data (AI Will Determine Actual Type)</h2>
                    <p className="text-sm text-gray-600 mb-6">
                      Choose the category that best represents what you <em>intended</em> to upload. Our AI crew will analyze the actual content and determine its true type and value.
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
                    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                      <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold text-gray-900">AI Crew Analysis</h2>
                        {isUploading && (
                          <div className="flex items-center space-x-2 text-blue-600">
                            <Bot className="h-5 w-5 animate-pulse" />
                            <span className="text-sm font-medium">Agentic crew active</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="space-y-6">
                        {uploadedFiles.map((fileUpload, index) => (
                          <FileAnalysis
                            key={fileUpload.id || index}
                            file={fileUpload}
                            onNavigate={handleNavigate}
                            onRetry={() => {
                              // Implement retry logic if needed
                              console.log('Retry file:', fileUpload.file.name);
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Getting Started */}
                  {uploadedFiles.length === 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                      <h2 className="text-xl font-semibold text-gray-900 mb-4">How Intelligent Analysis Works</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h3 className="font-medium text-gray-900 mb-2">🤖 AI-Powered Content Detection</h3>
                          <ul className="space-y-1 text-sm text-gray-600">
                            <li>• AI crew analyzes actual file content and structure</li>
                            <li>• Determines true data type regardless of upload category</li>
                            <li>• Assesses data quality and migration relevance</li>
                            <li>• Scores information value for your migration project</li>
                          </ul>
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900 mb-2">📊 Intelligent Recommendations</h3>
                          <ul className="space-y-1 text-sm text-gray-600">
                            <li>• Tailored processing workflow based on actual content</li>
                            <li>• Context-aware next steps for optimal migration planning</li>
                            <li>• Quality-based confidence scoring and issue identification</li>
                            <li>• Application-focused insights from any data type</li>
                          </ul>
                        </div>
                      </div>
                      
                      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Lightbulb className="h-5 w-5 text-blue-600" />
                          <div>
                            <p className="text-sm text-blue-800">
                              <strong>Pro Tip:</strong> Don't worry about choosing the "perfect" category - our AI crew is designed to understand your data regardless of how you categorize it. Just pick the closest match and let the intelligence do the rest!
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Agent Interaction Sidebar */}
              <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
                <div className="p-4 space-y-4">
                  {/* Agent Clarification Panel */}
                  <AgentClarificationPanel 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isUploading}
                    onQuestionAnswered={(questionId, response) => {
                      console.log('Question answered:', questionId, response);
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />

                  {/* Data Classification Display */}
                  <DataClassificationDisplay 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isUploading}
                    onClassificationUpdate={(itemId, newClassification) => {
                      console.log('Classification updated:', itemId, newClassification);
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />

                  {/* Agent Insights Section */}
                  <AgentInsightsSection 
                    pageContext="data-import"
                    refreshTrigger={agentRefreshTrigger}
                    isProcessing={isUploading}
                    onInsightAction={(insightId, action) => {
                      console.log('Insight action:', insightId, action);
                      setAgentRefreshTrigger(prev => prev + 1);
                    }}
                  />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default CMDBImport;
