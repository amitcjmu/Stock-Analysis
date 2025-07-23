import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Activity, Clock, AlertTriangle, MapPin, Zap, Server, Network } from 'lucide-react'
import { Play, Trash2, ExternalLink, CheckCircle, Loader2 } from 'lucide-react'
import { BatchDeletionConfirmDialog } from './BatchDeletionConfirmDialog';
import { FlowDeletionConfirmDialog } from './FlowDeletionConfirmDialog';

interface IncompleteFlowManagerProps {
  flows: unknown[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onBatchDelete: (flowIds: string[]) => void;
  onViewDetails?: (flowId: string, phase: string) => void;
  isLoading?: boolean;
}

export const IncompleteFlowManager: React.FC<IncompleteFlowManagerProps> = ({
  flows,
  onContinueFlow,
  onDeleteFlow,
  onBatchDelete,
  onViewDetails,
  isLoading = false
}) => {
  const [selectedFlows, setSelectedFlows] = useState<string[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showBatchDeleteConfirm, setShowBatchDeleteConfirm] = useState(false);

  const getPhaseIcon = (phase: string) => {
    const icons = {
      'field_mapping': MapPin,
      'data_cleansing': Zap,
      'asset_inventory': Server,
      'dependency_analysis': Network,
      'tech_debt_analysis': AlertTriangle
    };
    return icons[phase] || Activity;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPhaseDisplayName = (phase: string) => {
    const names = {
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing', 
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Technical Debt Analysis'
    };
    return names[phase] || phase?.replace('_', ' ').toUpperCase() || 'Unknown Phase';
  };

  const handleSelectFlow = (flowId: string, checked: boolean) => {
    setSelectedFlows(prev => 
      checked 
        ? [...prev, flowId]
        : prev.filter(id => id !== flowId)
    );
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectedFlows(checked ? flows.map(f => f.flow_id) : []);
  };

  const handleDeleteConfirm = (flowId: string) => {
    onDeleteFlow(flowId);
    setShowDeleteConfirm(null);
  };

  const handleBatchDeleteConfirm = () => {
    onBatchDelete(selectedFlows);
    setShowBatchDeleteConfirm(false);
    setSelectedFlows([]);
  };

  if (flows.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Incomplete Flows
        </h3>
        <p className="text-gray-600">
          All discovery flows are completed. You can start a new flow anytime.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with bulk actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Incomplete Discovery Flows</h2>
          <p className="text-gray-600 mt-1">
            {flows.length} incomplete flow{flows.length !== 1 ? 's' : ''} found. 
            Complete existing flows before starting new ones.
          </p>
        </div>
        
        {selectedFlows.length > 0 && (
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">
              {selectedFlows.length} selected
            </span>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowBatchDeleteConfirm(true)}
              disabled={isLoading}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Selected
            </Button>
          </div>
        )}
      </div>

      {/* Select all checkbox */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="select-all"
          checked={selectedFlows.length === flows.length}
          onCheckedChange={handleSelectAll}
          disabled={isLoading}
        />
        <label htmlFor="select-all" className="text-sm font-medium">
          Select all flows
        </label>
      </div>

      {/* Flow list */}
      <div className="space-y-4">
        {flows.map((flow, index) => {
          const PhaseIcon = getPhaseIcon(flow.current_phase);
          const isSelected = selectedFlows.includes(flow.flow_id);
          
          return (
            <Card key={flow.flow_id || `flow-${index}`} className={`${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => handleSelectFlow(flow.flow_id, checked as boolean)}
                      disabled={isLoading}
                    />
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <PhaseIcon className="h-5 w-5 text-blue-600" />
                        <span>{getPhaseDisplayName(flow.current_phase)}</span>
                        <Badge className={getStatusColor(flow.status)}>
                          {flow.status}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="mt-1">
                        Flow ID: {flow.flow_id}
                      </CardDescription>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      {Math.round(flow.progress_percentage || 0)}% complete
                    </p>
                    <p className="text-xs text-gray-500">
                      Created: {new Date(flow.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                <div className="space-y-4">
                  {/* Progress bar */}
                  <div>
                    <Progress value={flow.progress_percentage || 0} className="h-2" />
                  </div>
                  
                  {/* Flow details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Last Updated</p>
                      <p className="font-medium">
                        {new Date(flow.updated_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Flow Name</p>
                      <p className="font-medium">{flow.flow_name || 'Discovery Flow'}</p>
                    </div>
                  </div>
                  
                  {/* Agent insights preview */}
                  {flow.agent_insights && flow.agent_insights.length > 0 && (
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm font-medium text-blue-800 mb-1">
                        Latest Agent Insight
                      </p>
                      <p className="text-sm text-blue-700">
                        {(() => {
                          const latestInsight = flow.agent_insights[0];
                          return latestInsight?.description || latestInsight?.insight || 'Processing...';
                        })()}
                      </p>
                    </div>
                  )}
                  
                  {/* Action buttons */}
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center space-x-2">
                      {(flow.can_resume !== false && flow.status !== 'failed') && (
                        <Button
                          size="sm"
                          onClick={() => onContinueFlow(flow.flow_id)}
                          disabled={isLoading}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          ) : (
                            <Play className="h-4 w-4 mr-2" />
                          )}
                          Continue Flow
                        </Button>
                      )}
                      
                      {onViewDetails && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onViewDetails(flow.flow_id, flow.current_phase)}
                          disabled={isLoading}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      )}
                    </div>
                    
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setShowDeleteConfirm(flow.flow_id)}
                      disabled={isLoading}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Deletion confirmation dialogs */}
      {showDeleteConfirm && (
        <FlowDeletionConfirmDialog
          flow={flows.find(f => f.flow_id === showDeleteConfirm)}
          onConfirm={() => handleDeleteConfirm(showDeleteConfirm)}
          onCancel={() => setShowDeleteConfirm(null)}
        />
      )}

      {showBatchDeleteConfirm && (
        <BatchDeletionConfirmDialog
          flowCount={selectedFlows.length}
          flows={flows.filter(f => selectedFlows.includes(f.flow_id))}
          onConfirm={handleBatchDeleteConfirm}
          onCancel={() => setShowBatchDeleteConfirm(false)}
        />
      )}
    </div>
  );
};
