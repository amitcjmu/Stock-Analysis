import React from 'react';
import { Plus, Settings, Play, Pause, Square, Trash2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';

// Custom hooks and components
import { useBulkAnalysis } from './hooks/useBulkAnalysis';
import { JobQueue } from './components/JobQueue';
import { JobCreationDialog } from './components/JobCreationDialog';
import { JobResults } from './components/JobResults';
import { AnalyticsSummary } from './components/AnalyticsSummary';
import { BulkAnalysisProps } from './types';

const BulkAnalysisContainer: React.FC<BulkAnalysisProps> = ({
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
  onViewResults,
  maxConcurrentJobs = 3,
  className = ''
}) => {
  const {
    // State
    state,
    newJobConfig,
    setNewJobConfig,
    
    // Computed values
    filteredAndSortedJobs,
    queueStats,
    
    // Actions
    setSelectedJobs,
    setActiveTab,
    setFilterStatus,
    setFilterPriority,
    setSearchQuery,
    setShowCreateDialog,
    setShowResultsDialog,
    setSelectedJobForResults,
    handleSelectJob,
    handleSelectAll,
    handleCreateJob,
    handleStartJob,
    handlePauseJob,
    handleCancelJob,
    handleRetryJob,
    handleDeleteJob,
    handleBulkAction,
    handleExportResults,
    handleViewResults
  } = useBulkAnalysis({
    jobs,
    results,
    summary,
    maxConcurrentJobs,
    onCreateJob,
    onStartJob,
    onPauseJob,
    onCancelJob,
    onRetryJob,
    onDeleteJob,
    onExportResults
  });

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Bulk Analysis</h1>
          <p className="text-gray-600">
            Manage and monitor bulk 6R migration strategy analysis jobs
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>New Job</span>
          </Button>
          
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
        {/* Search */}
        <div className="flex-1 min-w-64">
          <Input
            placeholder="Search jobs..."
            value={state.searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Status Filter */}
        <Select value={state.filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>

        {/* Priority Filter */}
        <Select value={state.filterPriority} onValueChange={setFilterPriority}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>

        {/* Bulk Actions */}
        {state.selectedJobs.length > 0 && (
          <div className="flex items-center space-x-2 ml-auto">
            <span className="text-sm text-gray-600">
              {state.selectedJobs.length} selected
            </span>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBulkAction('start', state.selectedJobs)}
              disabled={!queueStats.canStartMore}
            >
              <Play className="h-3 w-3" />
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBulkAction('pause', state.selectedJobs)}
            >
              <Pause className="h-3 w-3" />
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBulkAction('cancel', state.selectedJobs)}
            >
              <Square className="h-3 w-3" />
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBulkAction('delete', state.selectedJobs)}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={state.activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="queue">Job Queue ({jobs.length})</TabsTrigger>
          <TabsTrigger value="results">Results ({results.length})</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="queue" className="space-y-6">
          <JobQueue
            jobs={filteredAndSortedJobs}
            selectedJobs={state.selectedJobs}
            queueStats={queueStats}
            onSelectJob={handleSelectJob}
            onSelectAll={handleSelectAll}
            onStartJob={handleStartJob}
            onPauseJob={handlePauseJob}
            onCancelJob={handleCancelJob}
            onRetryJob={handleRetryJob}
            onDeleteJob={handleDeleteJob}
            onViewResults={handleViewResults}
          />
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          <JobResults
            results={results}
            summary={summary}
            selectedJobId={state.selectedJobForResults}
            onExportResults={handleExportResults}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <AnalyticsSummary summary={summary} />
        </TabsContent>
      </Tabs>

      {/* Job Creation Dialog */}
      <JobCreationDialog
        open={state.showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={newJobConfig}
        onFormDataChange={setNewJobConfig}
        onCreateJob={handleCreateJob}
      />
    </div>
  );
};

export default BulkAnalysisContainer;