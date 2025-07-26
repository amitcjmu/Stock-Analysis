import React from 'react';
import { ArrowRight, Plus } from 'lucide-react';
import { Button } from '../../ui/button';

interface DependencyTableProps {
  type: 'app-server' | 'app-app';
  dependencies: unknown[];
  onReviewDependency: (dependency: unknown) => void;
  onAddDependency: () => void;
}

const getStrengthColor = (strength: string): any => {
  switch (strength?.toLowerCase()) {
    case 'critical':
      return 'bg-red-100 text-red-800';
    case 'high':
      return 'bg-orange-100 text-orange-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'low':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const DependencyTable: React.FC<DependencyTableProps> = ({
  type,
  dependencies,
  onReviewDependency,
  onAddDependency
}) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">
          {type === 'app-server' ? 'Application-Server Mappings' : 'Application Dependencies'}
        </h3>
        <Button onClick={onAddDependency} className="flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Add {type === 'app-server' ? 'Mapping' : 'Dependency'}</span>
        </Button>
      </div>

      {dependencies.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No dependencies found</p>
          <p className="text-sm text-gray-500">
            Add {type === 'app-server' ? 'application-server mappings' : 'application dependencies'} to track relationships
          </p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {type === 'app-server' ? 'Application' : 'Source App'}
                </th>
                <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-8">

                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {type === 'app-server' ? 'Server' : 'Target App'}
                </th>
                {type === 'app-app' && (
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                )}
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {type === 'app-server' ? 'Environment' : 'Strength'}
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dependencies.map((dep, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {type === 'app-server' ? dep.application_name : dep.source_app}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <ArrowRight className="h-4 w-4 text-gray-400 mx-auto" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {type === 'app-server' ? dep.server_name : dep.target_app}
                  </td>
                  {type === 'app-app' && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dep.dependency_type}
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStrengthColor(type === 'app-server' ? dep.environment : dep.strength)}`}>
                      {type === 'app-server' ? dep.environment : dep.strength}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {dep.confidence}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Button
                      variant="ghost"
                      onClick={() => onReviewDependency(dep)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Review
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
