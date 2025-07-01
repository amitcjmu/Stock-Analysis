import React from 'react';
import { Badge } from '../../ui/badge';
import { statusColors } from '../constants';

interface StatusBadgeProps {
  status: 'completed' | 'in_progress' | 'failed' | 'archived';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const colorClass = statusColors[status] || 'bg-gray-100 text-gray-800';
  const displayText = status.replace('_', ' ').split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  return (
    <Badge className={`${colorClass} ${className}`}>
      {displayText}
    </Badge>
  );
};