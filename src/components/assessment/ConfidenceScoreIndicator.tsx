import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfidenceScoreIndicatorProps {
  score: number;
  size?: 'small' | 'medium' | 'large';
  showIcon?: boolean;
  showLabel?: boolean;
  breakdown?: Record<string, number>;
}

export const ConfidenceScoreIndicator: React.FC<ConfidenceScoreIndicatorProps> = ({
  score,
  size = 'medium',
  showIcon = true,
  showLabel = true,
  breakdown
}) => {
  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return { level: 'excellent', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle };
    if (score >= 0.8) return { level: 'good', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle };
    if (score >= 0.7) return { level: 'moderate', color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: AlertTriangle };
    if (score >= 0.6) return { level: 'low', color: 'text-orange-600', bgColor: 'bg-orange-100', icon: AlertTriangle };
    return { level: 'very-low', color: 'text-red-600', bgColor: 'bg-red-100', icon: AlertCircle };
  };

  const confidenceInfo = getConfidenceLevel(score);
  const Icon = confidenceInfo.icon;
  const percentage = Math.round(score * 100);

  const sizeClasses = {
    small: {
      text: 'text-xs',
      progress: 'h-1',
      icon: 'h-3 w-3',
      badge: 'text-xs px-1.5 py-0.5'
    },
    medium: {
      text: 'text-sm',
      progress: 'h-2',
      icon: 'h-4 w-4',
      badge: 'text-sm px-2 py-1'
    },
    large: {
      text: 'text-base',
      progress: 'h-3',
      icon: 'h-5 w-5',
      badge: 'text-base px-3 py-1.5'
    }
  };

  const classes = sizeClasses[size];

  if (size === 'small') {
    return (
      <div className="flex items-center space-x-2">
        {showIcon && <Icon className={cn(classes.icon, confidenceInfo.color)} />}
        <span className={cn(classes.text, 'font-medium', confidenceInfo.color)}>
          {percentage}%
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {showIcon && <Icon className={cn(classes.icon, confidenceInfo.color)} />}
          {showLabel && (
            <span className={cn(classes.text, 'font-medium text-gray-700')}>
              Confidence Score
            </span>
          )}
        </div>
        <Badge className={cn(confidenceInfo.bgColor, confidenceInfo.color, classes.badge)}>
          {percentage}%
        </Badge>
      </div>
      
      <div className="space-y-1">
        <Progress 
          value={percentage} 
          className={cn(classes.progress, 'bg-gray-100')}
        />
        
        {size === 'large' && (
          <div className="flex justify-between text-xs text-gray-500">
            <span>Low (60%)</span>
            <span>Good (80%)</span>
            <span>Excellent (90%)</span>
          </div>
        )}
      </div>

      {breakdown && size === 'large' && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-xs font-medium text-gray-700 mb-2">Confidence Breakdown</h4>
          <div className="space-y-1">
            {Object.entries(breakdown).map(([factor, value]) => (
              <div key={factor} className="flex justify-between text-xs">
                <span className="text-gray-600 capitalize">{factor.replace('_', ' ')}</span>
                <span className={cn(
                  'font-medium',
                  value >= 0.8 ? 'text-green-600' :
                  value >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                )}>
                  {Math.round(value * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};