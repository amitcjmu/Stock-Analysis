import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Server,
  Network,
  Database,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';

interface Application {
  id: string;
  name: string;
  confidence: number;
  validation_status: 'high_confidence' | 'medium_confidence' | 'needs_clarification';
  component_count: number;
  technology_stack: string[];
  environment: string;
  business_criticality: string;
  dependencies: {
    internal: string[];
    external: string[];
    infrastructure: string[];
  };
  components: Array<{
    name: string;
    asset_type: string;
    environment: string;
  }>;
  confidence_factors: {
    discovery_confidence: number;
    component_count: number;
    naming_clarity: number;
    dependency_clarity: number;
    technology_consistency: number;
  };
}

interface ApplicationListProps {
  applications: Application[];
  onApplicationSelect: (application: Application) => void;
  onEdit?: (application: Application) => void;
  onDelete?: (applicationId: string) => void;
}

export const ApplicationList: React.FC<ApplicationListProps> = ({
  applications,
  onApplicationSelect,
  onEdit,
  onDelete
}) => {
  const getConfidenceColor = (confidence: number): unknown => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'high_confidence': return 'default';
      case 'medium_confidence': return 'secondary';
      case 'needs_clarification': return 'destructive';
      default: return 'outline';
    }
  };

  const getCriticalityColor = (criticality: string): unknown => {
    switch (criticality.toLowerCase()) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getAssetIcon = (assetType: string): JSX.Element => {
    switch (assetType.toLowerCase()) {
      case 'server':
      case 'vm':
        return <Server className="h-4 w-4" />;
      case 'database':
        return <Database className="h-4 w-4" />;
      case 'network':
      case 'load_balancer':
        return <Network className="h-4 w-4" />;
      default:
        return <Server className="h-4 w-4" />;
    }
  };

  const formatConfidenceLabel = (status: string): unknown => {
    return status.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="space-y-4">
      {applications.map((app) => (
        <Card
          key={app.id}
          className="hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => onApplicationSelect(app)}
        >
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold mb-1">{app.name}</h3>
                <div className="flex gap-2 items-center">
                  <Badge variant={getConfidenceBadgeVariant(app.validation_status)}>
                    {formatConfidenceLabel(app.validation_status)}
                  </Badge>
                  <span className={`text-sm font-medium ${getCriticalityColor(app.business_criticality)}`}>
                    {app.business_criticality} Priority
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onApplicationSelect(app);
                  }}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                {onEdit && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(app);
                    }}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(app.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <span className="text-sm text-gray-600">Environment</span>
                <div className="font-medium">{app.environment}</div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Components</span>
                <div className="font-medium">{app.component_count}</div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Dependencies</span>
                <div className="font-medium">
                  {app.dependencies.internal.length +
                   app.dependencies.external.length +
                   app.dependencies.infrastructure.length}
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Confidence</span>
                <div className={`font-medium ${getConfidenceColor(app.confidence)}`}>
                  {Math.round(app.confidence * 100)}%
                </div>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex gap-2 flex-wrap mb-2">
                {app.technology_stack.slice(0, 5).map((tech, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {tech}
                  </Badge>
                ))}
                {app.technology_stack.length > 5 && (
                  <Badge variant="outline" className="text-xs">
                    +{app.technology_stack.length - 5} more
                  </Badge>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">Components:</span>
                  {app.components.slice(0, 3).map((comp, idx) => (
                    <div key={idx} className="flex items-center gap-1">
                      {getAssetIcon(comp.asset_type)}
                      <span className="text-xs">{comp.asset_type}</span>
                    </div>
                  ))}
                  {app.components.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{app.components.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Overall Discovery Confidence</span>
                <span className={`font-medium ${getConfidenceColor(app.confidence)}`}>
                  {Math.round(app.confidence * 100)}%
                </span>
              </div>
              <Progress
                value={app.confidence * 100}
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
