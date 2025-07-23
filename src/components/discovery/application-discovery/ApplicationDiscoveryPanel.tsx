import React from 'react'
import type { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Input } from '@/components/ui/input';
import { Search, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

import { ApplicationOverview } from './components/ApplicationOverview';
import { ApplicationFilters } from './components/ApplicationFilters';
import { ApplicationList } from './components/ApplicationList';
import type { ApplicationDetails } from './components/ApplicationDetails';
import { Pagination } from './components/Pagination';

import { useApplicationDiscovery } from './hooks/useApplicationDiscovery';
import { useApplicationFilters } from './hooks/useApplicationFilters';

interface Application {
  id: string;
  name: string;
  confidence: number;
  validation_status: 'high_confidence' | 'medium_confidence' | 'needs_clarification';
  component_count: number;
  technology_stack: string[];
  environment: string;
  business_criticality: string;
  dependencies: {
    internal: string[];
    external: string[];
    infrastructure: string[];
  };
  components: Array<{
    name: string;
    asset_type: string;
    environment: string;
  }>;
  confidence_factors: {
    discovery_confidence: number;
    component_count: number;
    naming_clarity: number;
    dependency_clarity: number;
    technology_consistency: number;
  };
}

interface ApplicationValidation {
  type: string;
}

interface ApplicationDiscoveryPanelProps {
  onApplicationSelect?: (application: Application) => void;
  onValidationSubmit?: (applicationId: string, validation: ApplicationValidation) => void;
}

const ApplicationDiscoveryPanel: React.FC<ApplicationDiscoveryPanelProps> = ({
  onApplicationSelect,
  onValidationSubmit
}) => {
  const { portfolio, loading, error, refetch, validateApplication } = useApplicationDiscovery();
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    showFilters,
    setShowFilters,
    filteredApplications,
    clearFilters,
    filterOptions
  } = useApplicationFilters(portfolio?.applications || []);

  // Pagination logic
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedApplications = filteredApplications.slice(startIndex, endIndex);
  const totalPages = Math.ceil(filteredApplications.length / itemsPerPage);

  const handleApplicationSelect = (application: Application) => {
    setSelectedApplication(application);
    if (onApplicationSelect) {
      onApplicationSelect(application);
    }
  };

  const handleValidation = async (validationType: string) => {
    if (!selectedApplication) return;

    const success = await validateApplication(selectedApplication.id, validationType);
    if (success && onValidationSubmit) {
      onValidationSubmit(selectedApplication.id, { type: validationType });
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (items: number) => {
    setItemsPerPage(items);
    setCurrentPage(1);
  };

  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Discovering Applications...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            Application Discovery Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={refetch} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Discovery
          </Button>
        </CardContent>
      </Card>
    );
  }

  // No data state
  if (!portfolio) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Application Discovery</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">No application portfolio data available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Discovery Overview */}
      <ApplicationOverview
        discoveryMetadata={portfolio.discovery_metadata}
        discoveryConfidence={portfolio.discovery_confidence}
        clarificationCount={portfolio.clarification_questions.length}
        onRefresh={refetch}
      />

      {/* Main Content */}
      <Card>
        <CardHeader>
          <CardTitle>Discovered Applications</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Search and Filters */}
          <div className="space-y-4 mb-6">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search applications, technologies, environments..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <ApplicationFilters
                filters={filters}
                onFilterChange={setFilters}
                showFilters={showFilters}
                onToggleFilters={() => setShowFilters(!showFilters)}
                onClearFilters={clearFilters}
                environmentOptions={filterOptions.environments}
                criticalityOptions={filterOptions.criticalities}
                technologyOptions={filterOptions.technologies}
              />
            </div>
          </div>

          {/* Results count */}
          <p className="text-sm text-gray-600 mb-4">
            Found {filteredApplications.length} applications
            {searchTerm || Object.values(filters).some(v => v !== 'all' && v !== '') 
              ? ` (filtered from ${portfolio.applications.length} total)` 
              : ''}
          </p>

          {/* Application List */}
          {paginatedApplications.length > 0 ? (
            <>
              <ApplicationList
                applications={paginatedApplications}
                onApplicationSelect={handleApplicationSelect}
              />
              
              {/* Pagination */}
              {totalPages > 1 && (
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  totalItems={filteredApplications.length}
                  itemsPerPage={itemsPerPage}
                  onPageChange={handlePageChange}
                  onItemsPerPageChange={handleItemsPerPageChange}
                />
              )}
            </>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No applications found matching your criteria
            </div>
          )}
        </CardContent>
      </Card>

      {/* Application Details Modal */}
      {selectedApplication && (
        <ApplicationDetails
          application={selectedApplication}
          onClose={() => setSelectedApplication(null)}
          onValidate={handleValidation}
        />
      )}
    </div>
  );
};

export default ApplicationDiscoveryPanel;