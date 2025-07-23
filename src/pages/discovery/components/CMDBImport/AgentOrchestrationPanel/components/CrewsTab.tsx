import React from 'react';
import type { CrewProgress } from '../types';
import { CrewCard } from './CrewCard';

interface CrewsTabProps {
  crews: CrewProgress[];
}

export const CrewsTab: React.FC<CrewsTabProps> = ({ crews }) => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    {crews.map((crew, idx) => (
      <CrewCard key={idx} crew={crew} />
    ))}
  </div>
);