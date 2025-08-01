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
    nodes: unknown[];
    edges: unknown[];
  };
  suggested_patterns: unknown[];
  confidence_scores: Record<string, number>;
}

export interface InventoryAsset {
  id: string;
  name?: string;
  asset_name?: string;
  type: string;
  properties?: Record<string, unknown>;
}

export interface DependencyData {
  cross_application_mapping: CrossApplicationMapping;
  app_server_mapping: AppServerMapping;
  flow_id: string;
  crew_completion_status: Record<string, boolean>;
  // CRITICAL: Add inventory data for dropdowns
  available_servers?: InventoryAsset[];
  available_applications?: InventoryAsset[];
  available_databases?: InventoryAsset[];
  total_inventory_assets?: number;
  analysis_progress?: {
    total_applications: number;
    mapped_dependencies: number;
    completion_percentage: number;
  };
  dependency_relationships?: unknown[];
  dependency_matrix?: Record<string, unknown>;
  critical_dependencies?: unknown[];
  orphaned_assets?: unknown[];
  dependency_complexity_score?: number;
  recommendations?: string[];
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
