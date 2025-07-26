import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, Activity, Zap, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentUpdate {
  timestamp: Date;
  phase: string;
  message: string;
  progress?: number;
}

interface RealTimeProgressIndicatorProps {
  agentUpdates: AgentUpdate[];
  currentPhase: string;
}

export const RealTimeProgressIndicator: React.FC<RealTimeProgressIndicatorProps> = ({
  agentUpdates,
  currentPhase
}) => {
  const recentUpdates = agentUpdates.slice(-5);
  const latestUpdate = agentUpdates[agentUpdates.length - 1];

  const getPhaseDisplayName = (phase: string): JSX.Element => {
    const phaseNames: Record<string, string> = {
      'tech_debt_analysis': 'Technical Debt Analysis',
      'component_identification': 'Component Identification',
      'architecture_analysis': 'Architecture Analysis',
      'dependency_mapping': 'Dependency Mapping',
      'security_scanning': 'Security Scanning',
      'performance_analysis': 'Performance Analysis'
    };
    return phaseNames[phase] || phase;
  };

  const getUpdateIcon = (message: string): JSX.Element => {
    if (message.includes('completed') || message.includes('finished')) {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    }
    if (message.includes('analyzing') || message.includes('processing')) {
      return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    }
    return <Activity className="h-4 w-4 text-orange-600" />;
  };

  const formatTime = (timestamp: Date): any => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center space-x-2">
          <Zap className="h-5 w-5 text-blue-600" />
          <span>AI Agent Progress</span>
        </CardTitle>
        <CardDescription>
          Real-time updates from AI agents analyzing your applications
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Phase */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <Badge className="bg-blue-100 text-blue-700">
              Current Phase
            </Badge>
            <span className="text-sm text-blue-600 font-medium">
              {getPhaseDisplayName(currentPhase)}
            </span>
          </div>
          {latestUpdate?.progress && (
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-blue-700">Progress</span>
                <span className="text-blue-600">{latestUpdate.progress}%</span>
              </div>
              <Progress value={latestUpdate.progress} className="h-2" />
            </div>
          )}
        </div>

        {/* Recent Updates */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Recent Activity</h4>
          {recentUpdates.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">
              No updates yet. AI agents will start processing soon...
            </p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {recentUpdates.map((update, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex items-start space-x-3 p-2 rounded-lg transition-colors",
                    index === recentUpdates.length - 1
                      ? "bg-blue-50 border border-blue-200"
                      : "bg-gray-50"
                  )}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getUpdateIcon(update.message)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-900 truncate">
                        {update.message}
                      </p>
                      <span className="text-xs text-gray-500 ml-2">
                        {formatTime(update.timestamp)}
                      </span>
                    </div>
                    {update.phase !== currentPhase && (
                      <p className="text-xs text-gray-600 mt-1">
                        {getPhaseDisplayName(update.phase)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status Summary */}
        <div className="pt-2 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Total Updates:</span>
            <span className="font-medium">{agentUpdates.length}</span>
          </div>
          {latestUpdate && (
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-gray-600">Last Update:</span>
              <span className="font-medium">{formatTime(latestUpdate.timestamp)}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
