import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import { 
  Download, 
  BarChart3,
  FileText,
  Building2,
  TrendingUp,
  Users,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';

// Components
import { AnalysisFilters } from './components/AnalysisFilters';
import { AnalysisTable } from './components/AnalysisTable';
import { BulkActions } from './components/BulkActions';
import { AnalyticsCard } from './components/AnalyticsCard';

// Hooks
import { useAnalysisFilters } from './hooks/useAnalysisFilters';
import { useAnalysisSelection } from './hooks/useAnalysisSelection';
import { useAnalysisAnalytics } from './hooks/useAnalysisAnalytics';

// Types
import { AnalysisHistoryProps } from './types';

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({
  analyses,
  onExport,
  onDelete,
  onArchive,
  onCompare,
  onViewDetails,
  className = ''
}) => {
  const [currentTab, setCurrentTab] = useState('list');
  const [showCompareDialog, setShowCompareDialog] = useState(false);

  // Hooks
  const {
    filters,
    filteredAnalyses,
    departments,
    strategies,
    updateFilter,
    clearFilters
  } = useAnalysisFilters(analyses);

  const {
    selectedAnalyses,
    handleSelectAnalysis,
    handleSelectAll,
    clearSelection
  } = useAnalysisSelection();

  const analytics = useAnalysisAnalytics(filteredAnalyses);

  // Event handlers
  const handleExport = (format: 'csv' | 'pdf' | 'json') => {
    if (selectedAnalyses.length === 0) {
      toast.error('Please select analyses to export');
      return;
    }
    onExport?.(selectedAnalyses, format);
    clearSelection();
  };

  const handleCompare = () => {
    if (selectedAnalyses.length < 2) {
      toast.error('Please select at least 2 analyses to compare');
      return;
    }
    setShowCompareDialog(true);
  };

  const handleBulkAction = (action: 'archive' | 'delete') => {
    if (selectedAnalyses.length === 0) {
      toast.error('Please select analyses first');
      return;
    }

    selectedAnalyses.forEach(id => {
      if (action === 'archive') {
        onArchive?.(id);
      } else {
        onDelete?.(id);
      }
    });
    
    clearSelection();
    toast.success(`${selectedAnalyses.length} analyses ${action}d successfully`);
  };

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <AnalyticsCard
          title="Total Analyses"
          value={analytics.total}
          icon={FileText}
          description="All-time analyses"
        />
        <AnalyticsCard
          title="Completion Rate"
          value={`${analytics.completedRate}%`}
          icon={CheckCircle}
          description="Successfully completed"
        />
        <AnalyticsCard
          title="Avg Confidence"
          value={`${analytics.avgConfidence}%`}
          icon={TrendingUp}
          description="Average confidence score"
        />
        <AnalyticsCard
          title="Departments"
          value={Object.keys(analytics.departmentDistribution).length}
          icon={Building2}
          description="Active departments"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Strategy Distribution</CardTitle>
            <CardDescription>Recommended migration strategies</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(analytics.strategyDistribution).map(([strategy, count]) => (
                <div key={strategy} className="flex justify-between items-center">
                  <span className="text-sm capitalize">{strategy}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Effort Distribution</CardTitle>
            <CardDescription>Estimated effort levels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(analytics.effortDistribution).map(([effort, count]) => (
                <div key={effort} className="flex justify-between items-center">
                  <span className="text-sm capitalize">{effort.replace('_', ' ')}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderExportTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Export Options</CardTitle>
          <CardDescription>
            Export selected analyses in various formats. Select analyses from the list tab first.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              {selectedAnalyses.length} analyses selected for export
            </div>
            <div className="flex gap-3">
              <Button 
                onClick={() => handleExport('csv')}
                disabled={selectedAnalyses.length === 0}
                variant="outline"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
              <Button 
                onClick={() => handleExport('pdf')}
                disabled={selectedAnalyses.length === 0}
                variant="outline"
              >
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
              <Button 
                onClick={() => handleExport('json')}
                disabled={selectedAnalyses.length === 0}
                variant="outline"
              >
                <Download className="h-4 w-4 mr-2" />
                Export JSON
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className={`w-full space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Analysis History
          </CardTitle>
          <CardDescription>
            View and manage historical 6R analysis results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={currentTab} onValueChange={setCurrentTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="list">Analysis List</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="export">Export</TabsTrigger>
            </TabsList>

            <TabsContent value="list" className="space-y-4">
              <AnalysisFilters
                filters={filters}
                departments={departments}
                strategies={strategies}
                onFilterChange={updateFilter}
                onClearFilters={clearFilters}
              />

              <BulkActions
                selectedCount={selectedAnalyses.length}
                onCompare={handleCompare}
                onArchive={() => handleBulkAction('archive')}
                onDelete={() => handleBulkAction('delete')}
              />

              <AnalysisTable
                analyses={filteredAnalyses}
                selectedAnalyses={selectedAnalyses}
                onSelectAnalysis={handleSelectAnalysis}
                onSelectAll={handleSelectAll}
                onViewDetails={onViewDetails}
                onArchive={onArchive}
                onDelete={onDelete}
              />
            </TabsContent>

            <TabsContent value="analytics">
              {renderAnalyticsTab()}
            </TabsContent>

            <TabsContent value="export">
              {renderExportTab()}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Compare Dialog */}
      <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Compare Analyses</DialogTitle>
            <DialogDescription>
              Comparing {selectedAnalyses.length} selected analyses
            </DialogDescription>
          </DialogHeader>
          <div className="text-center py-8 text-gray-500">
            Comparison feature implementation in progress
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AnalysisHistory;