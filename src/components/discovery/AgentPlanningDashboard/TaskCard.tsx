/**
 * Task Card Component
 * 
 * Renders individual task cards with status and progress.
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import type { AgentTask } from './types';
import { getStatusColor, getPriorityColor } from './utils';
import StatusIcon from './StatusIcon';

interface TaskCardProps {
  task: AgentTask;
  showProgress?: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, showProgress = true }) => {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <StatusIcon status={task.status} />
            <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
            <Badge className={getStatusColor(task.status)}>
              {task.status.replace('_', ' ')}
            </Badge>
            <Badge className={getPriorityColor(task.priority)}>
              {task.priority}
            </Badge>
          </div>
          <p className="text-sm text-gray-600 mb-2">{task.task_description}</p>
          {showProgress && task.progress > 0 && (
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${task.progress}%` }}
              />
            </div>
          )}
          <div className="text-xs text-gray-500">
            Estimated duration: {task.estimated_duration} minutes
            {task.dependencies.length > 0 && (
              <span className="ml-2">
                • Depends on: {task.dependencies.join(', ')}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskCard;