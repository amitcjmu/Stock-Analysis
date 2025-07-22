import React from 'react';
import { Network } from 'lucide-react';

interface DependencyStatsProps {
  dependencyData: {
    cross_application_mapping: {
      cross_app_dependencies: unknown[];
      application_clusters: unknown[];
    };
    app_server_mapping: {
      hosting_relationships: unknown[];
    };
  } | null;
}

export const DependencyStats: React.FC<DependencyStatsProps> = ({ dependencyData }) => {
  if (!dependencyData) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-lg"></div>
              <div>
                <div className="h-4 bg-gray-200 rounded mb-2 w-20"></div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const totalDependencies = (
    (dependencyData.cross_application_mapping.cross_app_dependencies || []).length +
    (dependencyData.app_server_mapping.hosting_relationships || []).length
  );

  const applicationClusters = dependencyData.cross_application_mapping.application_clusters || [];

  const criticalDependencies = [
    ...(dependencyData.cross_application_mapping.cross_app_dependencies || []),
    ...(dependencyData.app_server_mapping.hosting_relationships || [])
  ].filter(dep => dep.impact_level === 'critical').length;

  const highImpactDependencies = [
    ...(dependencyData.cross_application_mapping.cross_app_dependencies || []),
    ...(dependencyData.app_server_mapping.hosting_relationships || [])
  ].filter(dep => dep.impact_level === 'high').length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3">
          <Network className="h-8 w-8 text-blue-500" />
          <div>
            <h3 className="text-sm font-medium text-gray-600">Total Dependencies</h3>
            <p className="text-2xl font-bold text-gray-900">
              {totalDependencies}
            </p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">C</span>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">Critical Dependencies</h3>
            <p className="text-2xl font-bold text-red-600">
              {criticalDependencies}
            </p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">H</span>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">High Impact</h3>
            <p className="text-2xl font-bold text-orange-600">
              {highImpactDependencies}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">A</span>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">Application Clusters</h3>
            <p className="text-2xl font-bold text-blue-600">
              {applicationClusters.length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}; 