/**
 * Plan Overview Component
 * 
 * Displays high-level plan metrics and progress.
 */

import React from 'react';
import { Progress } from '@/components/ui/progress';
import type { AgentPlan } from './types';

interface PlanOverviewProps {
  agentPlan: AgentPlan;
}

const PlanOverview: React.FC<PlanOverviewProps> = ({ agentPlan }) => {
  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <p className="text-gray-600 mb-4">{agentPlan.description}</p>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600">{agentPlan.overall_progress}%</div>
          <div className="text-sm text-gray-600">Overall Progress</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600">{agentPlan.completed_tasks}</div>
          <div className="text-sm text-gray-600">Completed Tasks</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-orange-600">{agentPlan.human_input_required.length}</div>
          <div className="text-sm text-gray-600">Need Your Input</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-purple-600">{agentPlan.blocking_issues.length}</div>
          <div className="text-sm text-gray-600">Blocking Issues</div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">Plan Progress</span>
          <span className="text-sm text-gray-600">
            {agentPlan.completed_tasks} of {agentPlan.total_tasks} tasks completed
          </span>
        </div>
        <Progress value={agentPlan.overall_progress} className="h-3" />
      </div>
    </div>
  );
};

export default PlanOverview;