import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Play, Pause, Square, Download } from 'lucide-react';

// Import layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Import existing collection components
import { ProgressTracker } from '@/components/collection/ProgressTracker';

// Import types
import type { ProgressMilestone } from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

interface CollectionFlow {
  id: string;
  name: string;
  type: 'adaptive' | 'bulk' | 'integration';
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  estimatedCompletion?: string;
  applicationCount: number;
  completedApplications: number;
}

interface CollectionMetrics {
  totalFlows: number;
  activeFlows: number;
  completedFlows: number;
  failedFlows: number;
  totalApplications: number;
  completedApplications: number;
  averageCompletionTime: number;
  dataQualityScore: number;
}

/**
 * Collection Progress Monitoring page
 * Provides real-time monitoring of collection workflows and progress tracking
 */
const CollectionProgress: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  // State management
  const [flows, setFlows] = useState<CollectionFlow[]>([]);
  const [metrics, setMetrics] = useState<CollectionMetrics | null>(null);
  const [selectedFlow, setSelectedFlow] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Get specific flow ID from URL params if provided
  const flowId = searchParams.get('flowId');

  // Mock data - in real implementation this would come from WebSocket or polling
  useEffect(() => {
    const mockFlows: CollectionFlow[] = [
      {
        id: 'flow-001',
        name: 'Enterprise Applications - Adaptive Collection',
        type: 'adaptive',
        status: 'running',
        progress: 68,
        startedAt: '2025-07-19T09:00:00Z',
        applicationCount: 45,
        completedApplications: 31,
        estimatedCompletion: '2025-07-19T16:30:00Z'
      },
      {
        id: 'flow-002',
        name: 'Legacy Systems - Bulk Upload',
        type: 'bulk',
        status: 'completed',
        progress: 100,
        startedAt: '2025-07-19T08:00:00Z',
        completedAt: '2025-07-19T10:45:00Z',
        applicationCount: 150,
        completedApplications: 150
      },
      {
        id: 'flow-003',
        name: 'Data Integration - Conflict Resolution',
        type: 'integration',
        status: 'paused',
        progress: 42,
        startedAt: '2025-07-19T11:00:00Z',
        applicationCount: 8,
        completedApplications: 3
      },
      {
        id: 'flow-004',
        name: 'Cloud Services - Adaptive Collection',
        type: 'adaptive',
        status: 'failed',
        progress: 25,
        startedAt: '2025-07-19T12:00:00Z',
        applicationCount: 20,
        completedApplications: 5
      }
    ];

    const mockMetrics: CollectionMetrics = {
      totalFlows: 4,
      activeFlows: 1,
      completedFlows: 1,
      failedFlows: 1,
      totalApplications: 223,
      completedApplications: 189,
      averageCompletionTime: 180000, // 3 minutes in ms
      dataQualityScore: 92.5
    };

    setTimeout(() => {
      setFlows(mockFlows);
      setMetrics(mockMetrics);
      setSelectedFlow(flowId || mockFlows[0].id);
      setIsLoading(false);
    }, 1000);
  }, [flowId]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate progress updates for running flows
      setFlows(prev => prev.map(flow => {
        if (flow.status === 'running' && flow.progress < 100) {
          const newProgress = Math.min(flow.progress + Math.random() * 5, 100);
          const newCompleted = Math.floor((newProgress / 100) * flow.applicationCount);
          
          return {
            ...flow,
            progress: newProgress,
            completedApplications: newCompleted,
            ...(newProgress >= 100 && {
              status: 'completed' as const,
              completedAt: new Date().toISOString()
            })
          };
        }
        return flow;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Get detailed milestones for selected flow
  const getFlowMilestones = (flow: CollectionFlow): ProgressMilestone[] => {
    const baseProgress = flow.progress;
    
    switch (flow.type) {
      case 'adaptive':
        return [
          {
            id: 'initialization',
            title: 'Flow Initialization',
            description: 'Collection flow setup and configuration',
            achieved: baseProgress >= 10,
            achievedAt: baseProgress >= 10 ? flow.startedAt : undefined,
            weight: 0.1,
            required: true
          },
          {
            id: 'form-generation',
            title: 'Form Generation',
            description: 'Adaptive forms generated for applications',
            achieved: baseProgress >= 25,
            weight: 0.15,
            required: true
          },
          {
            id: 'data-collection',
            title: 'Data Collection',
            description: 'Collecting application data via forms',
            achieved: baseProgress >= 75,
            weight: 0.5,
            required: true
          },
          {
            id: 'validation',
            title: 'Data Validation',
            description: 'Validating collected data quality',
            achieved: baseProgress >= 90,
            weight: 0.15,
            required: true
          },
          {
            id: 'completion',
            title: 'Flow Completion',
            description: 'Collection process completed',
            achieved: baseProgress >= 100,
            achievedAt: flow.completedAt,
            weight: 0.1,
            required: true
          }
        ];
      
      case 'bulk':
        return [
          {
            id: 'upload',
            title: 'File Upload',
            description: 'Bulk data file uploaded',
            achieved: baseProgress >= 20,
            weight: 0.2,
            required: true
          },
          {
            id: 'parsing',
            title: 'Data Parsing',
            description: 'File data parsed and structured',
            achieved: baseProgress >= 40,
            weight: 0.2,
            required: true
          },
          {
            id: 'processing',
            title: 'Data Processing',
            description: 'Processing and normalizing data',
            achieved: baseProgress >= 80,
            weight: 0.4,
            required: true
          },
          {
            id: 'completion',
            title: 'Processing Complete',
            description: 'Bulk processing completed',
            achieved: baseProgress >= 100,
            achievedAt: flow.completedAt,
            weight: 0.2,
            required: true
          }
        ];
      
      case 'integration':
        return [
          {
            id: 'source-analysis',
            title: 'Source Analysis',
            description: 'Analyzing data from multiple sources',
            achieved: baseProgress >= 25,
            weight: 0.25,
            required: true
          },
          {
            id: 'conflict-detection',
            title: 'Conflict Detection',
            description: 'Identifying data conflicts',
            achieved: baseProgress >= 50,
            weight: 0.25,
            required: true
          },
          {
            id: 'resolution',
            title: 'Conflict Resolution',
            description: 'Resolving data conflicts',
            achieved: baseProgress >= 85,
            weight: 0.35,
            required: true
          },
          {
            id: 'integration',
            title: 'Data Integration',
            description: 'Final data integration and validation',
            achieved: baseProgress >= 100,
            achievedAt: flow.completedAt,
            weight: 0.15,
            required: true
          }
        ];
      
      default:
        return [];
    }
  };

  const handleFlowAction = async (flowId: string, action: 'pause' | 'resume' | 'stop') => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setFlows(prev => prev.map(flow => {
        if (flow.id === flowId) {
          switch (action) {
            case 'pause':
              return { ...flow, status: 'paused' as const };
            case 'resume':
              return { ...flow, status: 'running' as const };
            case 'stop':
              return { ...flow, status: 'failed' as const };
            default:
              return flow;
          }
        }
        return flow;
      }));

      toast({
        title: `Flow ${action}${action.endsWith('e') ? 'd' : 'ped'}`,
        description: `Collection flow has been ${action}${action.endsWith('e') ? 'd' : 'ped'} successfully.`
      });
    } catch (error) {
      toast({
        title: 'Action Failed',
        description: `Failed to ${action} the collection flow.`,
        variant: 'destructive'
      });
    }
  };

  const handleExportReport = () => {
    // Generate mock report data
    const reportData = {
      generatedAt: new Date().toISOString(),
      metrics,
      flows: flows.map(flow => ({
        ...flow,
        milestones: getFlowMilestones(flow)
      }))
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `collection-progress-report-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    toast({
      title: 'Report Exported',
      description: 'Progress report has been downloaded successfully.'
    });
  };

  const getStatusBadge = (status: CollectionFlow['status']) => {
    switch (status) {
      case 'running':
        return <Badge variant="default">Running</Badge>;
      case 'paused':
        return <Badge variant="secondary">Paused</Badge>;
      case 'completed':
        return <Badge variant="outline">Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            <div className="flex items-center justify-center min-h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading collection progress...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const selectedFlowData = flows.find(f => f.id === selectedFlow);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate('/collection')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Collection
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Collection Progress Monitor</h1>
            <p className="text-muted-foreground">
              Real-time monitoring of collection workflows and progress
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
          </Button>
          <Button 
            variant="outline" 
            onClick={handleExportReport}
          >
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{metrics.activeFlows}</p>
                <p className="text-sm text-muted-foreground">Active Flows</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{metrics.completedApplications}</p>
                <p className="text-sm text-muted-foreground">Apps Processed</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{Math.round((metrics.completedApplications / metrics.totalApplications) * 100)}%</p>
                <p className="text-sm text-muted-foreground">Overall Progress</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{metrics.dataQualityScore}%</p>
                <p className="text-sm text-muted-foreground">Data Quality</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Flow List Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Active Flows</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {flows.map((flow) => (
                <div
                  key={flow.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedFlow === flow.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedFlow(flow.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{flow.name}</span>
                    {getStatusBadge(flow.status)}
                  </div>
                  <Progress value={flow.progress} className="h-2 mb-2" />
                  <div className="text-xs text-muted-foreground">
                    {flow.completedApplications}/{flow.applicationCount} apps ({Math.round(flow.progress)}%)
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {selectedFlowData && (
            <>
              {/* Flow Details */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{selectedFlowData.name}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        Started: {new Date(selectedFlowData.startedAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {selectedFlowData.status === 'running' && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleFlowAction(selectedFlowData.id, 'pause')}
                        >
                          <Pause className="h-4 w-4" />
                        </Button>
                      )}
                      {selectedFlowData.status === 'paused' && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleFlowAction(selectedFlowData.id, 'resume')}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                      )}
                      {(selectedFlowData.status === 'running' || selectedFlowData.status === 'paused') && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleFlowAction(selectedFlowData.id, 'stop')}
                        >
                          <Square className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Progress</span>
                        <span>{Math.round(selectedFlowData.progress)}%</span>
                      </div>
                      <Progress value={selectedFlowData.progress} className="h-3" />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Applications:</span>
                        <span className="ml-2 font-medium">
                          {selectedFlowData.completedApplications}/{selectedFlowData.applicationCount}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Type:</span>
                        <span className="ml-2 font-medium capitalize">{selectedFlowData.type}</span>
                      </div>
                      {selectedFlowData.estimatedCompletion && (
                        <div>
                          <span className="text-muted-foreground">ETA:</span>
                          <span className="ml-2 font-medium">
                            {new Date(selectedFlowData.estimatedCompletion).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {selectedFlowData.completedAt && (
                        <div>
                          <span className="text-muted-foreground">Completed:</span>
                          <span className="ml-2 font-medium">
                            {new Date(selectedFlowData.completedAt).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Progress Tracker */}
              <ProgressTracker
                formId={selectedFlowData.id}
                totalSections={getFlowMilestones(selectedFlowData).length}
                completedSections={getFlowMilestones(selectedFlowData).filter(m => m.achieved).length}
                overallCompletion={selectedFlowData.progress}
                confidenceScore={85}
                milestones={getFlowMilestones(selectedFlowData)}
                timeSpent={Date.now() - new Date(selectedFlowData.startedAt).getTime()}
                estimatedTimeRemaining={
                  selectedFlowData.estimatedCompletion 
                    ? new Date(selectedFlowData.estimatedCompletion).getTime() - Date.now()
                    : 0
                }
              />
            </>
          )}
        </div>
      </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionProgress;