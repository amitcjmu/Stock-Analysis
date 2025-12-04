import React from 'react';
import {
  AlertTriangle,
  Upload,
  Play,
  Trash2,
  Eye,
  Clock,
  TrendingUp,
  Activity,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import type { IncompleteFlow } from '@/hooks/discovery/useFlowOperations';

interface UploadBlockerProps {
  incompleteFlows: IncompleteFlow[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  isLoading?: boolean;
}

export const UploadBlocker: React.FC<UploadBlockerProps> = ({
  incompleteFlows,
  onContinueFlow,
  onDeleteFlow,
  onViewDetails,
  onManageFlows,
  isLoading = false
}) => {
  const getPhaseDisplayName = (phase: string): string => {
    if (!phase) return 'Unknown';

    const names: Record<string, string> = {
      'data_import': 'Data Import',
      'data_validation': 'Data Validation',
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing',
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Tech Debt Analysis',
    };
    return names[phase] || phase.replace(/_/g, ' ').toUpperCase();
  };

  const getStatusColor = (status: string): string => {
    if (!status) return 'bg-gray-100 text-gray-800 border-gray-200';

    switch (status) {
      case 'running':
      case 'active':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimeAgo = (timestamp: string): string => {
    if (!timestamp) return 'Unknown';

    try {
      const now = new Date();
      const time = new Date(timestamp);
      const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  const getHighestPriorityFlow = (): IncompleteFlow | null => {
    if (!incompleteFlows || incompleteFlows.length === 0) return null;

    // Filter out invalid flows first
    const validFlows = incompleteFlows.filter(flow =>
      flow && flow.flowId && typeof flow.flowId === 'string'
    );

    if (validFlows.length === 0) return null;

    // Prioritize failed flows, then running/active, then paused
    const priorityOrder: Record<string, number> = {
      'failed': 3,
      'running': 2,
      'active': 2,
      'paused': 1
    };

    return validFlows.sort((a, b) => {
      const aPriority = priorityOrder[a.status] || 0;
      const bPriority = priorityOrder[b.status] || 0;
      return bPriority - aPriority;
    })[0];
  };

  if (isLoading) {
    return (
      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            <div>
              <h3 className="text-lg font-semibold text-orange-800">Checking for Incomplete Flows...</h3>
              <p className="text-orange-600">Validating existing discovery processes...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (incompleteFlows.length === 0) {
    return null; // No blocking needed
  }

  const primaryFlow = getHighestPriorityFlow();

  return (
    <div className="space-y-4">
      {/* Main blocking alert */}
      <Alert className="border-red-200 bg-red-50">
        <AlertTriangle className="h-5 w-5 text-red-600" />
        <AlertDescription className="text-red-800">
          <div className="flex items-center justify-between">
            <div>
              <strong>Upload Blocked:</strong> {incompleteFlows.length} incomplete discovery flow{incompleteFlows.length > 1 ? 's' : ''} found.
              Complete or delete existing flows before uploading new data.
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onManageFlows}
              className="ml-4"
            >
              <Eye className="h-4 w-4 mr-2" />
              Manage Flows
            </Button>
          </div>
        </AlertDescription>
      </Alert>

      {/* Primary flow card */}
      {primaryFlow && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-orange-800 flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Primary Flow: {getPhaseDisplayName(primaryFlow.current_phase)}</span>
              </CardTitle>
              <Badge className={getStatusColor(primaryFlow.status)}>
                {primaryFlow.status.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>

          <CardContent>
            <div className="space-y-4">
              {/* Progress */}
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span>Overall Progress</span>
                  <span>{Math.round(primaryFlow.progress_percentage || 0)}%</span>
                </div>
                <Progress value={primaryFlow.progress_percentage || 0} className="h-2" />
              </div>

              {/* Flow details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Flow ID:</span>
                  <p className="font-mono text-xs">
                    {primaryFlow.flowId ? primaryFlow.flowId.substring(0, 12) + '...' : 'Unknown'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Last Activity:</span>
                  <p>{formatTimeAgo(primaryFlow.updated_at)}</p>
                </div>
              </div>

              {/* Agent insights if available */}
              {primaryFlow.agent_insights && primaryFlow.agent_insights.length > 0 && (
                <div className="bg-white p-3 rounded border">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Latest Agent Insight</h4>
                  <div className="text-xs text-gray-600">
                    <span className="font-medium capitalize">
                      {getPhaseDisplayName(primaryFlow.agent_insights[0].phase)}:
                    </span>
                    <p className="mt-1">{primaryFlow.agent_insights[0].insight}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-gray-400">
                        {formatTimeAgo(primaryFlow.agent_insights[0].timestamp)}
                      </span>
                      {primaryFlow.agent_insights[0].confidence && (
                        <Badge variant="outline" className="text-xs">
                          {Math.round(primaryFlow.agent_insights[0].confidence * 100)}% confidence
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <Separator />

              {/* Action buttons */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {primaryFlow.can_resume && primaryFlow.flowId && (
                    <Button
                      size="sm"
                      onClick={() => onContinueFlow(primaryFlow.flowId)}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Continue Flow
                    </Button>
                  )}

                  {primaryFlow.flowId && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails(primaryFlow.flowId, primaryFlow.current_phase || 'unknown')}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  )}
                </div>

                {primaryFlow.flowId && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDeleteFlow(primaryFlow.flowId)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Additional flows summary */}
      {incompleteFlows.length > 1 && (
        <Card className="border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-gray-800 flex items-center justify-between">
              <span>Additional Incomplete Flows ({incompleteFlows.length - 1})</span>
              <Button variant="outline" size="sm" onClick={onManageFlows}>
                <TrendingUp className="h-4 w-4 mr-2" />
                Manage All
              </Button>
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="space-y-2">
              {incompleteFlows.slice(1, 4).map((flow) => (
                <div key={flow.flowId} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs">
                      {flow.flowId ? flow.flowId.substring(0, 8) + '...' : 'Unknown'}
                    </span>
                    <span className="capitalize">{getPhaseDisplayName(flow.current_phase)}</span>
                    <Badge variant="outline" className="text-xs">
                      {flow.status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {Math.round(flow.progress_percentage || 0)}%
                    </span>
                    {flow.flowId && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetails(flow.flowId, flow.current_phase || 'unknown')}
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}

              {incompleteFlows.length > 4 && (
                <div className="text-center py-2">
                  <Button variant="link" size="sm" onClick={onManageFlows}>
                    View {incompleteFlows.length - 4} more flows...
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload disabled message */}
      <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">Data Upload Disabled</h3>
        <p className="text-gray-500 mb-4">
          Complete or delete existing discovery flows to enable new data uploads.
          This ensures proper data integrity and prevents conflicts.
        </p>
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
          <Shield className="h-4 w-4" />
          <span>Data integrity protection active</span>
        </div>
      </div>
    </div>
  );
};
