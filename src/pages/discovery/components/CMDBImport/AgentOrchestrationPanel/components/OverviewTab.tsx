import React from 'react';
import { Progress } from '@/components/ui/progress';
import { CrewProgress } from '../types';
import { getStatusIconWithStyles, getIconContainerStyles } from '../utils';

interface OverviewTabProps {
  crews: CrewProgress[];
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ crews }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {crews.map((crew, idx) => (
      <div key={idx} className="flex items-center gap-4 p-4 border rounded-lg">
        <div className={`p-2 rounded-lg ${getIconContainerStyles(crew.status)}`}>
          {crew.icon}
        </div>
        <div className="flex-1">
          <h4 className="font-medium">{crew.name}</h4>
          <p className="text-sm text-gray-600">{crew.currentTask}</p>
          <Progress value={crew.progress} className="h-1 mt-2" />
        </div>
        {getStatusIconWithStyles(crew.status)}
      </div>
    ))}
  </div>
);