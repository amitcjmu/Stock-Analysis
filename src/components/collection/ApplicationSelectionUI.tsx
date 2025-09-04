import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Search, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { apiCall } from '@/config/api';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { toast } from '@/components/ui/use-toast';
import type { Asset } from '@/types/asset';

interface ApplicationSelectionUIProps {
  flowId: string;
  onComplete: () => void;
  onCancel: () => void;
  className?: string;
}

/**
 * Inline Application Selection UI Component
 * Used when a 422 'no_applications_selected' error occurs
 */
export const ApplicationSelectionUI: React.FC<ApplicationSelectionUIProps> = ({
  flowId,
  onComplete,
  onCancel,
  className = ''
}) => {
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [environmentFilter, setEnvironmentFilter] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 20; // Smaller page size for inline UI

  // Fetch applications with filters
  const {
    data: applicationsResponse,
    isLoading,
    error
  } = useQuery({
    queryKey: ['tenant-applications', currentPage, searchTerm, environmentFilter, criticalityFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: PAGE_SIZE.toString(),
      });

      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }
      if (environmentFilter) {
        params.append('environment', environmentFilter);
      }
      if (criticalityFilter) {
        params.append('business_criticality', criticalityFilter);
      }

      return await apiCall(`/discovery/inventory/applications?${params}`);
    },
    staleTime: 30 * 1000, // 30 seconds
  });

  const applications = applicationsResponse?.items || [];
  const totalCount = applicationsResponse?.total || 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  // Load pre-selected applications from flow
  useEffect(() => {
    const loadExistingSelections = async () => {
      try {
        const flowDetails = await collectionFlowApi.getFlowDetails(flowId);
        const selectedIds = flowDetails.collection_config?.selected_application_ids || [];
        setSelectedApplications(new Set(selectedIds));
      } catch (error) {
        console.warn('Failed to load existing application selections:', error);
      }
    };

    if (flowId) {
      loadExistingSelections();
    }
  }, [flowId]);

  const handleApplicationToggle = (applicationId: string) => {
    setSelectedApplications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(applicationId)) {
        newSet.delete(applicationId);
      } else {
        // Limit to 100 applications for UX
        if (newSet.size < 100) {
          newSet.add(applicationId);
        } else {
          toast({
            title: 'Selection Limit',
            description: 'Maximum 100 applications can be selected.',
            variant: 'default'
          });
        }
      }
      return newSet;
    });
  };

  const handleSubmit = async () => {
    if (selectedApplications.size === 0) {
      toast({
        title: 'Selection Required',
        description: 'Please select at least one application.',
        variant: 'destructive'
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await collectionFlowApi.updateFlowApplications(flowId, Array.from(selectedApplications));

      toast({
        title: 'Applications Selected',
        description: `${selectedApplications.size} applications selected for collection.`,
        variant: 'default'
      });

      onComplete();
    } catch (error: any) {
      console.error('Failed to update flow applications:', error);
      toast({
        title: 'Update Failed',
        description: error.message || 'Failed to update application selection.',
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    setCurrentPage(1);
  }, []);

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription>
          Failed to load applications. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className={`border-amber-200 bg-amber-50 ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-amber-900">Select Applications</CardTitle>
            <CardDescription className="text-amber-800">
              Choose applications for data collection. At least one application is required.
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
            className="text-amber-700 hover:text-amber-900"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-2 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search applications..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10 bg-white"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={environmentFilter}
              onChange={(e) => {
                setEnvironmentFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
            >
              <option value="">All Environments</option>
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
              <option value="testing">Testing</option>
            </select>
            <select
              value={criticalityFilter}
              onChange={(e) => {
                setCriticalityFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
            >
              <option value="">All Criticality</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Selection Summary */}
        {selectedApplications.size > 0 && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              {selectedApplications.size} application{selectedApplications.size !== 1 ? 's' : ''} selected
            </AlertDescription>
          </Alert>
        )}

        {/* Application List */}
        <div className="space-y-2 mb-4 max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : applications.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No applications found matching your filters.
            </div>
          ) : (
            applications.map((app: Asset) => (
              <div
                key={app.id}
                className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg bg-white hover:bg-gray-50"
              >
                <Checkbox
                  checked={selectedApplications.has(app.id)}
                  onCheckedChange={() => handleApplicationToggle(app.id)}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900 truncate">
                      {app.name}
                    </h4>
                    {app.environment && (
                      <Badge variant="outline" className="text-xs">
                        {app.environment}
                      </Badge>
                    )}
                    {app.business_criticality && (
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          app.business_criticality === 'critical' ? 'border-red-300 text-red-700' :
                          app.business_criticality === 'high' ? 'border-orange-300 text-orange-700' :
                          'border-gray-300 text-gray-700'
                        }`}
                      >
                        {app.business_criticality}
                      </Badge>
                    )}
                  </div>
                  {app.description && (
                    <p className="text-sm text-gray-600 truncate">
                      {app.description}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center mb-4">
            <div className="text-sm text-gray-600">
              Page {currentPage} of {totalPages} ({totalCount} total)
            </div>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
            className="text-amber-700 border-amber-300"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || selectedApplications.size === 0}
            className="bg-amber-600 hover:bg-amber-700"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Updating...
              </>
            ) : (
              `Select ${selectedApplications.size} Application${selectedApplications.size !== 1 ? 's' : ''}`
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
