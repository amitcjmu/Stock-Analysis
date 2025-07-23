import React from 'react'
import { useState } from 'react'
import { Clock, TrendingUp, RefreshCw, Zap } from 'lucide-react'
import { AlertTriangle, Upload, Play, Trash2, Eye, Activity, Shield, Sparkles } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { IncompleteFlowV2 } from '@/hooks/discovery/useFlowOperations';
import { useFlowCleanup } from '@/hooks/useFlowDeletion';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';

interface UploadBlockerProps {
  incompleteFlows: IncompleteFlowV2[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onViewDetails: (flowId: string, phase: string) => void;
  onManageFlows: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const UploadBlocker: React.FC<UploadBlockerProps> = ({
  incompleteFlows,
  onContinueFlow,
  onDeleteFlow,
  onViewDetails,
  onManageFlows,
  onRefresh,
  isLoading = false
}) => {
  const { toast } = useToast();
  const { client, engagement } = useAuth();
  const { 
    performCleanup, 
    isExecutingCleanup,
    getCleanupRecommendations,
    recommendations,
    isLoadingRecommendations
  } = useFlowCleanup();

  const getPhaseDisplayName = (phase: string) => {
    if (!phase) return 'Unknown';
    
    const names = {
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing',
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Tech Debt Analysis',
      'data_import': 'Data Import'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const getStatusColor = (status: string) => {
    if (!status) return 'bg-gray-100 text-gray-800 border-gray-200';
    
    switch (status) {
      case 'running': 
      case 'active': 
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
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
      flow.flowId && 
      typeof flow.flowId === 'string' && 
      flow.flowId.length > 0
    );
    
    if (validFlows.length === 0) return null;
    
    // Prioritize failed flows, then running/active, then paused
    const priorityOrder = { 'failed': 3, 'running': 2, 'active': 2, 'paused': 1 };
    return validFlows.sort((a, b) => {
      const aPriority = priorityOrder[a.status as keyof typeof priorityOrder] || 0;
      const bPriority = priorityOrder[b.status as keyof typeof priorityOrder] || 0;
      return bPriority - aPriority;
    })[0] || null;
  };

  const primaryFlow = getHighestPriorityFlow();

  /**
   * New user-approval cleanup system
   * System recommends but never auto-deletes
   */
  const handleIntelligentCleanup = async () => {
    try {
      console.log('🧹 Starting intelligent cleanup with user approval...');
      
      if (!client?.id) {
        toast({
          title: "❌ Error",
          description: "Client context not available. Please refresh the page.",
          variant: "destructive",
        });
        return;
      }

      // Use centralized flow deletion service for cleanup
      const result = await performCleanup('discovery');
      
      if (result.success) {
        // Refresh the flow list after successful cleanup
        if (onRefresh) {
          setTimeout(onRefresh, 1000);
        }
      }
    } catch (error) {
      console.error('❌ Intelligent cleanup failed:', error);
      toast({
        title: "❌ Cleanup Failed",
        description: "Failed to perform cleanup. Please try manual cleanup or contact support.",
        variant: "destructive",
      });
    }
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

  // Debug: Show flow statuses for troubleshooting
  const debugInfo = incompleteFlows.map((flow, index) => ({
    id: safeSubstring(flow.flowId, 0, 8),
    uniqueKey: flow.flowId ? `${flow.flowId}-${index}` : `unknown-${index}`,
    status: flow.status,
    phase: flow.current_phase,
    progress: flow.progress_percentage
  }));

  console.log('🔍 Flow Debug Info:', debugInfo);

  return (
    <div className="space-y-4">
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
                  <span>{Math.round(primaryFlow.progress_percentage || 0)}%</span>
                </div>
                <Progress value={primaryFlow.progress_percentage || 0} className="h-2" />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Flow ID:</span>
                  <p className="font-mono text-xs">
                    {safeSubstring(primaryFlow.flowId, 0, 12)}
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
                  <p><span className="font-medium">Name:</span> {primaryFlow.flow_name || 'Discovery Flow'}</p>
                  {primaryFlow.flow_description && (
                    <p className="mt-1"><span className="font-medium">Description:</span> {primaryFlow.flow_description}</p>
                  )}
                  <p className="mt-1"><span className="font-medium">Next Phase:</span> {getPhaseDisplayName(primaryFlow.next_phase)}</p>
                </div>
              </div>

              <Separator />

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

      {/* Debug Information */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">
            Debug: Flow Status Information
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
            <strong>Issue:</strong> Flows with status="active" but phase="completed" and progress=100% 
            should be marked as completed and not block uploads.
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleIntelligentCleanup}
          disabled={isExecutingCleanup}
        >
          <Sparkles className="h-4 w-4 mr-2" />
          {isExecutingCleanup ? 'Requesting cleanup...' : 'Smart cleanup (user approval required)'}
        </Button>
        
        <div className="text-xs text-gray-500">
          💡 System will recommend flows for cleanup but requires your approval
        </div>
      </div>
    </div>
  );
};
