import type { useState } from 'react'
import { useEffect, useCallback } from 'react'
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
    context: unknown;
  }>;
  discovery_metadata: {
    total_assets_analyzed: number;
    applications_discovered: number;
    high_confidence_apps: number;
    needs_clarification: number;
    analysis_timestamp: string;
  };
}

export const useApplicationDiscovery = () => {
  const [portfolio, setPortfolio] = useState<ApplicationPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplicationPortfolio = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.APPLICATIONS, {
        method: 'GET'
      });

      if (response && response.status === 'success') {
        const transformedPortfolio: ApplicationPortfolio = {
          applications: response.data.applications || [],
          discovery_confidence: response.data.discovery_confidence || 0,
          clarification_questions: response.data.clarification_questions || [],
          discovery_metadata: {
            total_assets_analyzed: response.data.discovery_metadata?.total_assets_analyzed || 0,
            applications_discovered: response.data.discovery_metadata?.applications_discovered || 0,
            high_confidence_apps: response.data.discovery_metadata?.high_confidence_apps || 0,
            needs_clarification: response.data.discovery_metadata?.needs_clarification || 0,
            analysis_timestamp: response.data.discovery_metadata?.analysis_timestamp || new Date().toISOString()
          }
        };

        setPortfolio(transformedPortfolio);
      } else {
        throw new Error(response.message || 'Failed to fetch application portfolio');
      }
    } catch (err: unknown) {
      console.error('Error fetching application portfolio:', err);
      setError(err.message || 'Failed to load application discovery data');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleApplicationValidation = useCallback(async (
    applicationId: string, 
    validationType: string, 
    feedback: unknown = {}
  ) => {
    try {
      const validationData = {
        application_id: applicationId,
        validation_type: validationType,
        feedback: feedback,
        timestamp: new Date().toISOString()
      };

      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.VALIDATE_APPLICATION, {
        method: 'POST',
        body: JSON.stringify(validationData)
      });

      if (response && response.status === 'success') {
        // Update local state if needed
        if (portfolio) {
          const updatedApplications = portfolio.applications.map(app => 
            app.id === applicationId 
              ? { ...app, validation_status: 'high_confidence' as const }
              : app
          );
          
          setPortfolio({
            ...portfolio,
            applications: updatedApplications
          });
        }
        
        return true;
      }
      
      return false;
    } catch (err: unknown) {
      console.error('Error validating application:', err);
      return false;
    }
  }, [portfolio]);

  useEffect(() => {
    fetchApplicationPortfolio();
  }, [fetchApplicationPortfolio]);

  return {
    portfolio,
    loading,
    error,
    refetch: fetchApplicationPortfolio,
    validateApplication: handleApplicationValidation
  };
};