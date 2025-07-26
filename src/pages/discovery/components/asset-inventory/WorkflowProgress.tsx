import React from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import ProgressBar from './ProgressBar';

interface WorkflowStep {
  name: string;
  status: 'completed' | 'in-progress' | 'pending' | 'failed';
  progress: number;
  description?: string;
}

interface WorkflowProgressProps {
  workflowAnalysis: {
    discovery: Record<string, number>;
    mapping: Record<string, number>;
    cleanup: Record<string, number>;
    assessment_ready: Record<string, number>;
    completion_percentages: {
      discovery: number;
      mapping: number;
      cleanup: number;
      assessment_ready: number;
    };
  };
  className?: string;
}

const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  workflowAnalysis,
  className = '',
}) => {
  const steps: WorkflowStep[] = [
    {
      name: 'Discovery',
      status: workflowAnalysis.completion_percentages.discovery >= 100
        ? 'completed'
        : workflowAnalysis.completion_percentages.discovery > 0
          ? 'in-progress'
          : 'pending',
      progress: workflowAnalysis.completion_percentages.discovery,
      description: 'Asset inventory and initial data collection',
    },
    {
      name: 'Mapping',
      status: workflowAnalysis.completion_percentages.mapping >= 100
        ? 'completed'
        : workflowAnalysis.completion_percentages.mapping > 0
          ? 'in-progress'
          : 'pending',
      progress: workflowAnalysis.completion_percentages.mapping,
      description: 'Field mapping and data transformation',
    },
    {
      name: 'Cleanup',
      status: workflowAnalysis.completion_percentages.cleanup >= 100
        ? 'completed'
        : workflowAnalysis.completion_percentages.cleanup > 0
          ? 'in-progress'
          : 'pending',
      progress: workflowAnalysis.completion_percentages.cleanup,
      description: 'Data quality improvements and deduplication',
    },
    {
      name: 'Assessment Ready',
      status: workflowAnalysis.completion_percentages.assessment_ready >= 100
        ? 'completed'
        : workflowAnalysis.completion_percentages.assessment_ready > 0
          ? 'in-progress'
          : 'pending',
      progress: workflowAnalysis.completion_percentages.assessment_ready,
      description: 'Ready for migration assessment',
    },
  ];

  const getStatusIcon = (status: WorkflowStep['status']): JSX.Element => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in-progress':
        return <div className="h-5 w-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: WorkflowStep['status']): any => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressBarColor = (status: WorkflowStep['status']): any => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'in-progress':
        return 'bg-blue-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-200';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {steps.map((step, index) => (
        <div key={step.name} className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`inline-flex items-center justify-center h-8 w-8 rounded-full ${getStatusColor(step.status)}`}>
                {getStatusIcon(step.status)}
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-900">{step.name}</h3>
                {step.description && (
                  <p className="text-xs text-gray-500">{step.description}</p>
                )}
              </div>
            </div>
            <span className="text-sm font-medium text-gray-900">
              {Math.round(step.progress)}%
            </span>
          </div>
          <div className="pl-11">
            <ProgressBar
              percentage={step.progress}
              color={getProgressBarColor(step.status).replace('bg-', '')}
              height="sm"
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default WorkflowProgress;
