import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import {
  CheckCircle,
  AlertCircle,
  Server,
  Database,
  Network,
  ArrowRight,
  X
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

interface ApplicationDetailsProps {
  application: Application;
  onClose: () => void;
  onValidate?: (validationType: string) => void;
}

export const ApplicationDetails: React.FC<ApplicationDetailsProps> = ({
  application,
  onClose,
  onValidate
}) => {
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

  const getConfidenceColor = (value: number): any => {
    if (value >= 0.8) return 'text-green-600';
    if (value >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{application.name} - Detailed View</CardTitle>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="components">Components</TabsTrigger>
            <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
            <TabsTrigger value="confidence">Confidence</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Environment</label>
                <p className="text-lg">{application.environment}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Business Criticality</label>
                <p className="text-lg">{application.business_criticality}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Total Components</label>
                <p className="text-lg">{application.component_count}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Validation Status</label>
                <p className="text-lg">{application.validation_status.replace('_', ' ')}</p>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-600">Technology Stack</label>
              <div className="flex flex-wrap gap-2 mt-2">
                {application.technology_stack.map((tech, idx) => (
                  <Badge key={idx} variant="secondary">{tech}</Badge>
                ))}
              </div>
            </div>

            {onValidate && application.validation_status !== 'high_confidence' && (
              <div className="flex gap-2 mt-4">
                <Button
                  onClick={() => onValidate('approve')}
                  className="flex items-center gap-2"
                >
                  <CheckCircle className="h-4 w-4" />
                  Approve Configuration
                </Button>
                <Button
                  onClick={() => onValidate('modify')}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <AlertCircle className="h-4 w-4" />
                  Request Changes
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="components" className="space-y-4">
            <div className="space-y-2">
              {application.components.map((component, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getAssetIcon(component.asset_type)}
                    <div>
                      <p className="font-medium">{component.name}</p>
                      <p className="text-sm text-gray-600">
                        {component.asset_type} • {component.environment}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="dependencies" className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Internal Dependencies ({application.dependencies.internal.length})</h4>
              <div className="space-y-1">
                {application.dependencies.internal.map((dep, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <ArrowRight className="h-3 w-3" />
                    <span>{dep}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">External Dependencies ({application.dependencies.external.length})</h4>
              <div className="space-y-1">
                {application.dependencies.external.map((dep, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <ArrowRight className="h-3 w-3" />
                    <span>{dep}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Infrastructure Dependencies ({application.dependencies.infrastructure.length})</h4>
              <div className="space-y-1">
                {application.dependencies.infrastructure.map((dep, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <ArrowRight className="h-3 w-3" />
                    <span>{dep}</span>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="confidence" className="space-y-4">
            <div className="space-y-3">
              {Object.entries(application.confidence_factors).map(([factor, value]) => (
                <div key={factor}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm capitalize">
                      {factor.replace(/_/g, ' ')}
                    </span>
                    <span className={`text-sm font-medium ${getConfidenceColor(value)}`}>
                      {Math.round(value * 100)}%
                    </span>
                  </div>
                  <Progress value={value * 100} className="h-2" />
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="font-medium">Overall Confidence</span>
                <span className={`text-lg font-bold ${getConfidenceColor(application.confidence)}`}>
                  {Math.round(application.confidence * 100)}%
                </span>
              </div>
              <Progress
                value={application.confidence * 100}
                className="h-3 mt-2"
              />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
