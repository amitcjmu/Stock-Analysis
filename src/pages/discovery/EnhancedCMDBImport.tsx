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
  Settings,
  Target,
  MessageSquare,
  Network,
  TrendingUp,
  Shield,
  Layers
} from 'lucide-react';

// Components
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

// Enhanced Phase 5 Components
import CrewStatusCard from '../../components/discovery/CrewStatusCard';
import MemoryKnowledgePanel from '../../components/discovery/MemoryKnowledgePanel';
import PlanVisualization from '../../components/discovery/PlanVisualization';
import AgentCommunicationPanel from '../../components/discovery/AgentCommunicationPanel';

// Legacy Components
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

interface FlowStatus {
  flow_id: string;
  status: 'initializing' | 'running' | 'completed' | 'failed';
  current_phase: string;
  progress: number;
  started_at: string;
  crews: Array<{
    name: string;
    status: string;
    progress: number;
  }>;
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
  
  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
    50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
  }
  
  .animate-slide-in-right { animation: slide-in-right 0.3s ease-out; }
  .animate-fade-in { animation: fade-in 0.5s ease-out; }
  .animate-pulse-glow { animation: pulse-glow 2s infinite; }
`;

// Upload areas configuration with enhanced intelligence
const uploadAreas: UploadAreaType[] = [
  {
    id: 'intelligent-discovery',
    title: 'Intelligent Data Discovery',
    description: 'Upload any data file - our AI crew will intelligently determine its type and value',
    icon: Brain,
    color: 'bg-gradient-to-r from-blue-500 to-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json', '.xml', '.pdf', '.doc', '.log'],
    examples: ['Any CMDB export', 'Migration data', 'Documentation', 'Monitoring files']
  },
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
    title: 'Application Discovery',
    description: 'Application discovery and dependency scan results',
    icon: Monitor,
    color: 'bg-green-500',
    acceptedTypes: ['.csv', '.json', '.xml'],
    examples: ['AppDynamics exports', 'Dynatrace data', 'New Relic reports']
  },
  {
    id: 'migration-assessment',
    title: 'Migration Assessments',
    description: 'Migration readiness assessments and infrastructure details',
    icon: Target,
    color: 'bg-purple-500',
    acceptedTypes: ['.csv', '.xlsx', '.json'],
    examples: ['AWS Migration Hub', 'Azure Migrate data', 'Migration assessments']
  }
];

const EnhancedCMDBImport: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedUploadType, setSelectedUploadType] = useState<string>('');
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [currentFlowId, setCurrentFlowId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('upload');
  
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

  // Mock flow status - in real implementation this would come from an API
  const [flowStatus, setFlowStatus] = useState<FlowStatus | null>(null);

  // Handle file drop with enhanced processing
  const handleDrop = useCallback((acceptedFiles: File[], type: string) => {
    setShowUploadSuccess(true);
    setTimeout(() => setShowUploadSuccess(false), 3000);
    
    // Generate unique flow ID and file IDs
    const flowId = uuidv4();
    setCurrentFlowId(flowId);
    
    const filesWithIds = acceptedFiles.map(file => ({
      file,
      type,
      id: uuidv4(),
      flowId
    }));
    
    // Initialize flow status
    setFlowStatus({
      flow_id: flowId,
      status: 'initializing',
      current_phase: 'Data Upload',
      progress: 0,
      started_at: new Date().toISOString(),
      crews: [
        { name: 'Field Mapping Crew', status: 'pending', progress: 0 },
        { name: 'Data Cleansing Crew', status: 'pending', progress: 0 },
        { name: 'Inventory Building Crew', status: 'pending', progress: 0 },
        { name: 'App-Server Dependency Crew', status: 'pending', progress: 0 },
        { name: 'App-App Dependency Crew', status: 'pending', progress: 0 },
        { name: 'Technical Debt Crew', status: 'pending', progress: 0 }
      ]
    });
    
    // Switch to monitoring view
    setActiveTab('monitoring');
    
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

  // Enhanced upload area component
  const EnhancedUploadArea: React.FC<{ area: UploadAreaType }> = ({ area }) => (
    <Card className={`cursor-pointer transition-all duration-300 hover:shadow-lg hover:scale-105 ${
      area.id === 'intelligent-discovery' ? 'ring-2 ring-blue-500 animate-pulse-glow' : ''
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${area.color} text-white`}>
            <area.icon className="h-6 w-6" />
          </div>
          <div>
            <CardTitle className="text-lg">{area.title}</CardTitle>
            {area.id === 'intelligent-discovery' && (
              <Badge variant="default" className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                <Brain className="h-3 w-3 mr-1" />
                AI-Powered
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription className="mb-4">{area.description}</CardDescription>
        <div className="space-y-2">
          <div className="text-sm font-medium">Supported formats:</div>
          <div className="flex flex-wrap gap-2">
            {area.acceptedTypes.map(type => (
              <Badge key={type} variant="outline" className="text-xs">
                {type}
              </Badge>
            ))}
          </div>
        </div>
        <div className="mt-4 space-y-2">
          <div className="text-sm font-medium">Examples:</div>
          <ul className="text-xs text-gray-600 space-y-1">
            {area.examples.map((example, idx) => (
              <li key={idx}>• {example}</li>
            ))}
          </ul>
        </div>
        <Button 
          className="w-full mt-4" 
          variant={area.id === 'intelligent-discovery' ? 'default' : 'outline'}
          onClick={() => handleUploadClick(area.id)}
        >
          {area.id === 'intelligent-discovery' ? 'Smart Upload' : 'Upload Files'}
        </Button>
      </CardContent>
    </Card>
  );

  // Flow overview component
  const FlowOverview: React.FC = () => (
    <div className="space-y-6">
      {flowStatus && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Discovery Flow Status
                </CardTitle>
                <CardDescription>Flow ID: {flowStatus.flow_id}</CardDescription>
              </div>
              <Badge variant="outline" className="text-lg px-3 py-1">
                {flowStatus.progress}% Complete
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Overall Progress</span>
                  <span>{flowStatus.current_phase}</span>
                </div>
                <Progress value={flowStatus.progress} className="h-3" />
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {flowStatus.crews.map((crew, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm font-medium mb-1">{crew.name}</div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {crew.status}
                      </Badge>
                      <span className="text-xs text-gray-600">{crew.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

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
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            {/* Context Breadcrumbs */}
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Enhanced Discovery Flow</h1>
              <p className="mt-2 text-gray-600">
                Intelligent AI-powered discovery with hierarchical crews, collaborative intelligence, and real-time monitoring
              </p>
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Brain className="h-6 w-6 text-blue-600" />
                  <div>
                    <p className="text-sm text-blue-800">
                      <strong>Next-Generation AI Discovery:</strong> Our enhanced crews use hierarchical management, 
                      cross-crew collaboration, shared memory, and planning intelligence to deliver superior migration insights.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Upload Success Toast */}
            {showUploadSuccess && (
              <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in-right z-50">
                <CheckCircle className="h-5 w-5" />
                <span>Files uploaded successfully! Starting AI analysis...</span>
              </div>
            )}

            {/* Enhanced Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-6">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4" />
                  Upload
                </TabsTrigger>
                <TabsTrigger value="monitoring" className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Monitoring
                </TabsTrigger>
                <TabsTrigger value="planning" className="flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Planning
                </TabsTrigger>
                <TabsTrigger value="memory" className="flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  Memory
                </TabsTrigger>
                <TabsTrigger value="communication" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Communication
                </TabsTrigger>
                <TabsTrigger value="insights" className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4" />
                  Insights
                </TabsTrigger>
              </TabsList>

              {/* Upload Tab */}
              <TabsContent value="upload" className="space-y-6">
                <FlowOverview />
                
                {/* Enhanced Upload Areas */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {uploadAreas.map((area) => (
                    <EnhancedUploadArea key={area.id} area={area} />
                  ))}
                </div>

                {/* File Analysis */}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-6">
                    <div className="border-t pt-6">
                      <h2 className="text-xl font-bold text-gray-900 mb-4">
                        Uploaded Files ({uploadedFiles.length})
                      </h2>
                      <div className="space-y-4">
                        {uploadedFiles.map((file) => (
                          <FileAnalysis key={file.id} uploadedFile={file} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </TabsContent>

              {/* Enhanced Monitoring Tab */}
              <TabsContent value="monitoring" className="space-y-6">
                {currentFlowId ? (
                  <div className="space-y-6">
                    <FlowOverview />
                    
                    {/* Enhanced Crew Status Cards */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {flowStatus?.crews.map((crew, index) => (
                        <CrewStatusCard
                          key={index}
                          crewData={{
                            name: crew.name,
                            status: crew.status as any,
                            progress: crew.progress,
                            agents: [
                              {
                                name: `${crew.name.split(' ')[0]} Manager`,
                                role: `Coordinates ${crew.name.toLowerCase()} activities`,
                                status: crew.status as any,
                                isManager: true,
                                collaborations: 2,
                                performance: {
                                  tasks_completed: Math.floor(Math.random() * 10),
                                  success_rate: 0.85 + Math.random() * 0.1,
                                  avg_duration_seconds: 30 + Math.random() * 60
                                }
                              },
                              {
                                name: `${crew.name.split(' ')[0]} Expert`,
                                role: `Specialized ${crew.name.toLowerCase()} analysis`,
                                status: crew.status as any,
                                collaborations: 1,
                                performance: {
                                  tasks_completed: Math.floor(Math.random() * 8),
                                  success_rate: 0.80 + Math.random() * 0.15,
                                  avg_duration_seconds: 45 + Math.random() * 90
                                }
                              }
                            ],
                            current_phase: `Processing ${crew.name.toLowerCase()}`,
                            collaboration_metrics: {
                              intra_crew_score: 7 + Math.random() * 3,
                              cross_crew_score: 6 + Math.random() * 3,
                              memory_sharing_active: crew.status !== 'pending',
                              knowledge_utilization: 6 + Math.random() * 4
                            },
                            performance_metrics: {
                              execution_time_seconds: 300 + Math.random() * 600,
                              success_rate: 0.85 + Math.random() * 0.1,
                              resource_utilization: 0.6 + Math.random() * 0.3,
                              quality_score: 7 + Math.random() * 3
                            },
                            planning_status: {
                              strategy: `${crew.name.toLowerCase()}_optimized`,
                              coordination_score: 7 + Math.random() * 3,
                              adaptive_adjustments: Math.floor(Math.random() * 5)
                            }
                          }}
                          showDetailedView={false}
                        />
                      ))}
                    </div>
                  </div>
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <FileSpreadsheet className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Flow</h3>
                      <p className="text-gray-600 mb-4">Upload files to start monitoring the discovery flow</p>
                      <Button onClick={() => setActiveTab('upload')}>
                        <FileSpreadsheet className="h-4 w-4 mr-2" />
                        Upload Files
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Planning Tab */}
              <TabsContent value="planning" className="space-y-6">
                {currentFlowId ? (
                  <PlanVisualization
                    flowId={currentFlowId}
                    onOptimizePlan={() => console.log('Optimizing plan...')}
                    onApplyRecommendation={(rec) => console.log('Applying recommendation:', rec)}
                  />
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <Target className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Planning Data</h3>
                      <p className="text-gray-600 mb-4">Start a discovery flow to view planning intelligence</p>
                      <Button onClick={() => setActiveTab('upload')}>
                        Start Discovery Flow
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Memory Tab */}
              <TabsContent value="memory" className="space-y-6">
                {currentFlowId ? (
                  <MemoryKnowledgePanel
                    flowId={currentFlowId}
                    onOptimize={() => console.log('Optimizing memory...')}
                  />
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <Brain className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Memory Data</h3>
                      <p className="text-gray-600 mb-4">Start a discovery flow to view memory and knowledge analytics</p>
                      <Button onClick={() => setActiveTab('upload')}>
                        Start Discovery Flow
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Communication Tab */}
              <TabsContent value="communication" className="space-y-6">
                {currentFlowId ? (
                  <AgentCommunicationPanel
                    flowId={currentFlowId}
                    maxMessages={100}
                  />
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <MessageSquare className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Communication Data</h3>
                      <p className="text-gray-600 mb-4">Start a discovery flow to monitor agent communications</p>
                      <Button onClick={() => setActiveTab('upload')}>
                        Start Discovery Flow
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Insights Tab */}
              <TabsContent value="insights" className="space-y-6">
                {uploadedFiles.length > 0 ? (
                  <div className="space-y-6">
                    <AgentInsightsSection />
                    <DataClassificationDisplay />
                    <AgentClarificationPanel />
                  </div>
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <Lightbulb className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Insights Available</h3>
                      <p className="text-gray-600 mb-4">Upload files to generate AI-powered insights</p>
                      <Button onClick={() => setActiveTab('upload')}>
                        Upload Files
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </>
  );
};

export default EnhancedCMDBImport; 