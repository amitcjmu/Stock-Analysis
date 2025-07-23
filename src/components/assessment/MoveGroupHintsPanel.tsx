import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { Badge } from '@/components/ui/badge';
import type { SixRDecision } from '@/hooks/useAssessmentFlow';
import { Users, ArrowRight, Calendar } from 'lucide-react';

interface MoveGroupHintsPanelProps {
  decision: SixRDecision;
  onDecisionChange: (updates: Partial<SixRDecision>) => void;
}

export const MoveGroupHintsPanel: React.FC<MoveGroupHintsPanelProps> = ({
  decision,
  onDecisionChange
}) => {
  const moveGroupHints = decision.move_group_hints || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Move Group Recommendations</span>
          </CardTitle>
          <CardDescription>
            AI-generated suggestions for migration wave planning and dependency grouping
          </CardDescription>
        </CardHeader>
        <CardContent>
          {moveGroupHints.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Calendar className="h-8 w-8 mx-auto mb-2" />
              <p>No move group hints available yet</p>
              <p className="text-sm">Hints will be generated during strategy analysis</p>
            </div>
          ) : (
            <div className="space-y-3">
              {moveGroupHints.map((hint, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <ArrowRight className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-blue-800">{hint}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Planning Integration Info */}
      <Card>
        <CardHeader>
          <CardTitle>Planning Integration</CardTitle>
          <CardDescription>
            How these hints will be used in migration planning
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start space-x-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p>Move group hints help determine which applications should be migrated together</p>
            </div>
            <div className="flex items-start space-x-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p>Dependencies and shared infrastructure drive grouping recommendations</p>
            </div>
            <div className="flex items-start space-x-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
              <p>Risk levels and complexity influence wave sequencing</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};