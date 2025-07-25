/**
 * Agent Performance Card Component
 * Individual agent performance display card with metrics and status
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react'
import { useState } from 'react'
import { cn } from '../../lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  MoreHorizontal,
  Zap,
  Target,
  Timer
} from 'lucide-react';
import { AgentStatusIndicator, AgentOnlineIndicator } from './AgentStatusIndicator';
import type { PerformanceCardProps} from '../../types/api/observability/agent-performance';
import { AgentCardData } from '../../types/api/observability/agent-performance';

// Helper function to format duration
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
};

// Helper function to format numbers
const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

// Helper function to get success rate color
const getSuccessRateColor = (rate: number): string => {
  if (rate >= 0.9) return 'text-green-600';
  if (rate >= 0.7) return 'text-yellow-600';
  return 'text-red-600';
};

// Helper function to get trend icon
const getTrendIcon = (value: number, threshold: number = 0) => {
  if (value > threshold) return <TrendingUp className="h-3 w-3 text-green-500" />;
  if (value < threshold) return <TrendingDown className="h-3 w-3 text-red-500" />;
  return null;
};

export const AgentPerformanceCard: React.FC<PerformanceCardProps> = ({
  agent,
  detailed = false,
  showChart = false,
  onClick,
  className
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleCardClick = () => {
    if (onClick) {
      onClick(agent);
    }
  };

  const cardClasses = cn(
    'transition-all duration-200 hover:shadow-md',
    onClick && 'cursor-pointer hover:border-blue-300',
    isHovered && 'scale-[1.02]',
    'border border-gray-200',
    className
  );

  return (
    <Card
      className={cardClasses}
      onClick={handleCardClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <AgentStatusIndicator
                status={agent.status}
                variant="dot"
                size="md"
                pulse={agent.status === 'active'}
              />
              <CardTitle className="text-lg font-semibold text-gray-900 truncate">
                {agent.name}
              </CardTitle>
            </div>
            <AgentOnlineIndicator
              isOnline={agent.isOnline}
              size="sm"
            />
          </div>

          <div className="flex items-center space-x-2">
            {detailed && (
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {detailed && (
          <div className="text-sm text-gray-500">
            Last active: {agent.lastActive}
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Primary Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Target className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium text-gray-600">Success Rate</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={cn(
                  'text-xl font-bold',
                  getSuccessRateColor(agent.successRate)
                )}>
                  {(agent.successRate * 100).toFixed(1)}%
                </span>
                {getTrendIcon(agent.successRate, 0.8)}
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-gray-600">Tasks</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold text-gray-900">
                  {formatNumber(agent.totalTasks)}
                </span>
                <Badge variant="outline" className="text-xs">
                  Total
                </Badge>
              </div>
            </div>
          </div>

          {/* Secondary Metrics */}
          <div className="grid grid-cols-1 gap-3">
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
              <div className="flex items-center space-x-2">
                <Timer className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-600">Avg Duration</span>
              </div>
              <span className="text-sm font-semibold text-gray-900">
                {formatDuration(agent.avgDuration)}
              </span>
            </div>

            {detailed && (
              <>
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-orange-500" />
                    <span className="text-sm font-medium text-gray-600">Status</span>
                  </div>
                  <AgentStatusIndicator
                    status={agent.status}
                    variant="badge"
                    size="sm"
                  />
                </div>

                <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-2">
                    <Zap className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium text-gray-600">Health</span>
                  </div>
                  <Badge
                    variant={agent.successRate > 0.8 ? "default" : "destructive"}
                    className="text-xs"
                  >
                    {agent.successRate > 0.8 ? 'Healthy' : 'Needs Attention'}
                  </Badge>
                </div>
              </>
            )}
          </div>

          {/* Chart placeholder */}
          {showChart && (
            <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Performance Trend</span>
                <Clock className="h-4 w-4 text-gray-400" />
              </div>
              <div className="h-16 flex items-end space-x-1">
                {/* Simple sparkline placeholder */}
                {Array.from({ length: 12 }, (_, i) => {
                  const height = Math.random() * 80 + 20;
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-blue-300 rounded-t opacity-70 hover:opacity-100 transition-opacity"
                      style={{ height: `${height}%` }}
                    />
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          {detailed && (
            <div className="flex space-x-2 mt-4">
              <Button variant="outline" size="sm" className="flex-1">
                View Details
              </Button>
              <Button variant="outline" size="sm" className="flex-1">
                View History
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Compact version for grid layouts
export const AgentPerformanceCardCompact: React.FC<PerformanceCardProps> = (props) => {
  return (
    <AgentPerformanceCard
      {...props}
      detailed={false}
      showChart={false}
      className={cn('min-h-[200px]', props.className)}
    />
  );
};

// Detailed version for detailed views
export const AgentPerformanceCardDetailed: React.FC<PerformanceCardProps> = (props) => {
  return (
    <AgentPerformanceCard
      {...props}
      detailed={true}
      showChart={true}
      className={cn('min-h-[400px]', props.className)}
    />
  );
};

export default AgentPerformanceCard;
