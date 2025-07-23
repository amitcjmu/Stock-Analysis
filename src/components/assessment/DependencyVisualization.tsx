import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ApplicationComponent } from '@/hooks/useAssessmentFlow';
import { Network, ArrowRight } from 'lucide-react';

interface DependencyVisualizationProps {
  components: ApplicationComponent[];
  applicationId: string;
  printMode?: boolean;
}

export const DependencyVisualization: React.FC<DependencyVisualizationProps> = ({
  components,
  applicationId,
  printMode = false
}) => {
  // Extract all unique dependencies
  const allDependencies = Array.from(new Set(
    components.flatMap(c => c.dependencies || [])
  ));

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Network className="h-5 w-5" />
          <span>Dependency Mapping</span>
        </CardTitle>
        <CardDescription>
          Component dependencies and external integrations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {allDependencies.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Network className="h-8 w-8 mx-auto mb-2" />
            <p>No dependencies identified</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Dependency Summary */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-blue-900">
                  Total Dependencies
                </span>
                <Badge variant="outline">
                  {allDependencies.length}
                </Badge>
              </div>
            </div>

            {/* Component Dependencies */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">Component Dependencies</h4>
              {components.map((component) => (
                <div key={component.component_name} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium text-gray-900">{component.component_name}</h5>
                    <Badge variant="outline">{component.component_type}</Badge>
                  </div>
                  
                  {component.dependencies && component.dependencies.length > 0 ? (
                    <div className="space-y-1">
                      {component.dependencies.map((dep, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm">
                          <ArrowRight className="h-3 w-3 text-gray-400" />
                          <span className="text-gray-600">{dep}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No dependencies</p>
                  )}
                </div>
              ))}
            </div>

            {/* Unique Dependencies List */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">All Dependencies</h4>
              <div className="flex flex-wrap gap-1">
                {allDependencies.map((dep, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};