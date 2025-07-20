import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Play, 
  Trash2, 
  ExternalLink, 
  Activity, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  Database,
  Zap,
  Server,
  Network,
  Loader2,
  BarChart3,
  FileText,
  Users
} from 'lucide-react';
import { BatchDeletionConfirmDialog } from '../discovery/BatchDeletionConfirmDialog';
import { FlowDeletionConfirmDialog } from '../discovery/FlowDeletionConfirmDialog';

interface CollectionFlow {
  id: string;
  flow_id?: string;
  flow_name?: string;
  status: string;
  current_phase: string;
  progress: number;
  automation_tier: string;
  created_at: string;
  updated_at: string;
  collection_config?: any;
  gaps_identified?: number;
  can_resume?: boolean;
}

interface IncompleteCollectionFlowManagerProps {
  flows: CollectionFlow[];
  onContinueFlow: (flowId: string) => void;
  onDeleteFlow: (flowId: string) => void;
  onBatchDelete: (flowIds: string[]) => void;
  onViewDetails?: (flowId: string, phase: string) => void;
  isLoading?: boolean;
}

export const IncompleteCollectionFlowManager: React.FC<IncompleteCollectionFlowManagerProps> = ({
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
      'initialization': Activity,
      'platform_detection': Server,
      'automated_collection': Database,
      'gap_analysis': BarChart3,
      'questionnaire_generation': FileText,
      'manual_collection': Users,
      'data_validation': CheckCircle,
      'finalization': Zap
    };
    return icons[phase] || Activity;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'initialized': return 'bg-blue-100 text-blue-800';
      case 'platform_detection': return 'bg-purple-100 text-purple-800';
      case 'automated_collection': return 'bg-green-100 text-green-800';
      case 'gap_analysis': return 'bg-orange-100 text-orange-800';
      case 'manual_collection': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAutomationTierColor = (tier: string) => {
    switch (tier) {
      case 'tier_1': return 'bg-gray-100 text-gray-800';
      case 'tier_2': return 'bg-blue-100 text-blue-800';
      case 'tier_3': return 'bg-green-100 text-green-800';
      case 'tier_4': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPhaseDisplayName = (phase: string) => {
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
    return names[phase] || phase?.replace('_', ' ').toUpperCase() || 'Unknown Phase';
  };

  const getAutomationTierDisplay = (tier: string) => {
    const displays = {
      'tier_1': 'Tier 1 - Manual',
      'tier_2': 'Tier 2 - Script-Assisted',
      'tier_3': 'Tier 3 - API-Integrated',
      'tier_4': 'Tier 4 - Fully Automated'
    };
    return displays[tier] || tier;
  };

  const handleSelectFlow = (flowId: string, checked: boolean) => {
    setSelectedFlows(prev => 
      checked 
        ? [...prev, flowId]
        : prev.filter(id => id !== flowId)
    );
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectedFlows(checked ? flows.map(f => f.id) : []);
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
          No Incomplete Collection Flows
        </h3>
        <p className="text-gray-600">
          All collection flows are completed. You can start a new collection flow anytime.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with bulk actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Incomplete Collection Flows</h2>
          <p className="text-gray-600 mt-1">
            {flows.length} incomplete collection flow{flows.length !== 1 ? 's' : ''} found. 
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
          const isSelected = selectedFlows.includes(flow.id);
          
          return (
            <Card key={flow.id || `flow-${index}`} className={`${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => handleSelectFlow(flow.id, checked as boolean)}
                      disabled={isLoading}
                    />
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <PhaseIcon className="h-5 w-5 text-blue-600" />
                        <span>{getPhaseDisplayName(flow.current_phase)}</span>
                        <Badge className={getStatusColor(flow.status)}>
                          {flow.status}
                        </Badge>
                        <Badge className={getAutomationTierColor(flow.automation_tier)}>
                          {getAutomationTierDisplay(flow.automation_tier)}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="mt-1">
                        Flow ID: {flow.flow_id || flow.id}
                      </CardDescription>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      {Math.round(flow.progress || 0)}% complete
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
                    <Progress value={flow.progress || 0} className="h-2" />
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
                      <p className="font-medium">{flow.flow_name || 'Collection Flow'}</p>
                    </div>
                  </div>
                  
                  {/* Collection metrics */}
                  {(flow.gaps_identified !== undefined || flow.collection_config?.detected_platforms) && (
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm font-medium text-blue-800 mb-2">
                        Collection Progress
                      </p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {flow.gaps_identified !== undefined && (
                          <div>
                            <p className="text-blue-600">Data Gaps Identified</p>
                            <p className="font-medium text-blue-800">{flow.gaps_identified}</p>
                          </div>
                        )}
                        {flow.collection_config?.detected_platforms && (
                          <div>
                            <p className="text-blue-600">Platforms Detected</p>
                            <p className="font-medium text-blue-800">
                              {Array.isArray(flow.collection_config.detected_platforms) 
                                ? flow.collection_config.detected_platforms.length 
                                : 0}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Action buttons */}
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center space-x-2">
                      {(flow.can_resume !== false && flow.status !== 'failed') && (
                        <Button
                          size="sm"
                          onClick={() => onContinueFlow(flow.id)}
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
                          onClick={() => onViewDetails(flow.id, flow.current_phase)}
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
                      onClick={() => setShowDeleteConfirm(flow.id)}
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
          flow={flows.find(f => f.id === showDeleteConfirm)}
          onConfirm={() => handleDeleteConfirm(showDeleteConfirm)}
          onCancel={() => setShowDeleteConfirm(null)}
        />
      )}

      {showBatchDeleteConfirm && (
        <BatchDeletionConfirmDialog
          flowCount={selectedFlows.length}
          flows={flows.filter(f => selectedFlows.includes(f.id))}
          onConfirm={handleBatchDeleteConfirm}
          onCancel={() => setShowBatchDeleteConfirm(false)}
        />
      )}
    </div>
  );
};