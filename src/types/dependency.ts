export interface HostingRelationship {
  application_name: string;
  server_name: string;
  confidence: number;
  status: 'pending' | 'confirmed';
}

export interface AppServerMapping {
  hosting_relationships: HostingRelationship[];
  suggested_mappings: HostingRelationship[];
  confidence_scores: Record<string, number>;
}

export interface CrossAppDependency {
  source_app: string;
  target_app: string;
  dependency_type: string;
  confidence: number;
  status: 'pending' | 'confirmed';
}

export interface ApplicationCluster {
  applications: string[];
  cluster_type?: string;
  confidence: number;
}

export interface CrossApplicationMapping {
  cross_app_dependencies: CrossAppDependency[];
  application_clusters: ApplicationCluster[];
  dependency_graph: {
    nodes: any[];
    edges: any[];
  };
  suggested_patterns: any[];
  confidence_scores: Record<string, number>;
}

export interface DependencyData {
  cross_application_mapping: CrossApplicationMapping;
  app_server_mapping: AppServerMapping;
  flow_id: string;
  crew_completion_status: Record<string, boolean>;
}

export interface DependencyNavigationOptions {
  skipValidation?: boolean;
  forceComplete?: boolean;
}

export interface DependencyAnalysisResponse {
  success: boolean;
  message: string;
  data: DependencyData;
}

export interface DependencyCreateResponse {
  success: boolean;
  message: string;
  data: {
    id: string;
    type: 'app-server' | 'app-app';
    status: 'pending' | 'confirmed';
  };
}

export interface DependencyUpdateResponse {
  success: boolean;
  message: string;
  data: {
    id: string;
    type: 'app-server' | 'app-app';
    status: 'pending' | 'confirmed';
  };
} 