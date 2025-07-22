import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Upload, 
  Play, 
  Trash2, 
  Eye, 
  Clock,
  Activity,
  Shield,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { CollectionFlow } from '@/hooks/collection/useCollectionFlowManagement';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { canDeleteCollectionFlow } from '@/utils/rbac';

interface CollectionUploadBlockerProps {
  incompleteFlows: CollectionFlow[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const CollectionUploadBlocker: React.FC<CollectionUploadBlockerProps> = ({
  incompleteFlows,
  onContinueFlow,
  onDeleteFlow,
  onViewDetails,
  onManageFlows,
  onRefresh,
  isLoading = false
}) => {
  const { toast } = useToast();
  const { user } = useAuth();
  const [deletingFlowId, setDeletingFlowId] = useState<string | null>(null);

  const getPhaseDisplayName = (phase: string) => {
    if (!phase) return 'Unknown';
    
    const names = {
      'initialization': 'Initialization',
      'platform_detection': 'Platform Detection',
      'automated_collection': 'Automated Collection',
      'gap_analysis': 'Gap Analysis',
      'questionnaire_generation': 'Questionnaire Generation',
      'manual_collection': 'Manual Collection',
      'data_validation': 'Data Validation',
      'finalization': 'Finalization'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const getStatusColor = (status: string) => {
    if (!status) return 'bg-gray-100 text-gray-800 border-gray-200';
    
    switch (status.toLowerCase()) {
      case 'running': 
      case 'active': 
      case 'initialized':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'paused': 
      case 'manual_collection':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': 
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'gap_analysis':
      case 'questionnaire_generation':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default: 
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    if (!timestamp) return 'Unknown';
    
    try {
      const now = new Date();
      const time = new Date(timestamp);
      const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
      
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch (error) {
      return 'Unknown';
    }
  };

  const safeSubstring = (str: string | undefined | null, start: number, length?: number): string => {
    if (!str || typeof str !== 'string' || str.length === 0) return 'Unknown';
    
    try {
      if (length) {
        return str.substring(start, start + length) + '...';
      }
      return str.substring(start) + '...';
    } catch (error) {
      return 'Unknown';
    }
  };

  const getHighestPriorityFlow = () => {
    if (!incompleteFlows || incompleteFlows.length === 0) return null;
    
    // Filter out invalid flows first
    const validFlows = incompleteFlows.filter(flow => 
      flow && 
      (flow.flow_id || flow.id) && 
      typeof (flow.flow_id || flow.id) === 'string' && 
      (flow.flow_id || flow.id).length > 0
    );
    
    if (validFlows.length === 0) return null;
    
    // Prioritize failed flows, then running/active, then others
    const priorityOrder = { 
      'failed': 3, 
      'error': 3,
      'running': 2, 
      'active': 2, 
      'initialized': 2,
      'manual_collection': 2,
      'gap_analysis': 2,
      'questionnaire_generation': 2,
      'paused': 1 
    };
    
    return validFlows.sort((a, b) => {
      const aPriority = priorityOrder[a.status as keyof typeof priorityOrder] || 0;
      const bPriority = priorityOrder[b.status as keyof typeof priorityOrder] || 0;
      return bPriority - aPriority;
    })[0] || null;
  };

  const primaryFlow = getHighestPriorityFlow();

  if (isLoading) {
    return (
      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            <div>
              <h3 className="text-lg font-semibold text-orange-800">Checking for Incomplete Collection Flows...</h3>
              <p className="text-orange-600">Validating existing collection processes...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (incompleteFlows.length === 0) {
    return null; // No blocking needed
  }

  // Debug: Show flow statuses for troubleshooting
  const debugInfo = incompleteFlows.map((flow, index) => ({
    id: safeSubstring(flow.flow_id || flow.id, 0, 8),
    uniqueKey: (flow.flow_id || flow.id) ? `${flow.flow_id || flow.id}-${index}` : `unknown-${index}`,
    status: flow.status,
    phase: flow.current_phase,
    progress: flow.progress || 0
  }));

  console.log('🔍 Collection Flow Debug Info:', debugInfo);

  return (
    <div className="space-y-4">
      <Alert className="border-red-200 bg-red-50">
        <AlertTriangle className="h-5 w-5 text-red-600" />
        <AlertDescription className="text-red-800">
          <div className="flex items-center justify-between">
            <div>
              <strong>Collection Blocked:</strong> {incompleteFlows.length} incomplete collection flow{incompleteFlows.length > 1 ? 's' : ''} found. 
              Complete or delete existing flows before starting new collection processes.
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

      {primaryFlow && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-orange-800 flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Primary Flow: {getPhaseDisplayName(primaryFlow.current_phase)}</span>
              </CardTitle>
              <Badge className={getStatusColor(primaryFlow.status)}>
                {(primaryFlow.status || 'unknown').toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span>Overall Progress</span>
                  <span>{Math.round(primaryFlow.progress || 0)}%</span>
                </div>
                <Progress value={primaryFlow.progress || 0} className="h-2" />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Flow ID:</span>
                  <p className="font-mono text-xs">
                    {safeSubstring(primaryFlow.flow_id || primaryFlow.id, 0, 12)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Last Activity:</span>
                  <p>{formatTimeAgo(primaryFlow.updated_at)}</p>
                </div>
              </div>

              <div className="bg-white p-3 rounded border">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Flow Information</h4>
                <div className="text-xs text-gray-600">
                  <p><span className="font-medium">Name:</span> {primaryFlow.flow_name || 'Collection Flow'}</p>
                  <p className="mt-1"><span className="font-medium">Automation Tier:</span> {primaryFlow.automation_tier || 'Unknown'}</p>
                  {primaryFlow.collection_config && (
                    <p className="mt-1"><span className="font-medium">Type:</span> {primaryFlow.collection_config.form_type || 'Unknown'}</p>
                  )}
                </div>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {primaryFlow.can_resume && (primaryFlow.flow_id || primaryFlow.id) && (
                    <Button
                      size="sm"
                      onClick={() => onContinueFlow(primaryFlow.flow_id || primaryFlow.id)}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Continue Flow
                    </Button>
                  )}
                  
                  {(primaryFlow.flow_id || primaryFlow.id) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails(primaryFlow.flow_id || primaryFlow.id, primaryFlow.current_phase || 'unknown')}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  )}
                </div>
                
                {(primaryFlow.flow_id || primaryFlow.id) && canDeleteCollectionFlow(user) && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={async () => {
                      const flowId = primaryFlow.flow_id || primaryFlow.id;
                      setDeletingFlowId(flowId);
                      try {
                        await onDeleteFlow(flowId);
                      } finally {
                        setDeletingFlowId(null);
                      }
                    }}
                    disabled={isLoading || deletingFlowId === (primaryFlow.flow_id || primaryFlow.id)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {deletingFlowId === (primaryFlow.flow_id || primaryFlow.id) ? 'Deleting...' : 'Delete'}
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">Collection Form Disabled</h3>
        <p className="text-gray-500 mb-4">
          Complete or delete existing collection flows to enable new adaptive form collection. 
          This ensures proper data integrity and prevents workflow conflicts.
        </p>
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
          <Shield className="h-4 w-4" />
          <span>Data integrity protection active</span>
        </div>
      </div>

      {/* Debug Information */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">
            Debug: Collection Flow Status Information
          </h4>
          <div className="text-xs text-blue-700 space-y-1">
            {debugInfo.map(flow => (
              <div key={flow.uniqueKey} className="flex justify-between">
                <span>Flow {flow.id}:</span>
                <span>{flow.status} | {flow.phase} | {flow.progress}%</span>
              </div>
            ))}
          </div>
          <div className="mt-2 text-xs text-blue-600">
            <strong>Collection Flow Management:</strong> Flows with status other than "completed", "failed", or "cancelled" 
            are considered active and will block new collection processes.
          </div>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              className="mt-2"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Flow Status
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};