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
import { IncompleteFlowV2 } from '@/hooks/discovery/useIncompleteFlowDetectionV2';

interface UploadBlockerV2Props {
  incompleteFlows: IncompleteFlowV2[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  isLoading?: boolean;
}

export const UploadBlockerV2: React.FC<UploadBlockerV2Props> = ({
  incompleteFlows,
  onContinueFlow,
  onDeleteFlow,
  onViewDetails,
  onManageFlows,
  isLoading = false
}) => {
  const getPhaseDisplayName = (phase: string) => {
    const names = {
      'data_import': 'Data Import',
      'attribute_mapping': 'Attribute Mapping',
      'data_cleansing': 'Data Cleansing',
      'inventory': 'Asset Inventory',
      'dependencies': 'Dependency Analysis',
      'tech_debt': 'Tech Debt Analysis'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'active': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const getHighestPriorityFlow = () => {
    // Prioritize failed flows, then running/active, then paused
    const priorityOrder = { 'failed': 3, 'running': 2, 'active': 2, 'paused': 1 };
    return incompleteFlows.sort((a, b) => {
      const aPriority = priorityOrder[a.status as keyof typeof priorityOrder] || 0;
      const bPriority = priorityOrder[b.status as keyof typeof priorityOrder] || 0;
      return bPriority - aPriority;
    })[0];
  };

  const primaryFlow = getHighestPriorityFlow();

  if (isLoading) {
    return (
      <Card className="border-gray-200">
        <CardContent className="py-6">
          <div className="flex items-center space-x-3">
            <Clock className="h-5 w-5 text-gray-400 animate-spin" />
            <span className="text-gray-600">Checking for incomplete flows...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (incompleteFlows.length === 0) {
    return null; // No blocking needed
  }

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
                  <span>{Math.round(primaryFlow.progress_percentage)}%</span>
                </div>
                <Progress value={primaryFlow.progress_percentage} className="h-2" />
              </div>

              {/* Flow details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Flow ID:</span>
                  <p className="font-mono text-xs">{primaryFlow.flow_id.substring(0, 12)}...</p>
                </div>
                <div>
                  <span className="text-gray-600">Last Activity:</span>
                  <p>{formatTimeAgo(primaryFlow.updated_at)}</p>
                </div>
              </div>

              {/* Flow info */}
              <div className="bg-white p-3 rounded border">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Flow Information</h4>
                <div className="text-xs text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Flow Name:</span>
                    <span className="font-medium">{primaryFlow.flow_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Next Phase:</span>
                    <span className="font-medium">{getPhaseDisplayName(primaryFlow.next_phase || 'unknown')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Assessment Ready:</span>
                    <Badge variant={primaryFlow.assessment_ready ? "default" : "outline"} className="text-xs">
                      {primaryFlow.assessment_ready ? 'Yes' : 'No'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Migration Score:</span>
                    <span className="font-medium">{Math.round(primaryFlow.migration_readiness_score * 100)}%</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Action buttons */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {primaryFlow.can_resume && (
                    <Button
                      size="sm"
                      onClick={() => onContinueFlow(primaryFlow.flow_id)}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Continue Flow
                    </Button>
                  )}
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewDetails(primaryFlow.flow_id, primaryFlow.current_phase)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                </div>
                
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onDeleteFlow(primaryFlow.flow_id)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
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
                <div key={flow.flow_id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs">{flow.flow_id.substring(0, 8)}...</span>
                    <span className="capitalize">{getPhaseDisplayName(flow.current_phase)}</span>
                    <Badge variant="outline" className="text-xs">
                      {flow.status}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {Math.round(flow.progress_percentage)}%
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDetails(flow.flow_id, flow.current_phase)}
                    >
                      <Eye className="h-3 w-3" />
                    </Button>
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