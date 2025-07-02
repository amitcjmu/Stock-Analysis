import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SixRDecision, ArchitectureStandard } from '@/hooks/useAssessmentFlow';
import { Shield, AlertTriangle } from 'lucide-react';

interface ArchitectureExceptionsPanelProps {
  decision: SixRDecision;
  standards: ArchitectureStandard[];
  printMode?: boolean;
}

export const ArchitectureExceptionsPanel: React.FC<ArchitectureExceptionsPanelProps> = ({
  decision,
  standards,
  printMode = false
}) => {
  return (
    <Card className="print:shadow-none print:border-2">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Shield className="h-5 w-5" />
          <span>Architecture Compliance</span>
        </CardTitle>
        <CardDescription>
          Exceptions to engagement-level architecture standards
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {decision.architecture_exceptions.length === 0 ? (
          <div className="text-center py-6">
            <Shield className="h-8 w-8 mx-auto text-green-600 mb-2" />
            <p className="text-sm text-green-700 font-medium">Fully Compliant</p>
            <p className="text-xs text-gray-600">No architecture exceptions required</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-700">
                {decision.architecture_exceptions.length} Exception(s) Required
              </span>
            </div>
            
            <div className="space-y-2">
              {decision.architecture_exceptions.map((exception, index) => (
                <div key={index} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-sm text-orange-700">{exception}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Standards Summary */}
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Applied Standards</h4>
          <div className="grid grid-cols-2 gap-2">
            {standards.slice(0, 6).map((standard, index) => (
              <div key={index} className="flex items-center justify-between text-xs">
                <span className="text-gray-600 truncate">{standard.requirement_type}</span>
                <Badge variant={standard.mandatory ? "default" : "outline"} className="text-xs">
                  {standard.mandatory ? "Required" : "Optional"}
                </Badge>
              </div>
            ))}
            {standards.length > 6 && (
              <p className="text-xs text-gray-500 col-span-2">
                +{standards.length - 6} more standards
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};