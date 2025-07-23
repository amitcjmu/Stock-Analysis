import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { TechDebtItem } from '@/services/discovery/techDebtAnalysisService';

interface TechDebtItemCardProps {
  item: TechDebtItem;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
  showCheckbox?: boolean;
}

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    default:
      return 'bg-green-100 text-green-800 border-green-200';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'end_of_life':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'deprecated':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'extended':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    default:
      return 'bg-green-100 text-green-800 border-green-200';
  }
};

const getEffortValue = (effort: string) => {
  switch (effort) {
    case 'low':
      return 25;
    case 'medium':
      return 50;
    case 'high':
      return 75;
    case 'complex':
      return 100;
    default:
      return 0;
  }
};

export const TechDebtItemCard: React.FC<TechDebtItemCardProps> = ({
  item,
  isSelected = false,
  onSelect,
  showCheckbox = true,
}) => {
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onSelect) {
      onSelect(item.id);
    }
  };

  return (
    <Card className={`overflow-hidden transition-all ${isSelected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              {showCheckbox && (
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={handleCheckboxChange}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  onClick={(e) => e.stopPropagation()}
                />
              )}
              <CardTitle className="text-lg font-medium">
                {item.assetName}
              </CardTitle>
            </div>
            <p className="text-sm text-muted-foreground">
              {item.technology} ({item.currentVersion})
              {item.latestVersion && ` → ${item.latestVersion}`}
            </p>
          </div>
          <div className="flex space-x-2">
            <Badge variant="outline" className={getStatusColor(item.supportStatus)}>
              {item.supportStatus.replace(/_/g, ' ')}
            </Badge>
            <Badge variant="outline" className={getRiskColor(item.securityRisk)}>
              {item.securityRisk} risk
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground">Migration Effort:</span>
              <span className="font-medium capitalize">{item.migrationEffort}</span>
            </div>
            <Progress
              value={getEffortValue(item.migrationEffort)}
              className="h-2"
            />
          </div>

          {item.businessImpact && (
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-muted-foreground">Business Impact:</span>
                <span className="font-medium capitalize">{item.businessImpact}</span>
              </div>
              <Progress
                value={getEffortValue(item.businessImpact)}
                className="h-2 bg-gray-200"
              />
            </div>
          )}

          <div className="text-sm">
            <p className="font-medium text-muted-foreground mb-1">
              Recommended Action:
            </p>
            <p className="text-foreground">{item.recommendedAction}</p>
          </div>

          {item.endOfLifeDate && (
            <div className="text-sm">
              <p className="font-medium text-muted-foreground mb-1">
                End of Life Date:
              </p>
              <p className="text-foreground">
                {new Date(item.endOfLifeDate).toLocaleDateString()}
              </p>
            </div>
          )}

          {item.dependencies && item.dependencies.length > 0 && (
            <div className="mt-2">
              <p className="text-sm font-medium text-muted-foreground mb-1">
                Dependencies:
              </p>
              <div className="flex flex-wrap gap-1">
                {item.dependencies.map((dep) => (
                  <Badge
                    key={dep}
                    variant="outline"
                    className="text-xs font-normal"
                  >
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
