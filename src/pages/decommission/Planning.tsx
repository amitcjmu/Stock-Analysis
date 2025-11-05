/**
 * Decommission Planning Page (Issue #943)
 *
 * Provides:
 * - Dependency analysis results
 * - Risk assessment scores
 * - Cost estimation breakdown
 * - Compliance validation checklist
 * - Approve/Reject planning buttons
 *
 * Per ADR-027: Uses snake_case field names and phase name 'decommission_planning'
 * Per ADR-006: MFO pattern with HTTP polling (5s active, 15s paused)
 */

import React, { useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Network,
  DollarSign,
  Shield,
  TrendingUp,
  Server,
} from 'lucide-react';
import Sidebar from '../../components/layout/sidebar/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import {
  useDecommissionFlowStatus,
  useResumeDecommissionFlow,
  useCancelDecommissionFlow,
  useEligibleSystems,
  getPhaseDisplayName,
} from '../../hooks/decommissionFlow/useDecommissionFlow';
import { useToast } from '@/hooks/use-toast';

interface DependencyItem {
  id: string;
  name: string;
  type: string;
  impact: 'high' | 'medium' | 'low';
  mitigated: boolean;
}

interface ComplianceItem {
  id: string;
  requirement: string;
  status: 'compliant' | 'non_compliant' | 'pending';
  notes: string;
}

const DecommissionPlanning: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const flowId = searchParams.get('flow_id');

  // API hooks
  const { data: flowStatus, isLoading, error } = useDecommissionFlowStatus(flowId);
  const { data: eligibleSystems, isLoading: isLoadingSystems } = useEligibleSystems({
    enabled: !!flowId,
  });
  const resumeFlowMutation = useResumeDecommissionFlow();
  const cancelFlowMutation = useCancelDecommissionFlow();

  // Filter eligible systems to only show selected ones
  const selectedSystemsDetails = useMemo(() => {
    if (!flowStatus?.selected_systems || !eligibleSystems) return [];

    // selected_systems is an array of UUID strings
    const selectedIds = new Set(flowStatus.selected_systems);

    return eligibleSystems.filter(system => selectedIds.has(system.asset_id));
  }, [flowStatus?.selected_systems, eligibleSystems]);

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

  // Mock planning data (TODO: Extract from flowStatus.runtime_state when available)
  const dependencies: DependencyItem[] = [
    {
      id: 'dep-001',
      name: 'Customer Portal API',
      type: 'Upstream Dependency',
      impact: 'high',
      mitigated: true,
    },
    {
      id: 'dep-002',
      name: 'Reporting Database',
      type: 'Data Consumer',
      impact: 'medium',
      mitigated: true,
    },
    {
      id: 'dep-003',
      name: 'Legacy File Server',
      type: 'Storage Dependency',
      impact: 'low',
      mitigated: false,
    },
  ];

  const riskAssessment = {
    overall_score: 72,
    business_impact: 'medium',
    technical_complexity: 'high',
    data_sensitivity: 'medium',
    rollback_feasibility: 'high',
  };

  const costEstimation = {
    decommission_cost: 45000,
    annual_savings: 120000,
    roi_months: 4.5,
    payback_period: '5 months',
  };

  const complianceChecklist: ComplianceItem[] = [
    {
      id: 'comp-001',
      requirement: 'Data retention policy documented',
      status: 'compliant',
      notes: '7-year retention approved',
    },
    {
      id: 'comp-002',
      requirement: 'Stakeholder sign-offs obtained',
      status: 'compliant',
      notes: 'All stakeholders approved',
    },
    {
      id: 'comp-003',
      requirement: 'Security clearance for data archival',
      status: 'pending',
      notes: 'Awaiting InfoSec review',
    },
    {
      id: 'comp-004',
      requirement: 'Backup verification completed',
      status: 'compliant',
      notes: 'Full backup verified on 2025-01-15',
    },
  ];

  const handleApprovePlanning = async () => {
    if (!flowId) return;

    try {
      await resumeFlowMutation.mutateAsync({
        flowId,
        params: {
          phase: 'data_migration', // Move to next phase
          user_input: { planning_approved: true },
        },
      });

      toast({
        title: 'Planning approved',
        description: 'Moving to Data Migration phase',
      });

      navigate(`/decommission/data-migration?flow_id=${flowId}`);
    } catch (error) {
      toast({
        title: 'Failed to approve planning',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleRejectPlanning = async () => {
    if (!flowId) return;

    const confirmed = window.confirm(
      'Are you sure you want to reject this planning? The flow will be cancelled.'
    );

    if (!confirmed) return;

    try {
      await cancelFlowMutation.mutateAsync(flowId);

      toast({
        title: 'Planning rejected',
        description: 'Decommission flow has been cancelled',
      });

      navigate('/decommission');
    } catch (error) {
      toast({
        title: 'Failed to reject planning',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading planning data...</p>
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
  const phaseProgress = flowStatus.phase_progress?.decommission_planning || 'pending';

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <ContextBreadcrumbs />
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Decommission Planning
                  </h1>
                  <p className="text-lg text-gray-600">
                    Review dependencies, risks, and costs before proceeding
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Flow ID: {flowStatus.flow_id} | Phase:{' '}
                    {getPhaseDisplayName(currentPhase)} | Status: {phaseProgress}
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={handleRejectPlanning}
                    disabled={cancelFlowMutation.isPending}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                  >
                    Reject Planning
                  </button>
                  <button
                    onClick={handleApprovePlanning}
                    disabled={resumeFlowMutation.isPending}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    Approve & Continue
                  </button>
                </div>
              </div>
            </div>

            {/* Selected Systems Section */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Server className="h-6 w-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Selected Systems ({flowStatus.selected_systems?.length || 0})
                </h2>
              </div>

              {isLoadingSystems ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                  <span className="ml-3 text-gray-600">Loading system details...</span>
                </div>
              ) : selectedSystemsDetails.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No systems found for this flow.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {selectedSystemsDetails.map((system) => (
                    <div
                      key={system.asset_id}
                      className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="font-semibold text-gray-900 flex-1">
                          {system.asset_name}
                        </h3>
                        {system.six_r_strategy && system.six_r_strategy.toLowerCase().includes('retire') && (
                          <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                            RETIRE
                          </span>
                        )}
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">6R Strategy:</span>
                          <span className="font-medium text-gray-900">
                            {system.six_r_strategy || 'Not assessed'}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-gray-600">Annual Cost:</span>
                          <span className="font-medium text-green-600">
                            ${system.annual_cost?.toLocaleString() || '0'}
                          </span>
                        </div>

                        {system.retirement_reason && (
                          <div className="mt-2 pt-2 border-t border-gray-100">
                            <p className="text-xs text-gray-600 italic">
                              {system.retirement_reason}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Risk Assessment Summary */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
                <h2 className="text-xl font-semibold text-gray-900">Risk Assessment</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Overall Score</p>
                  <p className="text-2xl font-bold text-gray-900">{riskAssessment.overall_score}/100</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Business Impact</p>
                  <p className="text-lg font-semibold text-yellow-600 capitalize">
                    {riskAssessment.business_impact}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Technical Complexity</p>
                  <p className="text-lg font-semibold text-red-600 capitalize">
                    {riskAssessment.technical_complexity}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Data Sensitivity</p>
                  <p className="text-lg font-semibold text-yellow-600 capitalize">
                    {riskAssessment.data_sensitivity}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Rollback Feasibility</p>
                  <p className="text-lg font-semibold text-green-600 capitalize">
                    {riskAssessment.rollback_feasibility}
                  </p>
                </div>
              </div>
            </div>

            {/* Cost Estimation */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <DollarSign className="h-6 w-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">Cost Estimation</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Decommission Cost</p>
                  <p className="text-2xl font-bold text-red-600">
                    ${costEstimation.decommission_cost.toLocaleString()}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Annual Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${costEstimation.annual_savings.toLocaleString()}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">ROI</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {costEstimation.roi_months.toFixed(1)}x
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Payback Period</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {costEstimation.payback_period}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Dependency Analysis */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Network className="h-6 w-6 text-blue-600" />
                    <h2 className="text-xl font-semibold text-gray-900">
                      Dependency Analysis
                    </h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {dependencies.map((dep) => (
                      <div key={dep.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">{dep.name}</h3>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              dep.impact === 'high'
                                ? 'bg-red-100 text-red-800'
                                : dep.impact === 'medium'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {dep.impact.toUpperCase()} IMPACT
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{dep.type}</p>
                        <div className="flex items-center space-x-2">
                          {dep.mitigated ? (
                            <>
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              <span className="text-sm text-green-600">Mitigated</span>
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="h-4 w-4 text-yellow-600" />
                              <span className="text-sm text-yellow-600">
                                Mitigation Required
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Compliance Validation */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Shield className="h-6 w-6 text-purple-600" />
                    <h2 className="text-xl font-semibold text-gray-900">
                      Compliance Checklist
                    </h2>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {complianceChecklist.map((item) => (
                      <div key={item.id} className="border rounded-lg p-4">
                        <div className="flex items-start space-x-3 mb-2">
                          {item.status === 'compliant' ? (
                            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                          ) : item.status === 'non_compliant' ? (
                            <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900">{item.requirement}</h3>
                            <p className="text-sm text-gray-600 mt-1">{item.notes}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DecommissionPlanning;
