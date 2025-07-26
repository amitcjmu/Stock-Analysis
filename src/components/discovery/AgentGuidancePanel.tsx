/**
 * Agent Guidance Panel - Displays Flow Processing Agent guidance and checklist status
 *
 * This component shows users exactly what the Flow Processing Agent determined
 * and provides clear next steps for flow continuation.
 */

import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Brain,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Target,
  ListChecks,
  Lightbulb,
  ArrowRight
} from 'lucide-react';

interface TaskResult {
  task_id: string;
  task_name: string;
  status: 'completed' | 'pending' | 'blocked' | 'not_started';
  confidence: number;
  next_steps: string[];
}

interface PhaseChecklistResult {
  phase: string;
  status: 'completed' | 'in_progress' | 'pending' | 'blocked';
  completion_percentage: number;
  tasks: TaskResult[];
  next_required_actions: string[];
}

interface UserGuidance {
  summary: string;
  phase: string;
  completion_percentage: number;
  next_steps: string[];
  detailed_status: {
    completed_tasks: Array<{ name: string; confidence: number }>;
    pending_tasks: Array<{ name: string; next_steps: string[] }>;
  };
}

interface AgentGuidancePanelProps {
  guidance: UserGuidance;
  checklistStatus: PhaseChecklistResult[];
  flowId: string;
  onDismiss?: () => void;
  className?: string;
}

const AgentGuidancePanel: React.FC<AgentGuidancePanelProps> = ({
  guidance,
  checklistStatus,
  flowId,
  onDismiss,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showDetailedChecklist, setShowDetailedChecklist] = useState(false);

  const getTaskStatusIcon = (status: TaskResult['status']): JSX.Element => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'blocked':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string): any => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'blocked':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const currentPhase = checklistStatus.find(phase => phase.phase === guidance.phase);

  return (
    <Card className={`border-l-4 border-l-blue-500 bg-gradient-to-r from-blue-50 to-white ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
              <Brain className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">
                🤖 Flow Processing Agent Analysis
              </CardTitle>
              <CardDescription className="text-sm text-gray-600">
                AI-powered flow continuation guidance for {flowId.slice(0, 8)}...
              </CardDescription>
            </div>
          </div>
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Main Guidance Summary */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-3">
            <Target className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-blue-900 mb-1">Current Analysis</h4>
              <p className="text-blue-800 text-sm leading-relaxed">
                {guidance.summary}
              </p>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        {currentPhase && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">
                {guidance.phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Progress
              </span>
              <span className="text-gray-600">
                {currentPhase.completion_percentage.toFixed(0)}% complete
              </span>
            </div>
            <Progress value={currentPhase.completion_percentage} className="h-2" />
          </div>
        )}

        {/* Next Steps */}
        {guidance.next_steps.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-600" />
              <h4 className="font-medium text-gray-900">Recommended Next Steps</h4>
            </div>
            <div className="space-y-2">
              {guidance.next_steps.map((step, index) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <div className="flex items-center justify-center w-6 h-6 bg-amber-100 rounded-full text-xs font-medium text-amber-700">
                    {index + 1}
                  </div>
                  <p className="text-amber-800 text-sm leading-relaxed">
                    {step}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Task Status Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-900">Completed</span>
            </div>
            <p className="text-2xl font-bold text-green-700">
              {guidance.detailed_status.completed_tasks.length}
            </p>
            <p className="text-xs text-green-600">tasks done</p>
          </div>

          <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="h-4 w-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-900">Pending</span>
            </div>
            <p className="text-2xl font-bold text-yellow-700">
              {guidance.detailed_status.pending_tasks.length}
            </p>
            <p className="text-xs text-yellow-600">tasks remaining</p>
          </div>
        </div>

        {/* Detailed Checklist (Collapsible) */}
        <Collapsible open={showDetailedChecklist} onOpenChange={setShowDetailedChecklist}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-3 h-auto">
              <div className="flex items-center gap-2">
                <ListChecks className="h-4 w-4" />
                <span className="font-medium">Detailed Task Checklist</span>
              </div>
              {showDetailedChecklist ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>

          <CollapsibleContent className="space-y-3 mt-3">
            {/* Completed Tasks */}
            {guidance.detailed_status.completed_tasks.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-green-900 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Completed Tasks
                </h5>
                {guidance.detailed_status.completed_tasks.map((task, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-green-50 rounded border border-green-200">
                    <span className="text-sm text-green-800">{task.name}</span>
                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                      {(task.confidence * 100).toFixed(0)}% confidence
                    </Badge>
                  </div>
                ))}
              </div>
            )}

            {/* Pending Tasks */}
            {guidance.detailed_status.pending_tasks.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-yellow-900 flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Pending Tasks
                </h5>
                {guidance.detailed_status.pending_tasks.map((task, index) => (
                  <div key={index} className="p-3 bg-yellow-50 rounded border border-yellow-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-800">{task.name}</span>
                      <Badge variant="outline" className="text-xs border-yellow-300 text-yellow-700">
                        Action Required
                      </Badge>
                    </div>
                    {task.next_steps.length > 0 && (
                      <div className="space-y-1">
                        {task.next_steps.map((step, stepIndex) => (
                          <div key={stepIndex} className="flex items-start gap-2 text-xs text-yellow-700">
                            <ArrowRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CollapsibleContent>
        </Collapsible>

        {/* Agent Confidence Footer */}
        <div className="pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Analysis completed by Flow Processing Agent</span>
            <span>Confidence: {guidance.completion_percentage.toFixed(0)}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AgentGuidancePanel;
