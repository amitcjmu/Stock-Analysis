import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { LucideIcon } from 'lucide-react';

interface ClassificationCardProps {
  type: string;
  label: string;
  count: number;
  Icon: LucideIcon;
  color: string;
  isActive: boolean;
  onClick: () => void;
}

export const ClassificationCard: React.FC<ClassificationCardProps> = ({
  type,
  label,
  count,
  Icon,
  color,
  isActive,
  onClick
}) => {
  return (
    <Card 
      className={`cursor-pointer transition-all ${
        isActive ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
      }`}
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-lg bg-${color}-50`}>
            <Icon className={`h-6 w-6 text-${color}-600`} />
          </div>
          <Badge variant={isActive ? 'default' : 'secondary'}>
            {count}
          </Badge>
        </div>
        <h3 className="font-semibold text-lg">{label}</h3>
        <p className="text-sm text-gray-600 mt-1">
          {count} {type} discovered
        </p>
      </CardContent>
    </Card>
  );
};