/**
 * QueueManagement Component
 * Extracted from ApplicationSelector.tsx for modularization
 */

import React from 'react';
import { Play, Pause, Trash2, Clock } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import type { QueueManagementProps, AnalysisQueue } from '../types/ApplicationSelectorTypes';

export const QueueManagement: React.FC<QueueManagementProps> = ({
  analysisQueues,
  applications,
  onQueueAction
}) => {
  const renderQueueItem = (queue: AnalysisQueue) => {
    const queueApplications = applications.filter(app => queue.applications.includes(app.id));
    
    return (
      <div key={queue.id} className="p-4 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="font-medium">{queue.name}</h4>
            <p className="text-sm text-gray-600">
              {queue.applications.length} applications • Created {queue.created_at.toLocaleDateString()}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={queue.status === 'completed' ? 'default' : 'secondary'}>
              {queue.status}
            </Badge>
            {onQueueAction && (
              <div className="flex space-x-1">
                {queue.status === 'pending' && (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => onQueueAction(queue.id, 'start')}
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                )}
                {queue.status === 'in_progress' && (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => onQueueAction(queue.id, 'pause')}
                  >
                    <Pause className="h-3 w-3" />
                  </Button>
                )}
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => onQueueAction(queue.id, 'cancel')}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {queueApplications.slice(0, 3).map(app => (
              <Badge key={app.id} variant="outline" className="text-xs">
                {app.name}
              </Badge>
            ))}
            {queueApplications.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{queueApplications.length - 3} more
              </Badge>
            )}
          </div>
          
          {queue.estimated_duration && (
            <div className="text-xs text-gray-500">
              Estimated duration: {Math.round(queue.estimated_duration / 60)} minutes
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {analysisQueues.map(renderQueueItem)}
      
      {analysisQueues.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No analysis queues found</p>
        </div>
      )}
    </div>
  );
};