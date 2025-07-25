import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Clock, Zap, Filter } from 'lucide-react';
import { cn } from '@/lib/utils';

type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'all';

interface SeverityFilterProps {
  selectedSeverity: SeverityLevel;
  onSeverityChange: (severity: SeverityLevel) => void;
  counts: {
    all: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

const SEVERITY_OPTIONS = [
  {
    value: 'all' as const,
    label: 'All Issues',
    color: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
    icon: Filter
  },
  {
    value: 'critical' as const,
    label: 'Critical',
    color: 'bg-red-100 text-red-700 hover:bg-red-200',
    icon: AlertTriangle
  },
  {
    value: 'high' as const,
    label: 'High',
    color: 'bg-orange-100 text-orange-700 hover:bg-orange-200',
    icon: AlertTriangle
  },
  {
    value: 'medium' as const,
    label: 'Medium',
    color: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200',
    icon: Clock
  },
  {
    value: 'low' as const,
    label: 'Low',
    color: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
    icon: Zap
  }
];

export const SeverityFilter: React.FC<SeverityFilterProps> = ({
  selectedSeverity,
  onSeverityChange,
  counts
}) => {
  return (
    <div className="flex flex-wrap gap-2">
      {SEVERITY_OPTIONS.map((option) => {
        const Icon = option.icon;
        const count = counts[option.value];
        const isSelected = selectedSeverity === option.value;

        return (
          <Button
            key={option.value}
            variant={isSelected ? "default" : "outline"}
            size="sm"
            onClick={() => onSeverityChange(option.value)}
            className={cn(
              "flex items-center space-x-2",
              !isSelected && option.color
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{option.label}</span>
            <Badge
              variant={isSelected ? "secondary" : "outline"}
              className="ml-1 h-5 px-1.5 text-xs"
            >
              {count}
            </Badge>
          </Button>
        );
      })}
    </div>
  );
};
