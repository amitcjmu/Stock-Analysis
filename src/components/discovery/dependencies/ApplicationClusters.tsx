import React from 'react';

interface ApplicationCluster {
  id: string;
  name: string;
  applications: string[];
  complexity_score: number;
  migration_sequence: number;
}

interface ApplicationClustersProps {
  applicationClusters: ApplicationCluster[];
}

export const ApplicationClusters: React.FC<ApplicationClustersProps> = ({ 
  applicationClusters 
}) => {
  if (applicationClusters.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Application Clusters</h2>
      <p className="text-sm text-gray-600 mb-6">Groups of tightly coupled applications based on dependency analysis</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {applicationClusters.map((cluster) => (
          <div key={cluster.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="mb-3">
              <h3 className="font-medium text-gray-900">{cluster.name}</h3>
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{cluster.applications.length}</span> connected applications
              </div>
              <div className="text-sm text-gray-600">
                Complexity: <span className="font-medium">{cluster.complexity_score.toFixed(1)}</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-3">
                {cluster.applications.slice(0, 4).map((app, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    {app}
                  </span>
                ))}
                {cluster.applications.length > 4 && (
                  <span className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded">
                    +{cluster.applications.length - 4} more
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 