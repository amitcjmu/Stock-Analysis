import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  Download, 
  Upload,
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  BarChart3,
  FileText,
  Users,
  Building2,
  Zap,
  Target,
  TrendingUp,
  AlertTriangle,
  Settings,
  Eye,
  Trash2,
  Plus
} from 'lucide-react';
import { toast } from 'sonner';

export interface BulkAnalysisJob {
  id: string;
  name: string;
  description?: string;
  applications: number[];
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  progress: number;
  total_applications: number;
  completed_applications: number;
  failed_applications: number;
  estimated_duration: number; // in minutes
  actual_duration?: number; // in minutes
  created_by: string;
  parameters?: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

export interface BulkAnalysisResult {
  job_id: string;
  application_id: number;
  application_name: string;
  status: 'completed' | 'failed' | 'skipped';
  recommended_strategy: string;
  confidence_score: number;
  processing_time: number; // in seconds
  error_message?: string;
  iteration_count: number;
}

export interface BulkAnalysisSummary {
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_applications_processed: number;
  average_confidence: number;
  strategy_distribution: Record<string, number>;
  processing_time_stats: {
    min: number;
    max: number;
    average: number;
    total: number;
  };
}

interface BulkAnalysisProps {
  jobs: BulkAnalysisJob[];
  results: BulkAnalysisResult[];
  summary: BulkAnalysisSummary;
  onCreateJob?: (jobConfig: Partial<BulkAnalysisJob>) => void;
  onStartJob?: (jobId: string) => void;
  onPauseJob?: (jobId: string) => void;
  onCancelJob?: (jobId: string) => void;
  onRetryJob?: (jobId: string) => void;
  onDeleteJob?: (jobId: string) => void;
  onExportResults?: (jobId: string, format: 'csv' | 'pdf' | 'json') => void;
  onViewJobDetails?: (jobId: string) => void;
  maxConcurrentJobs?: number;
  className?: string;
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-orange-100 text-orange-800'
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800'
};

const strategyColors = {
  rehost: 'bg-blue-100 text-blue-800',
  replatform: 'bg-green-100 text-green-800',
  refactor: 'bg-yellow-100 text-yellow-800',
  rearchitect: 'bg-purple-100 text-purple-800',
  rewrite: 'bg-indigo-100 text-indigo-800',
  replace: 'bg-orange-100 text-orange-800',
  retire: 'bg-red-100 text-red-800'
};

export const BulkAnalysis: React.FC<BulkAnalysisProps> = ({
  jobs,
  results,
  summary,
  onCreateJob,
  onStartJob,
  onPauseJob,
  onCancelJob,
  onRetryJob,
  onDeleteJob,
  onExportResults,
  onViewJobDetails,
  maxConcurrentJobs = 3,
  className = ''
}) => {
  const [currentTab, setCurrentTab] = useState('queue');
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newJobConfig, setNewJobConfig] = useState({
    name: '',
    description: '',
    priority: 'medium' as const,
    parallel_limit: 5,
    retry_failed: true,
    auto_approve_high_confidence: false,
    confidence_threshold: 0.8
  });

  // Real-time updates simulation
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate progress updates for running jobs
      // In real implementation, this would come from WebSocket or polling
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Filter and sort jobs
  const sortedJobs = useMemo(() => {
    return [...jobs].sort((a, b) => {
      // Running jobs first, then by priority, then by creation date
      if (a.status === 'running' && b.status !== 'running') return -1;
      if (b.status === 'running' && a.status !== 'running') return 1;
      
      const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [jobs]);

  // Calculate queue statistics
  const queueStats = useMemo(() => {
    const runningJobs = jobs.filter(j => j.status === 'running').length;
    const pendingJobs = jobs.filter(j => j.status === 'pending').length;
    const totalApplicationsInQueue = jobs
      .filter(j => j.status === 'pending' || j.status === 'running')
      .reduce((sum, j) => sum + j.total_applications, 0);
    
    const estimatedTimeRemaining = jobs
      .filter(j => j.status === 'pending')
      .reduce((sum, j) => sum + j.estimated_duration, 0);

    return {
      runningJobs,
      pendingJobs,
      totalApplicationsInQueue,
      estimatedTimeRemaining,
      canStartMore: runningJobs < maxConcurrentJobs
    };
  }, [jobs, maxConcurrentJobs]);

  const handleSelectJob = (jobId: string) => {
    setSelectedJobs(prev => 
      prev.includes(jobId) 
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  const handleSelectAll = () => {
    setSelectedJobs(
      selectedJobs.length === jobs.length 
        ? [] 
        : jobs.map(j => j.id)
    );
  };

  const handleCreateJob = () => {
    if (!newJobConfig.name.trim()) {
      toast.error('Please enter a job name');
      return;
    }

    if (onCreateJob) {
      onCreateJob({
        name: newJobConfig.name,
        description: newJobConfig.description,
        priority: newJobConfig.priority,
        parameters: {
          parallel_limit: newJobConfig.parallel_limit,
          retry_failed: newJobConfig.retry_failed,
          auto_approve_high_confidence: newJobConfig.auto_approve_high_confidence,
          confidence_threshold: newJobConfig.confidence_threshold
        }
      });
      
      setShowCreateDialog(false);
      setNewJobConfig({
        name: '',
        description: '',
        priority: 'medium',
        parallel_limit: 5,
        retry_failed: true,
        auto_approve_high_confidence: false,
        confidence_threshold: 0.8
      });
      
      toast.success('Bulk analysis job created');
    }
  };

  const handleBulkAction = (action: 'start' | 'pause' | 'cancel' | 'delete') => {
    if (selectedJobs.length === 0) {
      toast.error('Please select jobs first');
      return;
    }

    selectedJobs.forEach(jobId => {
      switch (action) {
        case 'start':
          if (onStartJob) onStartJob(jobId);
          break;
        case 'pause':
          if (onPauseJob) onPauseJob(jobId);
          break;
        case 'cancel':
          if (onCancelJob) onCancelJob(jobId);
          break;
        case 'delete':
          if (onDeleteJob) onDeleteJob(jobId);
          break;
      }
    });

    const actionText = action === 'delete' ? 'deleted' : `${action}ed`;
    toast.success(`${selectedJobs.length} jobs ${actionText}`);
    setSelectedJobs([]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'cancelled': return <Square className="h-4 w-4 text-orange-600" />;
      default: return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const renderJobRow = (job: BulkAnalysisJob) => {
    const isSelected = selectedJobs.includes(job.id);
    const jobResults = results.filter(r => r.job_id === job.id);
    const successRate = job.completed_applications > 0 
      ? ((job.completed_applications - job.failed_applications) / job.completed_applications) * 100 
      : 0;

    return (
      <TableRow 
        key={job.id} 
        className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
      >
        <TableCell>
          <Checkbox 
            checked={isSelected}
            onChange={() => handleSelectJob(job.id)}
          />
        </TableCell>
        <TableCell>
          <div>
            <div className="font-medium">{job.name}</div>
            {job.description && (
              <div className="text-sm text-gray-500">{job.description}</div>
            )}
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center space-x-2">
            {getStatusIcon(job.status)}
            <Badge className={statusColors[job.status]}>
              {job.status}
            </Badge>
          </div>
        </TableCell>
        <TableCell>
          <Badge className={priorityColors[job.priority]}>
            {job.priority}
          </Badge>
        </TableCell>
        <TableCell>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>{job.completed_applications}/{job.total_applications}</span>
              <span>{Math.round(job.progress)}%</span>
            </div>
            <Progress value={job.progress} className="h-2" />
            {job.status === 'running' && (
              <div className="text-xs text-gray-500">
                Success rate: {Math.round(successRate)}%
              </div>
            )}
          </div>
        </TableCell>
        <TableCell>
          <div className="text-sm">
            {job.status === 'running' && job.started_at && (
              <div>
                Running for {formatDuration((Date.now() - job.started_at.getTime()) / (1000 * 60))}
              </div>
            )}
            {job.status === 'completed' && job.actual_duration && (
              <div>
                Completed in {formatDuration(job.actual_duration)}
              </div>
            )}
            {job.status === 'pending' && (
              <div>
                Est. {formatDuration(job.estimated_duration)}
              </div>
            )}
          </div>
        </TableCell>
        <TableCell>{job.created_by}</TableCell>
        <TableCell>
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewJobDetails?.(job.id)}
            >
              <Eye className="h-3 w-3" />
            </Button>
            {job.status === 'pending' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onStartJob?.(job.id)}
                disabled={!queueStats.canStartMore}
              >
                <Play className="h-3 w-3" />
              </Button>
            )}
            {job.status === 'running' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onPauseJob?.(job.id)}
              >
                <Pause className="h-3 w-3" />
              </Button>
            )}
            {(job.status === 'failed' || job.status === 'cancelled') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onRetryJob?.(job.id)}
              >
                <RotateCcw className="h-3 w-3" />
              </Button>
            )}
            {job.status === 'completed' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onExportResults?.(job.id, 'csv')}
              >
                <Download className="h-3 w-3" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDeleteJob?.(job.id)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  const renderSummaryCards = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Total Jobs</p>
              <p className="text-2xl font-bold">{summary.total_jobs}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <Zap className="h-4 w-4 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Active Jobs</p>
              <p className="text-2xl font-bold">{summary.active_jobs}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <Target className="h-4 w-4 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Apps Processed</p>
              <p className="text-2xl font-bold">{summary.total_applications_processed}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold">{Math.round(summary.average_confidence * 100)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderCreateJobDialog = () => (
    <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Bulk Analysis Job</DialogTitle>
          <DialogDescription>
            Configure a new bulk analysis job for multiple applications
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Job Name *</label>
            <Input
              value={newJobConfig.name}
              onChange={(e) => setNewJobConfig(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter job name..."
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Description</label>
            <Input
              value={newJobConfig.description}
              onChange={(e) => setNewJobConfig(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Optional description..."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Priority</label>
              <Select 
                value={newJobConfig.priority} 
                onValueChange={(value) => setNewJobConfig(prev => ({ ...prev, priority: value as any }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium">Parallel Limit</label>
              <Input
                type="number"
                min="1"
                max="10"
                value={newJobConfig.parallel_limit}
                onChange={(e) => setNewJobConfig(prev => ({ ...prev, parallel_limit: parseInt(e.target.value) || 5 }))}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={newJobConfig.retry_failed}
                onChange={(checked) => setNewJobConfig(prev => ({ ...prev, retry_failed: checked }))}
              />
              <label className="text-sm">Automatically retry failed analyses</label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={newJobConfig.auto_approve_high_confidence}
                onChange={(checked) => setNewJobConfig(prev => ({ ...prev, auto_approve_high_confidence: checked }))}
              />
              <label className="text-sm">Auto-approve high confidence recommendations</label>
            </div>
          </div>
          
          {newJobConfig.auto_approve_high_confidence && (
            <div>
              <label className="text-sm font-medium">Confidence Threshold</label>
              <Input
                type="number"
                min="0.5"
                max="1"
                step="0.1"
                value={newJobConfig.confidence_threshold}
                onChange={(e) => setNewJobConfig(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) || 0.8 }))}
              />
            </div>
          )}
          
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateJob}>
              Create Job
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  const renderResultsTable = () => {
    const completedResults = results.filter(r => r.status === 'completed');
    
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium">Analysis Results</h3>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-1" />
              Export All
            </Button>
          </div>
        </div>
        
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Application</TableHead>
                <TableHead>Job</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Processing Time</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {completedResults.map((result) => (
                <TableRow key={`${result.job_id}-${result.application_id}`}>
                  <TableCell className="font-medium">{result.application_name}</TableCell>
                  <TableCell>
                    {jobs.find(j => j.id === result.job_id)?.name || result.job_id}
                  </TableCell>
                  <TableCell>
                    <Badge className={strategyColors[result.recommended_strategy as keyof typeof strategyColors]}>
                      {result.recommended_strategy}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <span>{Math.round(result.confidence_score * 100)}%</span>
                      {result.confidence_score >= 0.8 && (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{result.processing_time}s</TableCell>
                  <TableCell>
                    <Badge className={statusColors[result.status]}>
                      {result.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Bulk Analysis Management</CardTitle>
            <CardDescription>
              Manage and monitor bulk 6R analysis jobs for multiple applications
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {queueStats.runningJobs}/{maxConcurrentJobs} running
            </Badge>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-1" />
              New Job
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={currentTab} onValueChange={setCurrentTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="queue">Job Queue</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="queue" className="space-y-4">
            {/* Queue Status */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 text-blue-500" />
                    <div>
                      <p className="text-sm text-gray-600">Running</p>
                      <p className="text-xl font-bold">{queueStats.runningJobs}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-yellow-500" />
                    <div>
                      <p className="text-sm text-gray-600">Pending</p>
                      <p className="text-xl font-bold">{queueStats.pendingJobs}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <Building2 className="h-4 w-4 text-purple-500" />
                    <div>
                      <p className="text-sm text-gray-600">Apps in Queue</p>
                      <p className="text-xl font-bold">{queueStats.totalApplicationsInQueue}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-orange-500" />
                    <div>
                      <p className="text-sm text-gray-600">Est. Time</p>
                      <p className="text-xl font-bold">{formatDuration(queueStats.estimatedTimeRemaining)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Bulk Actions */}
            {selectedJobs.length > 0 && (
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-sm text-blue-700">
                  {selectedJobs.length} jobs selected
                </span>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('start')}
                    disabled={!queueStats.canStartMore}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Start
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('pause')}
                  >
                    <Pause className="h-4 w-4 mr-1" />
                    Pause
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('cancel')}
                  >
                    <Square className="h-4 w-4 mr-1" />
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleBulkAction('delete')}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            )}

            {/* Jobs Table */}
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectedJobs.length === jobs.length && jobs.length > 0}
                        onChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Job Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Created By</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedJobs.map(renderJobRow)}
                </TableBody>
              </Table>
            </div>

            {jobs.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No bulk analysis jobs found</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setShowCreateDialog(true)}
                  className="mt-2"
                >
                  Create First Job
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="results" className="space-y-4">
            {renderResultsTable()}
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            {renderSummaryCards()}
            
            {/* Strategy Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Strategy Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(summary.strategy_distribution).map(([strategy, count]) => (
                      <div key={strategy} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge className={strategyColors[strategy as keyof typeof strategyColors]}>
                            {strategy}
                          </Badge>
                        </div>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Processing Time Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Average:</span>
                      <span className="font-medium">{Math.round(summary.processing_time_stats.average)}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Minimum:</span>
                      <span className="font-medium">{summary.processing_time_stats.min}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Maximum:</span>
                      <span className="font-medium">{summary.processing_time_stats.max}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total:</span>
                      <span className="font-medium">{formatDuration(summary.processing_time_stats.total / 60)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Queue Settings</CardTitle>
                <CardDescription>
                  Configure bulk analysis queue behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Maximum Concurrent Jobs</label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={maxConcurrentJobs}
                    className="w-32"
                    readOnly
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Currently set to {maxConcurrentJobs} concurrent jobs
                  </p>
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Default Job Settings</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs text-gray-600">Default Priority</label>
                      <Select defaultValue="medium">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <label className="text-xs text-gray-600">Default Parallel Limit</label>
                      <Input type="number" min="1" max="10" defaultValue="5" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {renderCreateJobDialog()}
      </CardContent>
    </Card>
  );
};

export default BulkAnalysis; 