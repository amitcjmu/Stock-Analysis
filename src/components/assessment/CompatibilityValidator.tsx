import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ComponentTreatment } from '@/hooks/useAssessmentFlow';
import { CheckCircle, AlertTriangle, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CompatibilityValidatorProps {
  treatments: ComponentTreatment[];
  onTreatmentChange: (componentName: string, treatment: Partial<ComponentTreatment>) => void;
}

export const CompatibilityValidator: React.FC<CompatibilityValidatorProps> = ({
  treatments,
  onTreatmentChange
}) => {
  const validatedComponents = treatments.filter(t => t.compatibility_validated);
  const invalidComponents = treatments.filter(t => !t.compatibility_validated);
  const componentsWithIssues = treatments.filter(t => t.compatibility_issues && t.compatibility_issues.length > 0);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Compatibility Summary</span>
          </CardTitle>
          <CardDescription>
            Overview of component compatibility validation status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{validatedComponents.length}</div>
              <div className="text-sm text-gray-600">Validated</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{invalidComponents.length}</div>
              <div className="text-sm text-gray-600">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{componentsWithIssues.length}</div>
              <div className="text-sm text-gray-600">With Issues</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Components with Issues */}
      {componentsWithIssues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>Components with Compatibility Issues</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {componentsWithIssues.map((treatment) => (
                <div key={treatment.component_name} className="p-3 border border-red-200 rounded-lg bg-red-50">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{treatment.component_name}</h4>
                    <Badge variant="destructive">{treatment.recommended_strategy}</Badge>
                  </div>
                  {treatment.compatibility_issues && (
                    <div className="space-y-1">
                      {treatment.compatibility_issues.map((issue, index) => (
                        <p key={index} className="text-sm text-red-700">
                          • {issue}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Components Status */}
      <Card>
        <CardHeader>
          <CardTitle>All Components</CardTitle>
          <CardDescription>
            Detailed compatibility status for each component
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {treatments.map((treatment) => (
              <div key={treatment.component_name} className={cn(
                "flex items-center justify-between p-3 border rounded-lg",
                treatment.compatibility_validated ? "border-green-200 bg-green-50" : "border-orange-200 bg-orange-50"
              )}>
                <div className="flex items-center space-x-3">
                  {treatment.compatibility_validated ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                  )}
                  <div>
                    <h4 className="font-medium text-gray-900">{treatment.component_name}</h4>
                    <p className="text-sm text-gray-600">{treatment.component_type}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">{treatment.recommended_strategy}</Badge>
                  <Badge variant={treatment.compatibility_validated ? "default" : "secondary"}>
                    {treatment.compatibility_validated ? "Validated" : "Pending"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
