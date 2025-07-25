import React from 'react';
import { Progress } from '../../ui/progress';
import { Card } from '../../ui/card';
import type { DependencyData } from '../../../types/dependency';

interface DependencyProgressProps {
  data: DependencyData | null;
  isLoading: boolean;
}

const DependencyProgress: React.FC<DependencyProgressProps> = ({ data, isLoading }) => {
  if (!data) return null;

  const hostingRelationships = data?.app_server_mapping?.hosting_relationships || [];
  const crossAppDependencies = data?.cross_application_mapping?.cross_app_dependencies || [];

  const appServerProgress = hostingRelationships.length > 0 ?
    (hostingRelationships.filter(r => r?.status === 'confirmed').length / hostingRelationships.length) * 100 : 0;

  const appAppProgress = crossAppDependencies.length > 0 ?
    (crossAppDependencies.filter(d => d?.status === 'confirmed').length / crossAppDependencies.length) * 100 : 0;

  const totalProgress = (appServerProgress + appAppProgress) / 2;

  return (
    <Card className="p-4">
      <div className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium">App-Server Dependencies</h3>
            <span className="text-sm text-gray-500">
              {hostingRelationships.filter(r => r?.status === 'confirmed').length} of {hostingRelationships.length} confirmed
            </span>
          </div>
          <Progress value={appServerProgress} className="h-2" />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium">App-App Dependencies</h3>
            <span className="text-sm text-gray-500">
              {crossAppDependencies.filter(d => d?.status === 'confirmed').length} of {crossAppDependencies.length} confirmed
            </span>
          </div>
          <Progress value={appAppProgress} className="h-2" />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium">Overall Progress</h3>
            <span className="text-sm text-gray-500">{Math.round(totalProgress)}% Complete</span>
          </div>
          <Progress value={totalProgress} className="h-2" />
        </div>
      </div>
    </Card>
  );
};

export default DependencyProgress;
