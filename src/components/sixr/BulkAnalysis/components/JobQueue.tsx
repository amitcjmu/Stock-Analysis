import React from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react'
import { Play, Pause, Square, RotateCcw, Eye, Trash2, Clock, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../ui/card';
import { Button } from '../../../ui/button';
import { Badge } from '../../../ui/badge';
import { Progress } from '../../../ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../ui/table';
import { Checkbox } from '../../../ui/checkbox';
import type { BulkAnalysisJob } from '../types';
import { statusColors, priorityColors, formatDuration, getStatusIcon, getPriorityIcon } from '../utils/analysisUtils';

interface JobQueueProps {
  jobs: BulkAnalysisJob[];
  selectedJobs: string[];
  queueStats: {
    runningJobs: number;
    pendingJobs: number;
    totalApplicationsInQueue: number;
    estimatedTimeRemaining: number;
    canStartMore: boolean;
  };
  onSelectJob: (jobId: string) => void;
  onSelectAll: () => void;
  onStartJob: (jobId: string) => void;
  onPauseJob: (jobId: string) => void;
  onCancelJob: (jobId: string) => void;
  onRetryJob: (jobId: string) => void;
  onDeleteJob: (jobId: string) => void;
  onViewResults: (jobId: string) => void;
}

export const JobQueue: React.FC<JobQueueProps> = ({
  jobs,
  selectedJobs,
  queueStats,
  onSelectJob,
  onSelectAll,
  onStartJob,
  onPauseJob,
  onCancelJob,
  onRetryJob,
  onDeleteJob,
  onViewResults
}) => {
  const getActionButtons = (job: BulkAnalysisJob) => {
    const buttons = [];

    switch (job.status) {
      case 'pending':
        if (queueStats.canStartMore) {
          buttons.push(
            <Button
              key="start"
              size="sm"
              variant="outline"
              onClick={() => onStartJob(job.id)}
              className="h-8 px-2"
            >
              <Play className="h-3 w-3" />
            </Button>
          );
        }
        break;

      case 'running':
        buttons.push(
          <Button
            key="pause"
            size="sm"
            variant="outline"
            onClick={() => onPauseJob(job.id)}
            className="h-8 px-2"
          >
            <Pause className="h-3 w-3" />
          </Button>
        );
        break;

      case 'paused':
        if (queueStats.canStartMore) {
          buttons.push(
            <Button
              key="resume"
              size="sm"
              variant="outline"
              onClick={() => onStartJob(job.id)}
              className="h-8 px-2"
            >
              <Play className="h-3 w-3" />
            </Button>
          );
        }
        break;

      case 'failed':
        buttons.push(
          <Button
            key="retry"
            size="sm"
            variant="outline"
            onClick={() => onRetryJob(job.id)}
            className="h-8 px-2"
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
        );
        break;

      case 'completed':
        buttons.push(
          <Button
            key="view"
            size="sm"
            variant="outline"
            onClick={() => onViewResults(job.id)}
            className="h-8 px-2"
          >
            <Eye className="h-3 w-3" />
          </Button>
        );
        break;
    }

    // Cancel button for running/paused jobs
    if (job.status === 'running' || job.status === 'paused') {
      buttons.push(
        <Button
          key="cancel"
          size="sm"
          variant="outline"
          onClick={() => onCancelJob(job.id)}
          className="h-8 px-2 text-red-600 hover:text-red-700"
        >
          <Square className="h-3 w-3" />
        </Button>
      );
    }

    // Delete button for completed/failed/cancelled jobs
    if (['completed', 'failed', 'cancelled'].includes(job.status)) {
      buttons.push(
        <Button
          key="delete"
          size="sm"
          variant="outline"
          onClick={() => onDeleteJob(job.id)}
          className="h-8 px-2 text-red-600 hover:text-red-700"
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      );
    }

    return buttons;
  };

  return (
    <div className="space-y-6">
      {/* Queue Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Running Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{queueStats.runningJobs}</div>
            <p className="text-xs text-gray-600">Currently processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{queueStats.pendingJobs}</div>
            <p className="text-xs text-gray-600">Waiting in queue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Applications in Queue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{queueStats.totalApplicationsInQueue}</div>
            <p className="text-xs text-gray-600">To be processed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Est. Time Remaining</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {formatDuration(queueStats.estimatedTimeRemaining)}
            </div>
            <p className="text-xs text-gray-600">For pending jobs</p>
          </CardContent>
        </Card>
      </div>

      {/* Job Table */}
      <Card>
        <CardHeader>
          <CardTitle>Job Queue</CardTitle>
          <CardDescription>
            Manage bulk analysis jobs and monitor their progress
          </CardDescription>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Jobs in Queue</h3>
              <p className="text-gray-600">Create your first bulk analysis job to get started.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedJobs.length === jobs.length}
                      onCheckedChange={onSelectAll}
                    />
                  </TableHead>
                  <TableHead>Job Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Applications</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedJobs.includes(job.id)}
                        onCheckedChange={() => onSelectJob(job.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{job.name}</div>
                        {job.description && (
                          <div className="text-sm text-gray-600">{job.description}</div>
                        )}
                        <div className="text-xs text-gray-500">
                          Created: {job.created_at.toLocaleDateString()}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[job.status]}>
                        {getStatusIcon(job.status)} {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={priorityColors[job.priority]}>
                        {getPriorityIcon(job.priority)} {job.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div>{job.completed_applications}/{job.total_applications}</div>
                        {job.failed_applications > 0 && (
                          <div className="text-red-600">{job.failed_applications} failed</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <Progress value={job.progress} className="h-2" />
                        <div className="text-xs text-gray-600">{job.progress}%</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {job.status === 'running' && job.started_at && (
                          <div className="flex items-center space-x-1">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>
                              {formatDuration(
                                (new Date().getTime() - job.started_at.getTime()) / (1000 * 60)
                              )}
                            </span>
                          </div>
                        )}
                        {job.actual_duration && (
                          <div>{formatDuration(job.actual_duration)}</div>
                        )}
                        {!job.actual_duration && job.status === 'pending' && (
                          <div className="text-gray-500">
                            Est: {formatDuration(job.estimated_duration)}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        {getActionButtons(job)}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};