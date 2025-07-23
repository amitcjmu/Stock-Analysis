import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ApplicationComponent, ComponentTreatment } from '@/hooks/useAssessmentFlow';
import type { ArrowRight } from 'lucide-react'
import { Cpu, CheckCircle, AlertTriangle } from 'lucide-react'

interface ComponentBreakdownViewProps {
  components: ApplicationComponent[];
  treatments: ComponentTreatment[];
  printMode?: boolean;
}

export const ComponentBreakdownView: React.FC<ComponentBreakdownViewProps> = ({
  components,
  treatments,
  printMode = false
}) => {
  const getComponentTreatment = (componentName: string) => {
    return treatments.find(t => t.component_name === componentName);
  };

  const getStrategyColor = (strategy: string) => {
    const strategyColors: Record<string, string> = {
      'rehost': 'bg-green-100 text-green-700',
      'replatform': 'bg-blue-100 text-blue-700',
      'refactor': 'bg-purple-100 text-purple-700',
      'repurchase': 'bg-orange-100 text-orange-700',
      'retire': 'bg-gray-100 text-gray-700',
      'retain': 'bg-yellow-100 text-yellow-700'
    };
    return strategyColors[strategy] || 'bg-gray-100 text-gray-700';
  };

  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Cpu className="h-5 w-5" />
          <span>Component Breakdown</span>
        </CardTitle>
        <CardDescription>
          Detailed view of all application components and their treatment strategies
        </CardDescription>
      </CardHeader>
      <CardContent>
        {components.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Cpu className="h-8 w-8 mx-auto mb-2" />
            <p>No components identified</p>
          </div>
        ) : (
          <div className="space-y-4">
            {components.map((component) => {
              const treatment = getComponentTreatment(component.component_name);
              
              return (
                <div key={component.component_name} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-900">{component.component_name}</h4>
                      <p className="text-sm text-gray-600">{component.component_type}</p>
                    </div>
                    
                    {treatment && (
                      <div className="flex items-center space-x-2">
                        <Badge className={getStrategyColor(treatment.recommended_strategy)}>
                          {treatment.recommended_strategy}
                        </Badge>
                        {treatment.compatibility_validated ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-orange-600" />
                        )}
                      </div>
                    )}
                  </div>

                  {treatment && (
                    <div className="space-y-2">
                      <p className="text-sm text-gray-700">{treatment.rationale}</p>
                      
                      {treatment.compatibility_issues && treatment.compatibility_issues.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-red-700">Compatibility Issues:</p>
                          {treatment.compatibility_issues.map((issue, index) => (
                            <p key={index} className="text-xs text-red-600 bg-red-50 p-1 rounded">
                              • {issue}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {component.dependencies && component.dependencies.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs font-medium text-gray-700 mb-1">Dependencies:</p>
                      <div className="flex flex-wrap gap-1">
                        {component.dependencies.map((dep, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {dep}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {component.technology_stack && Object.keys(component.technology_stack).length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">Technology Stack:</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(component.technology_stack).map(([key, value]) => (
                          <Badge key={key} variant="secondary" className="text-xs">
                            {key}: {value as string}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};