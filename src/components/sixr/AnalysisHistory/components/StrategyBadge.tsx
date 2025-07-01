import React from 'react';
import { Badge } from '../../ui/badge';
import { strategyColors } from '../constants';

interface StrategyBadgeProps {
  strategy: string;
  className?: string;
}

export const StrategyBadge: React.FC<StrategyBadgeProps> = ({ strategy, className = '' }) => {
  const colorClass = strategyColors[strategy as keyof typeof strategyColors] || 'bg-gray-100 text-gray-800';
  
  return (
    <Badge className={`${colorClass} ${className}`}>
      {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
    </Badge>
  );
};