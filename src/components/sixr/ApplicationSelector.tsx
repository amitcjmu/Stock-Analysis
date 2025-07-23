import React from 'react'
import type { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import type { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Play, Database } from 'lucide-react';
import { toast } from 'sonner';

// Modularized imports
import { useApplicationFilters } from './hooks/useApplicationFilters';
import { useApplicationSelection } from './hooks/useApplicationSelection';
import { FilterPanel } from './components/FilterPanel';
import { ApplicationTable } from './components/ApplicationTable';
import { QueueManagement } from './components/QueueManagement';
import { ApplicationSelectionActions } from './components/ApplicationSelectionActions';
import type { ApplicationSelectorProps } from './types/ApplicationSelectorTypes';

// Types are now imported from the types file

export const ApplicationSelector: React.FC<ApplicationSelectorProps> = ({
  applications,
  selectedApplications,
  onSelectionChange,
  onStartAnalysis,
  analysisQueues = [],
  onQueueAction,
  maxSelections = 50,
  showQueue = true,
  className = ''
}) => {
  const [currentTab, setCurrentTab] = useState('applications');
  const [queueName, setQueueName] = useState('');
  
  // Use modularized hooks
  const {
    filteredApplications,
    departments,
    technologies,
    filters,
    setFilters,
    clearFilters,
    showAdvancedFilters,
    setShowAdvancedFilters
  } = useApplicationFilters(applications);
  
  const { handleSelectAll, handleSelectApplication, handleStartAnalysis } = useApplicationSelection({
    selectedApplications,
    onSelectionChange,
    onStartAnalysis,
    maxSelections
  });

  const handleAnalysisStart = () => {
    try {
      handleStartAnalysis(queueName);
      setQueueName('');
      toast.success(`Started analysis for ${selectedApplications.length} applications`);
    } catch (error) {
      toast.error((error as Error).message);
    }
  };


  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Application Selection</CardTitle>
            <CardDescription>
              Select applications for 6R migration strategy analysis
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {selectedApplications.length}/{maxSelections} selected
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              <Filter className="h-4 w-4 mr-1" />
              Filters
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Search and Filters */}
        <FilterPanel
          filters={filters}
          onFiltersChange={setFilters}
          departments={departments}
          technologies={technologies}
          showAdvanced={showAdvancedFilters}
          onToggleAdvanced={setShowAdvancedFilters}
          onClearFilters={clearFilters}
        />

        {/* Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="applications">
              Applications ({filteredApplications.length})
            </TabsTrigger>
            {showQueue && (
              <TabsTrigger value="queue">
                Analysis Queue ({analysisQueues.length})
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="applications" className="space-y-4">
            {/* Selection Actions */}
            <ApplicationSelectionActions
              selectedCount={selectedApplications.length}
              filteredCount={filteredApplications.length}
              allSelected={selectedApplications.length === filteredApplications.length && filteredApplications.length > 0}
              onSelectAll={() => handleSelectAll(filteredApplications)}
            />

            {/* Applications Table */}
            <ApplicationTable
              applications={filteredApplications}
              selectedApplications={selectedApplications}
              onSelectApplication={handleSelectApplication}
              onSelectAll={() => handleSelectAll(filteredApplications)}
            />

            {filteredApplications.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No applications found matching your criteria</p>
                <Button variant="outline" size="sm" onClick={clearFilters} className="mt-2">
                  Clear Filters
                </Button>
              </div>
            )}
          </TabsContent>

          {showQueue && (
            <TabsContent value="queue" className="space-y-4">
              <QueueManagement
                analysisQueues={analysisQueues}
                applications={applications}
                onQueueAction={onQueueAction}
              />
            </TabsContent>
          )}
        </Tabs>

        {/* Analysis Actions */}
        {selectedApplications.length > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <Input
                  placeholder="Analysis queue name (optional)"
                  value={queueName}
                  onChange={(e) => setQueueName(e.target.value)}
                />
              </div>
              <Button onClick={handleAnalysisStart} className="bg-blue-600 hover:bg-blue-700">
                <Play className="h-4 w-4 mr-2" />
                Start Analysis ({selectedApplications.length})
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ApplicationSelector; 