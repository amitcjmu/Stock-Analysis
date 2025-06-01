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
  Trash2
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

  useEffect(() => {
    fetchApplicationPortfolio();
  }, []);

  const fetchApplicationPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATION_PORTFOLIO, {
        method: 'GET'
      });
      
      setPortfolio(response.application_portfolio);
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
          <CardTitle>Discovered Applications</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              {portfolio.applications.map((app) => (
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
              ))}
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