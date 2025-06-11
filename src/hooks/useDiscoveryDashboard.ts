import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

// Types
export interface DiscoveryMetrics {
  totalAssets: number;
  totalApplications: number;
  applicationToServerMapping: number;
  dependencyMappingComplete: number;
  techDebtItems: number;
  criticalIssues: number;
  discoveryCompleteness: number;
  dataQuality: number;
}

export interface ApplicationLandscape {
  applications: Array<{
    id: string;
    name: string;
    environment: string;
    criticality: string;
    techStack: string[];
    serverCount: number;
    databaseCount: number;
    dependencyCount: number;
    techDebtScore: number;
    cloudReadiness: number;
  }>;
  summary: {
    byEnvironment: { [key: string]: number };
    byCriticality: { [key: string]: number };
    byTechStack: { [key: string]: number };
  };
}

export interface InfrastructureLandscape {
  servers: {
    total: number;
    physical: number;
    virtual: number;
    cloud: number;
    supportedOS: number;
    deprecatedOS: number;
  };
  databases: {
    total: number;
    supportedVersions: number;
    deprecatedVersions: number;
    endOfLife: number;
  };
  networks: {
    devices: number;
    securityDevices: number;
    storageDevices: number;
  };
}

export const useDiscoveryMetrics = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<DiscoveryMetrics, Error>({
    queryKey: ['discovery', 'metrics'],
    queryFn: async () => {
      const response = await apiCall(
        '/api/v1/discovery/metrics',
        { 
          method: 'GET',
          headers: getAuthHeaders()
        },
        true
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useApplicationLandscape = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<ApplicationLandscape, Error>({
    queryKey: ['discovery', 'application-landscape'],
    queryFn: async () => {
      const response = await apiCall(
        '/api/v1/discovery/application-landscape',
        { 
          method: 'GET',
          headers: getAuthHeaders()
        },
        true
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useInfrastructureLandscape = () => {
  const { getAuthHeaders } = useAuth();
  
  return useQuery<InfrastructureLandscape, Error>({
    queryKey: ['discovery', 'infrastructure-landscape'],
    queryFn: async () => {
      const response = await apiCall(
        '/api/v1/discovery/infrastructure-landscape',
        { 
          method: 'GET',
          headers: getAuthHeaders()
        },
        true
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}; 