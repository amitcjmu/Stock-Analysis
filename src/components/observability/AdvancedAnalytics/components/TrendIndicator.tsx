/**
 * Trend Indicator Component
 * Shows trend direction and rate of change
 */

import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

interface TrendIndicatorProps {
  trend: 'improving' | 'declining' | 'stable';
  rate: number;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ trend, rate }) => {
  const icons = {
    improving: <TrendingUp className="w-4 h-4 text-green-500" />,
    declining: <TrendingDown className="w-4 h-4 text-red-500" />,
    stable: <Activity className="w-4 h-4 text-gray-500" />
  };

  const colors = {
    improving: 'text-green-600 bg-green-100',
    declining: 'text-red-600 bg-red-100',
    stable: 'text-gray-600 bg-gray-100'
  };

  return (
    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${colors[trend]}`}>
      {icons[trend]}
      <span>{trend}</span>
      {rate !== 0 && <span>({Math.abs(rate).toFixed(1)}%)</span>}
    </div>
  );
};

export default TrendIndicator;