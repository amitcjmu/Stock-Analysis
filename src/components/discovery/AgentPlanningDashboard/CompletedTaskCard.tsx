/**
 * Completed Task Card Component
 * 
 * Specialized card for displaying completed tasks.
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle } from 'lucide-react';
import { AgentTask } from './types';

interface CompletedTaskCardProps {
  task: AgentTask;
}

const CompletedTaskCard: React.FC<CompletedTaskCardProps> = ({ task }) => {
  return (
    <div className="border rounded-lg p-4 bg-green-50">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
        <Badge className="text-green-600 bg-green-100">completed</Badge>
      </div>
      <p className="text-sm text-gray-600 mb-2">{task.task_description}</p>
      <div className="text-xs text-gray-500">
        Completed: {task.completed_at ? new Date(task.completed_at).toLocaleString() : 'Unknown'}
        • Duration: {task.estimated_duration} minutes
      </div>
    </div>
  );
};

export default CompletedTaskCard;