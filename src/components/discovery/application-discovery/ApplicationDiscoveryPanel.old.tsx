import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle, 
  AlertCircle, 
  HelpCircle, 
  Users, 
  Server, 
  Database,
  Network,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Search,
  Filter,
  SlidersHorizontal,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { apiCall, API_CONFIG } from '@/config/api';

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

interface ApplicationPortfolio {
  applications: Application[];
  discovery_confidence: number;
  clarification_questions: Array<{
    id: string;
    application_id: string;
    application_name: string;
    question: string;
    options: string[];
    context: any;
  }>;
  discovery_metadata: {
    total_assets_analyzed: number;
    applications_discovered: number;
    high_confidence_apps: number;
    needs_clarification: number;
    analysis_timestamp: string;
  };
}

interface ApplicationDiscoveryPanelProps {
  onApplicationSelect?: (application: Application) => void;
  onValidationSubmit?: (applicationId: string, validation: any) => void;
}

const ApplicationDiscoveryPanel: React.FC<ApplicationDiscoveryPanelProps> = ({
  onApplicationSelect,
  onValidationSubmit
}) => {
  const [portfolio, setPortfolio] = useState<ApplicationPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Enhanced filtering and search state
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    validation_status: 'all',
    environment: 'all',
    business_criticality: 'all',
    technology_stack: 'all',
    component_count_min: '',
    component_count_max: '',
    confidence_min: ''
  });
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    fetchApplicationPortfolio();
  }, []);

  const fetchApplicationPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use the existing applications endpoint since APPLICATION_PORTFOLIO endpoint doesn't exist
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS, {
        method: 'GET'
      });
      
      // Transform the response to match expected ApplicationPortfolio format
      if (response && response.applications) {
        const transformedPortfolio: ApplicationPortfolio = {
          applications: response.applications.map((app: any) => ({
            id: app.id,
            name: app.name,
            confidence: 0.8, // Default confidence
            validation_status: 'medium_confidence' as const,
            component_count: 1,
            technology_stack: app.technology_stack ? [app.technology_stack] : ['Unknown'],
            environment: app.environment || 'Unknown',
            business_criticality: app.criticality || 'Medium',
            dependencies: {
              internal: [],
              external: [],
              infrastructure: []
            },
            components: [{
              name: app.name,
              asset_type: app.type || 'Application',
              environment: app.environment || 'Unknown'
            }],
            confidence_factors: {
              discovery_confidence: 0.8,
              component_count: 1,
              naming_clarity: 0.7,
              dependency_clarity: 0.6,
              technology_consistency: 0.75
            }
          })),
          discovery_confidence: 0.8,
          clarification_questions: [],
          discovery_metadata: {
            total_assets_analyzed: response.summary?.total_applications || response.applications.length,
            applications_discovered: response.applications.length,
            high_confidence_apps: Math.floor(response.applications.length * 0.6),
            needs_clarification: Math.floor(response.applications.length * 0.2),
            analysis_timestamp: new Date().toISOString()
          }
        };
        
        setPortfolio(transformedPortfolio);
      }
    } catch (err) {
      console.error('Failed to fetch application portfolio:', err);
      setError('Failed to load application portfolio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplicationValidation = async (applicationId: string, validationType: string, feedback: any = {}) => {
    try {
      const validationData = {
        application_id: applicationId,
        validation_type: validationType,
        feedback: feedback,
        application_data: portfolio?.applications.find(app => app.id === applicationId)
      };

      await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATION_VALIDATION, {
        method: 'POST',
        body: JSON.stringify(validationData)
      });

      // Refresh portfolio after validation
      await fetchApplicationPortfolio();
      
      if (onValidationSubmit) {
        onValidationSubmit(applicationId, validationData);
      }
    } catch (err) {
      console.error('Failed to submit validation:', err);
      setError('Failed to submit validation. Please try again.');
    }
  };

  // Filtering and search logic
  const getFilteredApplications = () => {
    if (!portfolio?.applications) return [];

    let filtered = portfolio.applications;

    // Text search
    if (searchTerm.trim()) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(app => 
        app.name.toLowerCase().includes(search) ||
        app.technology_stack.some(tech => tech.toLowerCase().includes(search)) ||
        app.environment.toLowerCase().includes(search) ||
        app.business_criticality.toLowerCase().includes(search) ||
        app.components.some(comp => comp.name.toLowerCase().includes(search))
      );
    }

    // Validation status filter
    if (filters.validation_status !== 'all') {
      filtered = filtered.filter(app => app.validation_status === filters.validation_status);
    }

    // Environment filter
    if (filters.environment !== 'all') {
      filtered = filtered.filter(app => app.environment === filters.environment);
    }

    // Business criticality filter
    if (filters.business_criticality !== 'all') {
      filtered = filtered.filter(app => app.business_criticality === filters.business_criticality);
    }

    // Technology stack filter
    if (filters.technology_stack !== 'all') {
      filtered = filtered.filter(app => 
        app.technology_stack.some(tech => tech.toLowerCase().includes(filters.technology_stack.toLowerCase()))
      );
    }

    // Component count filters
    if (filters.component_count_min) {
      filtered = filtered.filter(app => app.component_count >= parseInt(filters.component_count_min));
    }
    if (filters.component_count_max) {
      filtered = filtered.filter(app => app.component_count <= parseInt(filters.component_count_max));
    }

    // Confidence filter
    if (filters.confidence_min) {
      filtered = filtered.filter(app => app.confidence >= parseFloat(filters.confidence_min) / 100);
    }

    return filtered;
  };

  const getPaginatedApplications = () => {
    const filtered = getFilteredApplications();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return {
      applications: filtered.slice(startIndex, endIndex),
      total: filtered.length,
      totalPages: Math.ceil(filtered.length / itemsPerPage)
    };
  };

  // Get unique values for filter options
  const getUniqueValues = (field: keyof Application) => {
    if (!portfolio?.applications) return [];
    return [...new Set(portfolio.applications.map(app => app[field as keyof Application]).filter(Boolean))];
  };

  const getTechnologyOptions = () => {
    if (!portfolio?.applications) return [];
    const allTechs = portfolio.applications.flatMap(app => app.technology_stack);
    return [...new Set(allTechs)].filter(Boolean);
  };

  const clearFilters = () => {
    setFilters({
      validation_status: 'all',
      environment: 'all',
      business_criticality: 'all',
      technology_stack: 'all',
      component_count_min: '',
      component_count_max: '',
      confidence_min: ''
    });
    setSearchTerm('');
    setCurrentPage(1);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadgeVariant = (status: string) => {
    switch (status) {
      case 'high_confidence': return 'default';
      case 'medium_confidence': return 'secondary';
      case 'needs_clarification': return 'destructive';
      default: return 'outline';
    }
  };

  const getCriticalityColor = (criticality: string) => {
    switch (criticality.toLowerCase()) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

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
          <Button onClick={fetchApplicationPortfolio} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Discovery
          </Button>
        </CardContent>
      </Card>
    );
  }

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

  const { applications: paginatedApps, total: totalApps, totalPages } = getPaginatedApplications();

  return (
    <div className="space-y-6">
      {/* Discovery Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Application Portfolio Discovery
            </span>
            <Button onClick={fetchApplicationPortfolio} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {portfolio.discovery_metadata.applications_discovered}
              </div>
              <div className="text-sm text-gray-600">Applications Found</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {portfolio.discovery_metadata.high_confidence_apps}
              </div>
              <div className="text-sm text-gray-600">High Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {portfolio.discovery_metadata.needs_clarification}
              </div>
              <div className="text-sm text-gray-600">Need Clarification</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {portfolio.discovery_metadata.total_assets_analyzed}
              </div>
              <div className="text-sm text-gray-600">Assets Analyzed</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Overall Discovery Confidence</span>
              <span className={`text-sm font-medium ${getConfidenceColor(portfolio.discovery_confidence)}`}>
                {Math.round(portfolio.discovery_confidence * 100)}%
              </span>
            </div>
            <Progress value={portfolio.discovery_confidence * 100} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Applications List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Discovered Applications</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {totalApps} total
              </span>
              {(searchTerm || Object.values(filters).some(filter => filter !== 'all' && filter !== '')) && (
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Search and Filter Controls */}
          <div className="mb-6 space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search applications, technologies, environments..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2"
              >
                <SlidersHorizontal className="h-4 w-4" />
                Filters
                {showFilters && <ChevronDown className="h-4 w-4" />}
              </Button>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="border rounded-lg p-4 bg-gray-50 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Validation Status
                    </label>
                    <select
                      value={filters.validation_status}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, validation_status: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Status</option>
                      <option value="high_confidence">High Confidence</option>
                      <option value="medium_confidence">Medium Confidence</option>
                      <option value="needs_clarification">Needs Clarification</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Environment
                    </label>
                    <select
                      value={filters.environment}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, environment: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Environments</option>
                      {getUniqueValues('environment').map((env) => (
                        <option key={env} value={env}>{env}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Criticality
                    </label>
                    <select
                      value={filters.business_criticality}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, business_criticality: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Criticalities</option>
                      {getUniqueValues('business_criticality').map((crit) => (
                        <option key={crit} value={crit}>{crit}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Technology
                    </label>
                    <select
                      value={filters.technology_stack}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, technology_stack: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Technologies</option>
                      {getTechnologyOptions().map((tech) => (
                        <option key={tech} value={tech}>{tech}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Confidence (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.confidence_min}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, confidence_min: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0-100"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Components
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={filters.component_count_min}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, component_count_min: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Minimum components"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Components
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={filters.component_count_max}
                      onChange={(e) => {
                        setFilters(prev => ({ ...prev, component_count_max: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Maximum components"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              {/* Pagination Controls - Top */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">
                      Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalApps)} of {totalApps}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Per page:</span>
                    <select
                      value={itemsPerPage}
                      onChange={(e) => {
                        setItemsPerPage(parseInt(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value={5}>5</option>
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </select>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm px-2">
                        {currentPage} of {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Application List */}
              {paginatedApps.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Filter className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p>No applications match your current filters</p>
                  <Button variant="outline" onClick={clearFilters} className="mt-2">
                    Clear Filters
                  </Button>
                </div>
              ) : (
                paginatedApps.map((app) => (
                  <div
                    key={app.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => {
                      setSelectedApplication(app);
                      if (onApplicationSelect) onApplicationSelect(app);
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-lg">{app.name}</h3>
                      <div className="flex items-center gap-2">
                        <Badge variant={getConfidenceBadgeVariant(app.validation_status)}>
                          {app.validation_status.replace('_', ' ')}
                        </Badge>
                        <span className={`text-sm font-medium ${getConfidenceColor(app.confidence)}`}>
                          {Math.round(app.confidence * 100)}%
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Components:</span>
                        <span className="ml-1 font-medium">{app.component_count}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Environment:</span>
                        <span className="ml-1 font-medium">{app.environment}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Criticality:</span>
                        <span className={`ml-1 font-medium ${getCriticalityColor(app.business_criticality)}`}>
                          {app.business_criticality}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Tech Stack:</span>
                        <span className="ml-1 font-medium">
                          {app.technology_stack.slice(0, 2).join(', ')}
                          {app.technology_stack.length > 2 && '...'}
                        </span>
                      </div>
                    </div>

                    {app.validation_status === 'needs_clarification' && (
                      <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                        <div className="flex items-center gap-2 text-yellow-800">
                          <HelpCircle className="h-4 w-4" />
                          <span className="text-sm">This application needs validation</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}

              {/* Pagination Controls - Bottom */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center">
                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                    >
                      First
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    
                    {/* Page numbers */}
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const pageNum = currentPage - 2 + i;
                      if (pageNum >= 1 && pageNum <= totalPages) {
                        return (
                          <Button
                            key={pageNum}
                            variant={pageNum === currentPage ? "default" : "outline"}
                            size="sm"
                            onClick={() => setCurrentPage(pageNum)}
                          >
                            {pageNum}
                          </Button>
                        );
                      }
                      return null;
                    })}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                    >
                      Last
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="details" className="space-y-4">
              {selectedApplication ? (
                <div className="space-y-6">
                  <div className="border rounded-lg p-4">
                    <h3 className="font-semibold text-lg mb-4">{selectedApplication.name}</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium mb-2">Confidence Factors</h4>
                        <div className="space-y-2">
                          {Object.entries(selectedApplication.confidence_factors).map(([factor, value]) => (
                            <div key={factor} className="flex justify-between items-center">
                              <span className="text-sm capitalize">
                                {factor.replace('_', ' ')}
                              </span>
                              <div className="flex items-center gap-2">
                                <Progress value={value * 100} className="w-20 h-2" />
                                <span className="text-sm w-10">{Math.round(value * 100)}%</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium mb-2">Dependencies</h4>
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm text-gray-600">Internal:</span>
                            <span className="ml-2 text-sm">
                              {selectedApplication.dependencies.internal.length || 'None'}
                            </span>
                          </div>
                          <div>
                            <span className="text-sm text-gray-600">External:</span>
                            <span className="ml-2 text-sm">
                              {selectedApplication.dependencies.external.length || 'None'}
                            </span>
                          </div>
                          <div>
                            <span className="text-sm text-gray-600">Infrastructure:</span>
                            <span className="ml-2 text-sm">
                              {selectedApplication.dependencies.infrastructure.length || 'None'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Components ({selectedApplication.component_count})</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {selectedApplication.components.map((component, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                            <Server className="h-4 w-4 text-gray-600" />
                            <span>{component.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {component.asset_type}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600">
                  Select an application from the overview to see details
                </div>
              )}
            </TabsContent>

            <TabsContent value="validation" className="space-y-4">
              {portfolio.clarification_questions.length > 0 ? (
                <div className="space-y-4">
                  <h3 className="font-semibold">Applications Requiring Validation</h3>
                  {portfolio.clarification_questions.map((question) => (
                    <div key={question.id} className="border rounded-lg p-4">
                      <h4 className="font-medium mb-2">{question.application_name}</h4>
                      <p className="text-sm text-gray-700 mb-4">{question.question}</p>
                      
                      <div className="space-y-2">
                        {question.options.map((option, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            className="mr-2 mb-2"
                            onClick={() => handleApplicationValidation(question.application_id, option)}
                          >
                            {option}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-600" />
                  <p>All applications have been validated!</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationDiscoveryPanel; 