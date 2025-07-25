/**
 * TaskHistoryRow Component
 * Extracted from AgentDetailPage.tsx for modularization
 */

import React from 'react';
import { Calendar, Brain, Zap, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Alert, AlertDescription } from '../../../components/ui/alert';
import type { TaskHistoryRowProps } from '../types/AgentDetailTypes';

export const TaskHistoryRow: React.FC<TaskHistoryRowProps> = ({ task, onViewDetails }) => {
  const statusColor = task.success ? 'text-green-600' : 'text-red-600';
  const statusIcon = task.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />;

  return (
    <div className="border-b border-gray-100 p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={statusColor}>{statusIcon}</span>
            <span className="font-medium text-gray-900">{task.taskName}</span>
            <Badge variant="secondary" className="text-xs">
              {task.duration.toFixed(1)}s
            </Badge>
            <Badge variant={task.confidenceScore > 0.8 ? 'default' : 'secondary'} className="text-xs">
              {(task.confidenceScore * 100).toFixed(0)}% confidence
            </Badge>
          </div>
          <div className="text-sm text-gray-600 mt-1">
            {task.resultPreview}
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(task.startedAt).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <Brain className="w-3 h-3" />
              {task.llmCallsCount} LLM calls
            </span>
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {task.tokenUsage.inputTokens + task.tokenUsage.outputTokens} tokens
            </span>
          </div>
          {task.errorMessage && (
            <Alert className="mt-2">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {task.errorMessage}
              </AlertDescription>
            </Alert>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetails(task.taskId)}
          className="ml-4"
        >
          View Details
        </Button>
      </div>
    </div>
  );
};
