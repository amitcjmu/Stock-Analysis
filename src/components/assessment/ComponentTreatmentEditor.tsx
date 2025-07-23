import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ComponentTreatment } from '@/hooks/useAssessmentFlow';
import { Cpu, CheckCircle, AlertTriangle } from 'lucide-react';

interface ComponentTreatmentEditorProps {
  treatments: ComponentTreatment[];
  onTreatmentChange: (componentName: string, treatment: Partial<ComponentTreatment>) => void;
  editingComponent: string | null;
  onEditComponent: (componentName: string | null) => void;
  bulkEditMode: boolean;
  selectedComponents: string[];
  onSelectionChange: (selected: string[]) => void;
}

export const ComponentTreatmentEditor: React.FC<ComponentTreatmentEditorProps> = ({
  treatments,
  onTreatmentChange,
  editingComponent,
  onEditComponent,
  bulkEditMode,
  selectedComponents,
  onSelectionChange
}) => {
  return (
    <div className="space-y-4">
      {treatments.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <Cpu className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Components Found</h3>
            <p className="text-gray-600">
              Component treatments will appear here after technical debt analysis is complete.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {treatments.map((treatment) => (
            <Card key={treatment.component_name} className="hover:shadow-sm transition-shadow">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center justify-between">
                  <span className="truncate">{treatment.component_name}</span>
                  <div className="flex items-center space-x-1">
                    {treatment.compatibility_validated ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                    )}
                  </div>
                </CardTitle>
                <CardDescription>{treatment.component_type}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Badge variant="outline">
                    {treatment.recommended_strategy}
                  </Badge>
                </div>
                
                <p className="text-sm text-gray-600">{treatment.rationale}</p>
                
                {treatment.compatibility_issues && treatment.compatibility_issues.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-red-700">Compatibility Issues:</p>
                    {treatment.compatibility_issues.map((issue, index) => (
                      <p key={index} className="text-xs text-red-600 bg-red-50 p-1 rounded">
                        {issue}
                      </p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};