/**
 * Human Input Tab Component
 * 
 * Displays tasks requiring human input with feedback options.
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle } from 'lucide-react';
import { AgentTask } from './types';
import { getPriorityColor } from './utils';

interface HumanInputTabProps {
  humanInputTasks: AgentTask[];
  onHumanInputSubmission: (taskId: string, input: unknown) => void;
}

const HumanInputTab: React.FC<HumanInputTabProps> = ({ 
  humanInputTasks, 
  onHumanInputSubmission 
}) => {
  if (humanInputTasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No human input required at this time</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {humanInputTasks.map((task) => (
        <div key={task.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
              <p className="text-sm text-gray-600">{task.task_description}</p>
            </div>
            <Badge className={getPriorityColor(task.priority)}>
              {task.priority}
            </Badge>
          </div>
          
          {task.human_feedback && (
            <div className="mt-3">
              <p className="text-sm font-medium text-orange-900 mb-2">
                {task.human_feedback.question}
              </p>
              <p className="text-xs text-orange-700 mb-3">
                Context: {task.human_feedback.context}
              </p>
              <div className="flex flex-wrap gap-2">
                {task.human_feedback.options.map((option, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => onHumanInputSubmission(task.id, { selected_option: option })}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default HumanInputTab;