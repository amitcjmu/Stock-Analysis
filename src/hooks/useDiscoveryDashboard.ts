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
    queryKey: ['discovery', 'metrics', client?.id, engagement?.id],
    queryFn: async () => {
      // Security fix: Never fall back to hardcoded client IDs
      if (!client?.id || !engagement?.id) {
        console.warn('Missing client or engagement context for discovery metrics');
        // Return default empty metrics instead of throwing error
        return {
          totalAssets: 0,
          totalApplications: 0,
          applicationToServerMapping: 0,
          dependencyMappingComplete: 0,
          techDebtItems: 0,
          criticalIssues: 0,
          discoveryCompleteness: 0,
          dataQuality: 0
        };
      }

      return await masterFlowServiceExtended.getDiscoveryMetrics(
        client.id,
        engagement.id
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    enabled: !!client?.id && !!engagement?.id, // Only run when auth context is available
  });
};

export const useApplicationLandscape = () => {
  const { client, engagement } = useAuth();

  return useQuery<ApplicationLandscape, Error>({
    queryKey: ['discovery', 'application-landscape', client?.id, engagement?.id],
    queryFn: async () => {
      // Security fix: Never fall back to hardcoded client IDs
      if (!client?.id || !engagement?.id) {
        console.warn('Missing client or engagement context for application landscape');
        // Return default empty landscape instead of throwing error
        return {
          applications: [],
          summary: {
            byEnvironment: {},
            byCriticality: {},
            byTechStack: {}
          }
        };
      }

      return await masterFlowServiceExtended.getApplicationLandscape(
        client.id,
        engagement.id
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    enabled: !!client?.id && !!engagement?.id, // Only run when auth context is available
  });
};

export const useInfrastructureLandscape = () => {
  const { client, engagement } = useAuth();

  return useQuery<InfrastructureLandscape, Error>({
    queryKey: ['discovery', 'infrastructure-landscape', client?.id, engagement?.id],
    queryFn: async () => {
      // Security fix: Never fall back to hardcoded client IDs
      if (!client?.id || !engagement?.id) {
        console.warn('Missing client or engagement context for infrastructure landscape');
        // Return default empty infrastructure instead of throwing error
        return {
          servers: {
            total: 0,
            physical: 0,
            virtual: 0,
            cloud: 0,
            supportedOS: 0,
            deprecatedOS: 0
          },
          databases: {
            total: 0,
            supportedVersions: 0,
            deprecatedVersions: 0,
            endOfLife: 0
          },
          networks: {
            devices: 0,
            securityDevices: 0,
            storageDevices: 0
          }
        };
      }

      return await masterFlowServiceExtended.getInfrastructureLandscape(
        client.id,
        engagement.id
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    enabled: !!client?.id && !!engagement?.id, // Only run when auth context is available
  });
};
