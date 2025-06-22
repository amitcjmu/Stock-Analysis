import React, { useState } from 'react';
import { 
  MapPin, 
  Zap, 
  Server, 
  Network, 
  AlertTriangle, 
  Activity,
  Play,
  Trash2,
  ExternalLink,
  CheckCircle,
  Circle,
  Clock,
  Users,
  Database,
  FileText,
  Eye,
  MoreHorizontal,
  Calendar,
  TrendingUp
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { IncompleteFlow } from '@/hooks/discovery/useIncompleteFlowDetection';
import { FlowDeletionConfirmDialog } from './FlowDeletionConfirmDialog';
import { BatchDeletionConfirmDialog } from './BatchDeletionConfirmDialog';

interface IncompleteFlowManagerProps {
  flows: IncompleteFlow[];
  onContinueFlow: (sessionId: string) => void;
  onDeleteFlow: (sessionId: string) => void;
  onBatchDelete: (sessionIds: string[]) => void;
  onViewDetails: (sessionId: string, phase: string) => void;
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
    return icons[phase as keyof typeof icons] || Activity;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPhaseDisplayName = (phase: string) => {
    const names = {
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing',
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Tech Debt Analysis'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedFlows(flows.map(f => f.session_id));
    } else {
      setSelectedFlows([]);
    }
  };

  const handleFlowSelection = (sessionId: string, checked: boolean) => {
    if (checked) {
      setSelectedFlows([...selectedFlows, sessionId]);
    } else {
      setSelectedFlows(selectedFlows.filter(id => id !== sessionId));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-2 bg-gray-200 rounded"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (flows.length === 0) {
    return (
      <Alert className="border-green-200 bg-green-50">
        <CheckCircle className="h-5 w-5 text-green-600" />
        <AlertDescription className="text-green-800">
          <strong>No Incomplete Flows:</strong> All discovery flows are complete. You can start a new discovery flow.
        </AlertDescription>
      </Alert>
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
        
        {flows.length > 0 && (
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={selectedFlows.length === flows.length}
                onCheckedChange={handleSelectAll}
              />
              <span className="text-sm text-gray-600">Select All</span>
            </div>
            
            {selectedFlows.length > 0 && (
              <div className="flex items-center space-x-3 border-l pl-3">
                <span className="text-sm text-gray-600">
                  {selectedFlows.length} selected
                </span>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowBatchDeleteConfirm(true)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Selected
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Flow list */}
      <div className="space-y-4">
        {flows.map((flow) => {
          const PhaseIcon = getPhaseIcon(flow.current_phase);
          const isSelected = selectedFlows.includes(flow.session_id);
          
          return (
            <Card key={flow.session_id} className={`overflow-hidden transition-all hover:shadow-md ${
              isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''
            }`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => 
                        handleFlowSelection(flow.session_id, checked as boolean)
                      }
                    />
                    <div className="flex items-center space-x-2">
                      <PhaseIcon className="h-5 w-5 text-blue-600" />
                      <div>
                        <h3 className="font-semibold">
                          {getPhaseDisplayName(flow.current_phase)} Phase
                        </h3>
                        <p className="text-sm text-gray-600">
                          Session: {flow.session_id.substring(0, 8)}...
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(flow.status)}>
                      {flow.status.toUpperCase()}
                    </Badge>
                    <Badge variant="outline">
                      {Math.round(flow.progress_percentage)}% Complete
                    </Badge>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onViewDetails(flow.session_id, flow.current_phase)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {flow.can_resume && (
                          <DropdownMenuItem onClick={() => onContinueFlow(flow.session_id)}>
                            <Play className="h-4 w-4 mr-2" />
                            Continue Flow
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem 
                          onClick={() => setShowDeleteConfirm(flow.session_id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Flow
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                {/* Progress bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="font-medium">Overall Progress</span>
                    <span>{Math.round(flow.progress_percentage)}%</span>
                  </div>
                  <Progress value={flow.progress_percentage} className="h-2" />
                </div>

                {/* Phase completion status */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
                  {Object.entries(flow.phase_completion).map(([phase, completed]) => (
                    <div key={phase} className="flex items-center space-x-1">
                      {completed ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <Circle className="h-4 w-4 text-gray-300" />
                      )}
                      <span className="text-xs text-gray-600 capitalize">
                        {getPhaseDisplayName(phase)}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Flow metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Created</p>
                      <p className="text-sm font-medium">{formatTimeAgo(flow.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Last Activity</p>
                      <p className="text-sm font-medium">{formatTimeAgo(flow.updated_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Database className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Data Records</p>
                      <p className="text-sm font-medium">
                        {flow.deletion_impact.data_to_delete.assets || 0}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Cleanup Time</p>
                      <p className="text-sm font-medium">
                        {flow.deletion_impact.estimated_cleanup_time}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Recent agent insights */}
                {flow.agent_insights.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                      <Users className="h-4 w-4 mr-1" />
                      Recent Agent Insights
                    </h4>
                    <div className="space-y-2">
                      {flow.agent_insights.slice(0, 2).map((insight, idx) => (
                        <div key={idx} className="text-xs bg-gray-50 p-3 rounded-lg border">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-gray-700 capitalize">
                              {getPhaseDisplayName(insight.phase)}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {Math.round(insight.confidence * 100)}% confidence
                            </Badge>
                          </div>
                          <p className="text-gray-600">{insight.insight}</p>
                          <p className="text-gray-400 mt-1">
                            {formatTimeAgo(insight.timestamp)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Separator className="my-4" />

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {flow.can_resume && (
                      <Button
                        size="sm"
                        onClick={() => onContinueFlow(flow.session_id)}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Continue Flow
                      </Button>
                    )}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewDetails(flow.session_id, flow.current_phase)}
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                  
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setShowDeleteConfirm(flow.session_id)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Delete confirmation dialogs */}
      {showDeleteConfirm && (
        <FlowDeletionConfirmDialog
          flow={flows.find(f => f.session_id === showDeleteConfirm)!}
          onConfirm={() => {
            onDeleteFlow(showDeleteConfirm);
            setShowDeleteConfirm(null);
          }}
          onCancel={() => setShowDeleteConfirm(null)}
        />
      )}

      {showBatchDeleteConfirm && (
        <BatchDeletionConfirmDialog
          flowCount={selectedFlows.length}
          flows={flows.filter(f => selectedFlows.includes(f.session_id))}
          onConfirm={() => {
            onBatchDelete(selectedFlows);
            setSelectedFlows([]);
            setShowBatchDeleteConfirm(false);
          }}
          onCancel={() => setShowBatchDeleteConfirm(false)}
        />
      )}
    </div>
  );
}; 