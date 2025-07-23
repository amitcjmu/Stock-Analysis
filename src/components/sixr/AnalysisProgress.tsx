import React from 'react'
import type { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader2, 
  Play, 
  Pause, 
  RotateCcw,
  Zap,
  Brain,
  FileSearch,
  MessageSquare,
  Target,
  CheckSquare
} from 'lucide-react';

export interface AnalysisStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  estimatedDuration?: number; // in seconds
  actualDuration?: number; // in seconds
  startTime?: Date;
  endTime?: Date;
  error?: string;
  details?: string[];
}

export interface AnalysisProgress {
  analysisId: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  overallProgress: number;
  currentStep?: string;
  steps: AnalysisStep[];
  estimatedCompletion?: Date;
  startTime?: Date;
  endTime?: Date;
  iterationNumber: number;
}

interface AnalysisProgressProps {
  progress: AnalysisProgress;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
  onRefresh?: () => void;
  showDetails?: boolean;
  realTimeUpdates?: boolean;
  className?: string;
}

const stepIcons = {
  discovery: <FileSearch className="h-4 w-4" />,
  analysis: <Brain className="h-4 w-4" />,
  questions: <MessageSquare className="h-4 w-4" />,
  processing: <Zap className="h-4 w-4" />,
  refinement: <Target className="h-4 w-4" />,
  validation: <CheckSquare className="h-4 w-4" />
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'text-green-600 bg-green-50 border-green-200';
    case 'in_progress': return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'failed': return 'text-red-600 bg-red-50 border-red-200';
    case 'pending': return 'text-gray-600 bg-gray-50 border-gray-200';
    case 'skipped': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'paused': return 'text-orange-600 bg-orange-50 border-orange-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'in_progress': return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    case 'failed': return <AlertCircle className="h-4 w-4 text-red-600" />;
    case 'pending': return <Clock className="h-4 w-4 text-gray-600" />;
    case 'paused': return <Pause className="h-4 w-4 text-orange-600" />;
    default: return <Clock className="h-4 w-4 text-gray-600" />;
  }
};

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
};

const formatTimeRemaining = (endTime: Date): string => {
  const now = new Date();
  const diff = endTime.getTime() - now.getTime();
  
  if (diff <= 0) return 'Completing...';
  
  const minutes = Math.ceil(diff / (1000 * 60));
  if (minutes < 60) return `${minutes}m remaining`;
  
  const hours = Math.ceil(minutes / 60);
  return `${hours}h remaining`;
};

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  progress,
  onPause,
  onResume,
  onCancel,
  onRetry,
  onRefresh,
  showDetails = true,
  realTimeUpdates = true,
  className = ''
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  useEffect(() => {
    if (progress.estimatedCompletion && progress.status === 'in_progress') {
      const updateTimeRemaining = () => {
        setTimeRemaining(formatTimeRemaining(progress.estimatedCompletion));
      };

      updateTimeRemaining();
      const interval = setInterval(updateTimeRemaining, 30000); // Update every 30 seconds

      return () => clearInterval(interval);
    }
  }, [progress.estimatedCompletion, progress.status]);

  const toggleStepDetails = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const completedSteps = progress.steps.filter(step => step.status === 'completed').length;
  const totalSteps = progress.steps.length;
  const currentStepIndex = progress.steps.findIndex(step => step.status === 'in_progress');
  const currentStep = currentStepIndex >= 0 ? progress.steps[currentStepIndex] : null;

  const renderStepItem = (step: AnalysisStep, index: number) => {
    const isExpanded = expandedSteps.has(step.id);
    const stepIcon = stepIcons[step.id as keyof typeof stepIcons] || <Clock className="h-4 w-4" />;
    
    return (
      <div key={step.id} className="relative">
        {/* Connection line */}
        {index < progress.steps.length - 1 && (
          <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-200"></div>
        )}
        
        <div 
          className={`
            flex items-start space-x-4 p-4 rounded-lg border transition-all cursor-pointer
            ${getStatusColor(step.status)}
            ${isExpanded ? 'shadow-md' : 'hover:shadow-sm'}
          `}
          onClick={() => showDetails && toggleStepDetails(step.id)}
        >
          <div className="flex-shrink-0 w-12 h-12 rounded-full bg-white border-2 flex items-center justify-center">
            {step.status === 'in_progress' ? (
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            ) : (
              stepIcon
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">{step.name}</h4>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(step.status)}
                <Badge variant="outline" className={getStatusColor(step.status)}>
                  {step.status.replace('_', ' ')}
                </Badge>
              </div>
            </div>
            
            {step.status === 'in_progress' && (
              <div className="mt-2">
                <Progress value={step.progress} className="h-2" />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{Math.round(step.progress)}% complete</span>
                  {step.estimatedDuration && (
                    <span>~{formatDuration(step.estimatedDuration)} estimated</span>
                  )}
                </div>
              </div>
            )}
            
            {step.status === 'completed' && step.actualDuration && (
              <div className="mt-1 text-xs text-gray-500">
                Completed in {formatDuration(step.actualDuration)}
              </div>
            )}
            
            {step.status === 'failed' && step.error && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                Error: {step.error}
              </div>
            )}
            
            {isExpanded && step.details && step.details.length > 0 && (
              <div className="mt-3 space-y-1">
                <Separator />
                <div className="pt-2">
                  <h5 className="text-xs font-medium text-gray-700 mb-1">Details:</h5>
                  <ul className="space-y-1">
                    {step.details.map((detail, idx) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start space-x-1">
                        <span className="text-blue-500 mt-0.5">•</span>
                        <span>{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold flex items-center space-x-2">
              {getStatusIcon(progress.status)}
              <span>Analysis Progress</span>
              <Badge variant="outline">Iteration {progress.iterationNumber}</Badge>
            </CardTitle>
            <CardDescription>
              6R migration strategy analysis workflow
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {onRefresh && (
              <Button variant="outline" size="sm" onClick={onRefresh}>
                <RotateCcw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
            )}
            {progress.status === 'in_progress' && onPause && (
              <Button variant="outline" size="sm" onClick={onPause}>
                <Pause className="h-4 w-4 mr-1" />
                Pause
              </Button>
            )}
            {progress.status === 'paused' && onResume && (
              <Button variant="outline" size="sm" onClick={onResume}>
                <Play className="h-4 w-4 mr-1" />
                Resume
              </Button>
            )}
            {progress.status === 'failed' && onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry}>
                <RotateCcw className="h-4 w-4 mr-1" />
                Retry
              </Button>
            )}
            {(progress.status === 'in_progress' || progress.status === 'paused') && onCancel && (
              <Button variant="destructive" size="sm" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-gray-600">
              {completedSteps}/{totalSteps} steps completed
            </span>
          </div>
          <Progress value={progress.overallProgress} className="h-3" />
          <div className="flex justify-between text-xs text-gray-500">
            <span>{Math.round(progress.overallProgress)}% complete</span>
            {timeRemaining && (
              <span className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{timeRemaining}</span>
              </span>
            )}
          </div>
        </div>

        {/* Current Step Highlight */}
        {currentStep && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
              <div>
                <h4 className="font-medium text-blue-900">Currently Processing</h4>
                <p className="text-sm text-blue-700">{currentStep.name}</p>
              </div>
            </div>
            {currentStep.progress > 0 && (
              <div className="mt-3">
                <Progress value={currentStep.progress} className="h-2" />
                <div className="text-xs text-blue-600 mt-1">
                  {Math.round(currentStep.progress)}% complete
                </div>
              </div>
            )}
          </div>
        )}

        <Separator />

        {/* Step Details */}
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900">Analysis Steps</h3>
          <div className="space-y-2">
            {progress.steps.map((step, index) => renderStepItem(step, index))}
          </div>
        </div>

        {/* Analysis Summary */}
        {(progress.status === 'completed' || progress.status === 'failed') && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Analysis Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Status:</span>
                <div className="font-medium capitalize">{progress.status}</div>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <div className="font-medium">
                  {progress.startTime && progress.endTime && 
                    formatDuration((progress.endTime.getTime() - progress.startTime.getTime()) / 1000)
                  }
                </div>
              </div>
              <div>
                <span className="text-gray-600">Steps Completed:</span>
                <div className="font-medium">{completedSteps}/{totalSteps}</div>
              </div>
              <div>
                <span className="text-gray-600">Iteration:</span>
                <div className="font-medium">{progress.iterationNumber}</div>
              </div>
            </div>
          </div>
        )}

        {/* Real-time Updates Indicator */}
        {realTimeUpdates && progress.status === 'in_progress' && (
          <div className="flex items-center justify-center text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Real-time updates enabled</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AnalysisProgress; 