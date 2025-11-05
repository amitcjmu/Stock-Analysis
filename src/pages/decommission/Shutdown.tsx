/**
 * Decommission System Shutdown Page (Issue #945)
 *
 * Provides:
 * - Pre-shutdown validation checklist
 * - System shutdown status
 * - Post-shutdown validation results
 * - Resource cleanup tracking
 * - Execute/Rollback buttons
 *
 * Per ADR-027: Uses snake_case field names and phase name 'system_shutdown'
 * Per ADR-006: MFO pattern with HTTP polling (5s active, 15s paused)
 */

import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Power,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Trash2,
  RotateCcw,
  Shield,
  Server,
} from 'lucide-react';
import Sidebar from '../../components/layout/sidebar/Sidebar';
import {
  useDecommissionFlowStatus,
  useResumeDecommissionFlow,
  useCancelDecommissionFlow,
  getPhaseDisplayName,
} from '../../hooks/decommissionFlow/useDecommissionFlow';
import { useToast } from '@/hooks/use-toast';

interface ValidationItem {
  id: string;
  check_name: string;
  status: 'passed' | 'failed' | 'pending';
  severity: 'critical' | 'high' | 'medium' | 'low';
  details: string;
  checked_at?: string;
}

interface SystemShutdownStatus {
  id: string;
  system_name: string;
  shutdown_status: 'pending' | 'in_progress' | 'completed' | 'failed';
  shutdown_at?: string;
  rollback_available: boolean;
}

interface ResourceCleanup {
  id: string;
  resource_type: string;
  resource_name: string;
  cleanup_status: 'pending' | 'in_progress' | 'completed' | 'failed';
  estimated_savings: string;
}

const Shutdown: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'execute' | 'rollback' | null>(null);

  const flowId = searchParams.get('flow_id');

  // API hooks
  const { data: flowStatus, isLoading, error } = useDecommissionFlowStatus(flowId);
  const resumeFlowMutation = useResumeDecommissionFlow();
  const cancelFlowMutation = useCancelDecommissionFlow();

  // Redirect if no flow_id
  useEffect(() => {
    if (!flowId) {
      toast({
        title: 'No flow selected',
        description: 'Please initialize a decommission flow first',
        variant: 'destructive',
      });
      navigate('/decommission');
    }
  }, [flowId, navigate, toast]);

  // Mock data (TODO: Extract from flowStatus.runtime_state when available)
  const preShutdownValidation: ValidationItem[] = [
    {
      id: 'val-001',
      check_name: 'All dependencies migrated',
      status: 'passed',
      severity: 'critical',
      details: 'All dependent systems confirmed migration complete',
      checked_at: '2025-01-15T10:00:00Z',
    },
    {
      id: 'val-002',
      check_name: 'Data archival complete',
      status: 'passed',
      severity: 'critical',
      details: '100% of data successfully archived and verified',
      checked_at: '2025-01-15T10:15:00Z',
    },
    {
      id: 'val-003',
      check_name: 'Stakeholder approvals obtained',
      status: 'passed',
      severity: 'high',
      details: 'All required sign-offs received',
      checked_at: '2025-01-15T09:30:00Z',
    },
    {
      id: 'val-004',
      check_name: 'Rollback plan validated',
      status: 'passed',
      severity: 'high',
      details: 'Rollback procedures tested and documented',
      checked_at: '2025-01-15T09:45:00Z',
    },
    {
      id: 'val-005',
      check_name: 'No active user sessions',
      status: 'pending',
      severity: 'medium',
      details: 'Checking for active connections',
    },
  ];

  const systemsStatus: SystemShutdownStatus[] = [
    {
      id: 'sys-001',
      system_name: 'Legacy Mainframe System',
      shutdown_status: 'completed',
      shutdown_at: '2025-01-15T11:00:00Z',
      rollback_available: true,
    },
    {
      id: 'sys-002',
      system_name: 'Old CRM Database',
      shutdown_status: 'in_progress',
      rollback_available: true,
    },
    {
      id: 'sys-003',
      system_name: 'Legacy Web Server',
      shutdown_status: 'pending',
      rollback_available: true,
    },
  ];

  const postShutdownValidation: ValidationItem[] = [
    {
      id: 'post-001',
      check_name: 'Service endpoints unreachable',
      status: 'passed',
      severity: 'critical',
      details: 'All service endpoints confirmed down',
      checked_at: '2025-01-15T11:05:00Z',
    },
    {
      id: 'post-002',
      check_name: 'No data loss detected',
      status: 'passed',
      severity: 'critical',
      details: 'Data integrity checks passed',
      checked_at: '2025-01-15T11:10:00Z',
    },
    {
      id: 'post-003',
      check_name: 'Dependent systems operational',
      status: 'pending',
      severity: 'high',
      details: 'Monitoring dependent system health',
    },
  ];

  const resourceCleanup: ResourceCleanup[] = [
    {
      id: 'res-001',
      resource_type: 'Compute Instance',
      resource_name: 'mainframe-prod-01',
      cleanup_status: 'completed',
      estimated_savings: '$5,000/month',
    },
    {
      id: 'res-002',
      resource_type: 'Storage Volume',
      resource_name: 'crm-data-volume',
      cleanup_status: 'in_progress',
      estimated_savings: '$1,200/month',
    },
    {
      id: 'res-003',
      resource_type: 'Network Load Balancer',
      resource_name: 'web-server-lb',
      cleanup_status: 'pending',
      estimated_savings: '$800/month',
    },
  ];

  const handleExecuteShutdown = async () => {
    if (!flowId) return;

    setShowConfirmModal(false);
    setConfirmAction(null);

    try {
      await resumeFlowMutation.mutateAsync({
        flowId,
        params: {
          phase: 'system_shutdown',
          user_input: { shutdown_confirmed: true },
        },
      });

      toast({
        title: 'Shutdown initiated',
        description: 'Systems are being shut down safely',
      });
    } catch (error) {
      toast({
        title: 'Failed to execute shutdown',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleRollback = async () => {
    if (!flowId) return;

    setShowConfirmModal(false);
    setConfirmAction(null);

    try {
      await cancelFlowMutation.mutateAsync(flowId);

      toast({
        title: 'Rollback initiated',
        description: 'Systems are being restored to previous state',
      });

      navigate('/decommission');
    } catch (error) {
      toast({
        title: 'Failed to rollback',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const openConfirmModal = (action: 'execute' | 'rollback') => {
    setConfirmAction(action);
    setShowConfirmModal(true);
  };

  const handleConfirm = () => {
    if (confirmAction === 'execute') {
      handleExecuteShutdown();
    } else if (confirmAction === 'rollback') {
      handleRollback();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading shutdown status...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !flowStatus) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center">
            <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
            <p className="text-gray-600">Failed to load flow data</p>
            <button
              onClick={() => navigate('/decommission')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to Overview
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentPhase = flowStatus.current_phase;
  const phaseProgress = flowStatus.phase_progress?.system_shutdown || 'pending';

  const allPreChecksPassedOrPending = preShutdownValidation.every(
    (item) => item.status === 'passed' || item.status === 'pending'
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">System Shutdown</h1>
                  <p className="text-lg text-gray-600">
                    Execute safe system shutdown with validation and rollback capability
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Flow ID: {flowStatus.flow_id} | Phase:{' '}
                    {getPhaseDisplayName(currentPhase)} | Status: {phaseProgress}
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => openConfirmModal('rollback')}
                    disabled={cancelFlowMutation.isPending}
                    className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                  >
                    <RotateCcw className="h-5 w-5" />
                    <span>Rollback</span>
                  </button>
                  <button
                    onClick={() => openConfirmModal('execute')}
                    disabled={!allPreChecksPassedOrPending || resumeFlowMutation.isPending}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                  >
                    <Power className="h-5 w-5" />
                    <span>Execute Shutdown</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Warning Banner */}
            {!allPreChecksPassedOrPending && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  <div>
                    <h3 className="font-semibold text-yellow-900">
                      Pre-shutdown validation incomplete
                    </h3>
                    <p className="text-sm text-yellow-800">
                      Some validation checks have not passed. Review before proceeding.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Pre-Shutdown Validation */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <Shield className="h-6 w-6 text-blue-600" />
                  <h2 className="text-xl font-semibold text-gray-900">
                    Pre-Shutdown Validation
                  </h2>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {preShutdownValidation.map((item) => (
                    <div
                      key={item.id}
                      className={`border rounded-lg p-4 ${
                        item.status === 'failed' ? 'border-red-300 bg-red-50' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        {item.status === 'passed' ? (
                          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                        ) : item.status === 'failed' ? (
                          <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                        ) : (
                          <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h3 className="font-medium text-gray-900">{item.check_name}</h3>
                            <span
                              className={`px-2 py-1 text-xs rounded-full ${
                                item.severity === 'critical'
                                  ? 'bg-red-100 text-red-800'
                                  : item.severity === 'high'
                                  ? 'bg-orange-100 text-orange-800'
                                  : item.severity === 'medium'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {item.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{item.details}</p>
                          {item.checked_at && (
                            <p className="text-xs text-gray-500 mt-1">
                              Checked: {new Date(item.checked_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* System Shutdown Status */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Server className="h-6 w-6 text-red-600" />
                    <h2 className="text-xl font-semibold text-gray-900">
                      System Shutdown Status
                    </h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {systemsStatus.map((system) => (
                      <div key={system.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">{system.system_name}</h3>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              system.shutdown_status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : system.shutdown_status === 'in_progress'
                                ? 'bg-blue-100 text-blue-800'
                                : system.shutdown_status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {system.shutdown_status.toUpperCase().replace('_', ' ')}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm text-gray-600">
                          <span>
                            Rollback: {system.rollback_available ? 'Available' : 'Not Available'}
                          </span>
                          {system.shutdown_at && (
                            <span className="text-xs text-gray-500">
                              {new Date(system.shutdown_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Resource Cleanup */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Trash2 className="h-6 w-6 text-purple-600" />
                    <h2 className="text-xl font-semibold text-gray-900">Resource Cleanup</h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {resourceCleanup.map((resource) => (
                      <div key={resource.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {resource.resource_name}
                            </h3>
                            <p className="text-sm text-gray-600">{resource.resource_type}</p>
                          </div>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              resource.cleanup_status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : resource.cleanup_status === 'in_progress'
                                ? 'bg-blue-100 text-blue-800'
                                : resource.cleanup_status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {resource.cleanup_status.toUpperCase().replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-green-600 font-medium">
                          Savings: {resource.estimated_savings}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Post-Shutdown Validation */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                  <h2 className="text-xl font-semibold text-gray-900">
                    Post-Shutdown Validation
                  </h2>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {postShutdownValidation.map((item) => (
                    <div key={item.id} className="border rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        {item.status === 'passed' ? (
                          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                        ) : item.status === 'failed' ? (
                          <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                        ) : (
                          <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h3 className="font-medium text-gray-900">{item.check_name}</h3>
                            <span
                              className={`px-2 py-1 text-xs rounded-full ${
                                item.severity === 'critical'
                                  ? 'bg-red-100 text-red-800'
                                  : item.severity === 'high'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {item.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{item.details}</p>
                          {item.checked_at && (
                            <p className="text-xs text-gray-500 mt-1">
                              Checked: {new Date(item.checked_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {confirmAction === 'execute' ? 'Confirm Shutdown' : 'Confirm Rollback'}
            </h2>
            <p className="text-gray-600 mb-6">
              {confirmAction === 'execute'
                ? 'Are you sure you want to execute the system shutdown? This action will shut down all selected systems.'
                : 'Are you sure you want to rollback? This will restore systems to their previous state and cancel the decommission flow.'}
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowConfirmModal(false);
                  setConfirmAction(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                className={`px-4 py-2 rounded-lg text-white ${
                  confirmAction === 'execute'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-yellow-600 hover:bg-yellow-700'
                }`}
              >
                {confirmAction === 'execute' ? 'Execute Shutdown' : 'Confirm Rollback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Shutdown;
