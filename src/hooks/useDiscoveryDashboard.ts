import { useQuery } from '@tanstack/react-query';
import masterFlowServiceExtended from '@/services/api/masterFlowService.extensions';
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
  const { client, engagement } = useAuth();
  
  return useQuery<DiscoveryMetrics, Error>({
    queryKey: ['discovery', 'metrics'],
    queryFn: async () => {
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      return await masterFlowServiceExtended.getDiscoveryMetrics(
        clientAccountId,
        engagementId
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useApplicationLandscape = () => {
  const { client, engagement } = useAuth();
  
  return useQuery<ApplicationLandscape, Error>({
    queryKey: ['discovery', 'application-landscape'],
    queryFn: async () => {
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      return await masterFlowServiceExtended.getApplicationLandscape(
        clientAccountId,
        engagementId
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

export const useInfrastructureLandscape = () => {
  const { client, engagement } = useAuth();
  
  return useQuery<InfrastructureLandscape, Error>({
    queryKey: ['discovery', 'infrastructure-landscape'],
    queryFn: async () => {
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      return await masterFlowServiceExtended.getInfrastructureLandscape(
        clientAccountId,
        engagementId
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}; 