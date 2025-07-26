import React from 'react';
import { CheckCircle, XCircle, AlertCircle, ArrowRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

interface Criteria {
  current: number;
  required: number;
  met: boolean;
}

interface MigrationReadinessProps {
  readiness: {
    ready_for_assessment: number;
    needs_more_data: number;
    has_dependencies: number;
    needs_modernization: number;
    readiness_by_type: Record<string, {
      ready: number;
      total: number;
    }>;
  };
  totalAssets: number;
  className?: string;
}

const MigrationReadiness: React.FC<MigrationReadinessProps> = ({
  readiness,
  totalAssets,
  className = '',
}) => {
  const readinessPercentage = Math.round((readiness.ready_for_assessment / totalAssets) * 100) || 0;
  const readinessStatus = readinessPercentage >= 90 ? 'ready' : readinessPercentage >= 50 ? 'partial' : 'not-ready';

  const getStatusColor = (status: string): any => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-red-100 text-red-800';
    }
  };

  const getStatusText = (status: string): any => {
    switch (status) {
      case 'ready': return 'Ready for Migration';
      case 'partial': return 'Partially Ready';
      default: return 'Not Ready for Migration';
    }
  };

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'partial':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const readinessCriteria: Array<{ label: string; count: number; color: string }> = [
    {
      label: 'Ready for Assessment',
      count: readiness.ready_for_assessment,
      color: 'bg-green-500',
    },
    {
      label: 'Needs More Data',
      count: readiness.needs_more_data,
      color: 'bg-yellow-500',
    },
    {
      label: 'Has Dependencies',
      count: readiness.has_dependencies,
      color: 'bg-orange-500',
    },
    {
      label: 'Needs Modernization',
      count: readiness.needs_modernization,
      color: 'bg-red-500',
    },
  ];

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Migration Readiness</CardTitle>
            <CardDescription>
              {readinessStatus === 'ready'
                ? 'Your assets are ready for migration'
                : readinessStatus === 'partial'
                  ? 'Some assets need attention before migration'
                  : 'Your assets require significant work before migration'}
            </CardDescription>
          </div>
          <Badge className={`${getStatusColor(readinessStatus)}`}>
            {getStatusIcon(readinessStatus)}
            <span className="ml-1.5">{getStatusText(readinessStatus)}</span>
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Readiness Progress */}
          <div>
            <div className="flex justify-between text-sm font-medium mb-1">
              <span>Assets Ready for Migration</span>
              <span>{readiness.ready_for_assessment} / {totalAssets} ({readinessPercentage}%)</span>
            </div>
            <Progress value={readinessPercentage} className="h-2" />
          </div>

          {/* Readiness Breakdown */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Readiness Breakdown</h4>
            <div className="space-y-2">
              {readinessCriteria.map((item) => (
                <div key={item.label} className="flex items-center justify-between text-sm">
                  <div className="flex items-center">
                    <div
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-gray-700">{item.label}</span>
                  </div>
                  <span className="font-medium">
                    {item.count} ({Math.round((item.count / totalAssets) * 100)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Readiness by Type */}
          {Object.keys(readiness.readiness_by_type).length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Readiness by Asset Type</h4>
              <div className="space-y-2">
                {Object.entries(readiness.readiness_by_type).map(([type, stats]) => (
                  <div key={type} className="text-sm">
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-700 capitalize">{type}</span>
                      <span className="font-medium">
                        {Math.round((stats.ready / stats.total) * 100)}% ready
                      </span>
                    </div>
                    <Progress
                      value={(stats.ready / stats.total) * 100}
                      className="h-1.5"
                      indicatorClassName={
                        (stats.ready / stats.total) > 0.9
                          ? 'bg-green-500'
                          : (stats.ready / stats.total) > 0.5
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="bg-blue-50 p-3 rounded-md border border-blue-100">
            <h4 className="text-sm font-medium text-blue-800 mb-1">Improve Readiness</h4>
            <p className="text-xs text-blue-700 mb-2">
              {readinessStatus === 'ready'
                ? 'Your assets are well-prepared for migration. Consider optimizing further for cost savings.'
                : readinessStatus === 'partial'
                  ? 'Address the issues with non-ready assets to improve overall migration readiness.'
                  : 'Focus on the most critical assets first to improve migration readiness.'}
            </p>
            <Button variant="outline" size="sm" className="text-xs h-7">
              View Readiness Report
              <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MigrationReadiness;
