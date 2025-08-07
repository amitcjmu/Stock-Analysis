import React from 'react';
import { Play } from 'lucide-react'
import { Activity, CheckCircle2, AlertTriangle, Clock, Zap, Eye, Trash2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { validateFlowObject, createDisplaySafeUUID, debugUUID } from '@/utils/uuidValidation';
import type { FlowSummary } from '../types';

interface FlowsOverviewProps {
  flows: FlowSummary[] | undefined;
  onViewDetails: (flowId: string, phase: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onSetFlowStatus: (flowId: string) => void;
  isDeleting: boolean;
}

export const FlowsOverview: React.FC<FlowsOverviewProps> = ({
  flows,
  onViewDetails,
  onDeleteFlow,
  onSetFlowStatus,
  isDeleting
}) => {
  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'paused':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'running':
      case 'active':
        return <Zap className="h-4 w-4 text-blue-600 animate-pulse" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string): unknown => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'running':
      case 'active':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Defensive check: Handle undefined/null flows
  if (!flows || !Array.isArray(flows)) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Activity className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Flows...</h3>
          <p className="text-gray-600 text-center">
            Please wait while we load your discovery flows.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (flows.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Activity className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Flows</h3>
          <p className="text-gray-600 text-center">
            Start a new discovery flow to begin monitoring AI-powered migration analysis.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">Active Discovery Flows</h2>

      <div className="grid gap-4">
        {flows
          .filter((flow) => {
            // More comprehensive flow_id validation
            if (!flow || typeof flow !== 'object') {
              console.error('❌ Invalid flow object:', flow);
              return false;
            }
            if (!flow.flow_id || typeof flow.flow_id !== 'string' || flow.flow_id.trim() === '') {
              console.error('❌ Flow missing or invalid flow_id:', {
                flow_id: flow.flow_id,
                type: typeof flow.flow_id,
                engagement_name: flow.engagement_name || 'Unknown',
                full_flow: flow
              });
              return false;
            }
            return true;
          })
          .map((flow, index) => {
          // Since we've already filtered for flow_id existence, we know it's safe
          // But add additional validation for corruption detection with error handling
          let validation: { validated: boolean; issues: string[]; flow_id?: string } = {
            validated: true,
            issues: []
          };

          try {
            validation = validateFlowObject(flow, 'FlowsOverview');
          } catch (error) {
            console.error('❌ Flow validation threw error:', error, 'for flow:', flow);
            validation = { validated: false, issues: [`Validation error: ${error}`] };
          }

          if (!validation.validated) {
            console.warn('⚠️ Flow validation failed but proceeding with render:', validation.issues);
            // Only call debugUUID if flow_id exists and is a string
            if (flow.flow_id && typeof flow.flow_id === 'string') {
              try {
                debugUUID(flow.flow_id, `Corrupted Flow ID for ${flow.engagement_name || 'Unknown'}`);
              } catch (debugError) {
                console.error('❌ Debug UUID failed:', debugError);
              }
            }
          }

          // Use flow_id as key, with fallback to index for safety
          const cardKey = flow.flow_id || `flow-${index}`;

          return (
          <Card key={cardKey} className="border border-gray-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(flow.status)}
                  <div>
                    <CardTitle className="text-lg">
                      {flow.engagement_name}
                    </CardTitle>
                    <p className="text-sm text-gray-600">
                      {flow.client_name} • {flow.flow_type} flow
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(flow.status)}>
                    {flow.status.charAt(0).toUpperCase() + flow.status.slice(1)}
                  </Badge>
                  <Badge variant="outline">
                    {flow.current_phase}
                  </Badge>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="space-y-4">
                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Progress</span>
                    <span className="font-medium">{flow.progress}%</span>
                  </div>
                  <Progress value={flow.progress} className="h-2" />
                </div>

                {/* Flow metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Active Agents</div>
                    <div className="font-semibold">{flow.active_agents}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Data Sources</div>
                    <div className="font-semibold">{flow.data_sources}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Success Criteria</div>
                    <div className="font-semibold">
                      {flow.success_criteria_met}/{flow.total_success_criteria}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-600">Started</div>
                    <div className="font-semibold">
                      {new Date(flow.started_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="text-xs text-gray-500 font-mono">
                    {validation.validated
                      ? createDisplaySafeUUID(validation.flow_id, { length: 8 })
                      : `⚠️ INVALID: ${flow.flow_id ? flow.flow_id.slice(0, 8) + '...' : 'NO_ID'}`
                    }
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSetFlowStatus(flow.flow_id)}
                      className="flex items-center space-x-1"
                    >
                      <Activity className="h-3 w-3" />
                      <span>Monitor</span>
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails(flow.flow_id, flow.current_phase)}
                      className="flex items-center space-x-1"
                    >
                      <Eye className="h-3 w-3" />
                      <span>View</span>
                    </Button>

                    {flow.status === 'failed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDeleteFlow(flow.flow_id)}
                        disabled={isDeleting}
                        className="flex items-center space-x-1 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-3 w-3" />
                        <span>Delete</span>
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          );
        })}
      </div>
    </div>
  );
};
