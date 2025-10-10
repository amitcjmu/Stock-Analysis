/**
 * Phase Timeline Component
 *
 * Visual timeline showing collection flow phases and their progression
 */

import React from 'react';
import { CheckCircle2, Circle, Clock, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface PhaseInfo {
  id: string;
  name: string;
  display_name: string;
  description: string;
  status: 'completed' | 'current' | 'upcoming' | 'skipped';
  started_at?: string;
  completed_at?: string;
  requires_user_input?: boolean;
}

export interface PhaseTimelineProps {
  phases: PhaseInfo[];
  currentPhase?: string;
  className?: string;
}

const COLLECTION_PHASES = [
  {
    id: 'initialization',
    display_name: 'Initialization',
    description: 'Flow setup and configuration'
  },
  {
    id: 'asset_selection',
    display_name: 'Asset Selection',
    description: 'Select assets for collection'
  },
  {
    id: 'gap_analysis',
    display_name: 'Gap Analysis',
    description: 'Analyze data gaps'
  },
  {
    id: 'questionnaire_generation',
    display_name: 'Form Generation',
    description: 'Generate collection forms'
  },
  {
    id: 'manual_collection',
    display_name: 'Data Collection',
    description: 'Collect application data'
  },
  {
    id: 'data_validation',
    display_name: 'Validation',
    description: 'Validate collected data'
  },
  {
    id: 'finalization',
    display_name: 'Finalization',
    description: 'Complete and finalize'
  }
];

const getPhaseIcon = (status: PhaseInfo['status']) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    case 'current':
      return <Clock className="h-5 w-5 text-blue-600 animate-pulse" />;
    case 'skipped':
      return <AlertCircle className="h-5 w-5 text-yellow-600" />;
    default:
      return <Circle className="h-5 w-5 text-gray-300" />;
  }
};

const getPhaseColor = (status: PhaseInfo['status']) => {
  switch (status) {
    case 'completed':
      return 'border-green-500 bg-green-50';
    case 'current':
      return 'border-blue-500 bg-blue-50 shadow-md';
    case 'skipped':
      return 'border-yellow-500 bg-yellow-50';
    default:
      return 'border-gray-200 bg-gray-50';
  }
};

export const PhaseTimeline: React.FC<PhaseTimelineProps> = ({
  phases,
  currentPhase,
  className = ''
}) => {
  // Merge backend phases with default phase order
  const phaseOrder = COLLECTION_PHASES.map(defaultPhase => {
    const backendPhase = phases.find(p => p.id === defaultPhase.id);

    let status: PhaseInfo['status'] = 'upcoming';
    if (backendPhase) {
      status = backendPhase.status;
    } else if (currentPhase) {
      const currentIndex = COLLECTION_PHASES.findIndex(p => p.id === currentPhase);
      const phaseIndex = COLLECTION_PHASES.findIndex(p => p.id === defaultPhase.id);
      if (phaseIndex < currentIndex) {
        status = 'completed';
      } else if (phaseIndex === currentIndex) {
        status = 'current';
      }
    }

    return {
      ...defaultPhase,
      name: defaultPhase.id,
      status,
      ...(backendPhase || {})
    };
  });

  const currentPhaseIndex = phaseOrder.findIndex(p => p.status === 'current');
  const completedCount = phaseOrder.filter(p => p.status === 'completed').length;
  const progressPercentage = Math.round((completedCount / phaseOrder.length) * 100);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Phase Timeline</CardTitle>
          <Badge variant="outline" className="text-sm">
            {completedCount}/{phaseOrder.length} Complete ({progressPercentage}%)
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {phaseOrder.map((phase, index) => {
            const isLast = index === phaseOrder.length - 1;
            const isActive = phase.status === 'current';

            return (
              <div key={phase.id} className="relative">
                {/* Connecting Line */}
                {!isLast && (
                  <div
                    className={cn(
                      'absolute left-[10px] top-[28px] w-0.5 h-[calc(100%+4px)]',
                      phase.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'
                    )}
                  />
                )}

                {/* Phase Card */}
                <div
                  className={cn(
                    'relative flex items-start gap-3 p-3 rounded-lg border-2 transition-all',
                    getPhaseColor(phase.status),
                    isActive && 'ring-2 ring-blue-300'
                  )}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-0.5 relative z-10 bg-white rounded-full">
                    {getPhaseIcon(phase.status)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className={cn(
                          'font-medium text-sm',
                          isActive && 'text-blue-900',
                          phase.status === 'completed' && 'text-green-900',
                          phase.status === 'upcoming' && 'text-muted-foreground'
                        )}>
                          {phase.display_name}
                        </h4>
                        <p className={cn(
                          'text-xs mt-0.5',
                          isActive && 'text-blue-700',
                          phase.status === 'completed' && 'text-green-700',
                          phase.status === 'upcoming' && 'text-muted-foreground'
                        )}>
                          {phase.description}
                        </p>
                      </div>

                      {/* Status Badge */}
                      <Badge
                        variant={
                          phase.status === 'completed' ? 'outline' :
                          phase.status === 'current' ? 'default' :
                          'secondary'
                        }
                        className={cn(
                          'text-xs',
                          phase.status === 'completed' && 'bg-green-50 text-green-700 border-green-300',
                          phase.status === 'current' && 'bg-blue-600',
                          phase.status === 'skipped' && 'bg-yellow-50 text-yellow-700 border-yellow-300'
                        )}
                      >
                        {phase.status === 'current' ? 'In Progress' :
                         phase.status === 'completed' ? 'Done' :
                         phase.status === 'skipped' ? 'Skipped' :
                         'Pending'}
                      </Badge>
                    </div>

                    {/* Timestamps */}
                    {(phase.started_at || phase.completed_at) && (
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        {phase.started_at && (
                          <span>
                            Started: {new Date(phase.started_at).toLocaleString()}
                          </span>
                        )}
                        {phase.completed_at && (
                          <span>
                            Completed: {new Date(phase.completed_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    )}

                    {/* User Input Required */}
                    {phase.requires_user_input && phase.status === 'current' && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                        <AlertCircle className="h-3 w-3" />
                        <span>Requires user input</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Current Phase Summary */}
        {currentPhaseIndex >= 0 && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-900">
              Currently in: {phaseOrder[currentPhaseIndex].display_name}
            </p>
            <p className="text-xs text-blue-700 mt-1">
              {phaseOrder[currentPhaseIndex].description}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PhaseTimeline;
