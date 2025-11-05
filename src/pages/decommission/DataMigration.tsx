/**
 * Decommission Data Migration Page (Issue #944)
 *
 * Provides:
 * - Data retention policies table
 * - Archive job status tracking
 * - Backup verification results
 * - Data volume metrics
 * - Start/Pause archival buttons
 *
 * Per ADR-027: Uses snake_case field names and phase name 'data_migration'
 * Per ADR-006: MFO pattern with HTTP polling (5s active, 15s paused)
 */

import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Database,
  CheckCircle,
  XCircle,
  Clock,
  HardDrive,
  Pause,
  Play,
  AlertTriangle,
} from 'lucide-react';
import Sidebar from '../../components/layout/sidebar/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import {
  useDecommissionFlowStatus,
  useResumeDecommissionFlow,
  usePauseDecommissionFlow,
  getPhaseDisplayName,
  isFlowPaused,
} from '../../hooks/decommissionFlow/useDecommissionFlow';
import { useToast } from '@/hooks/use-toast';

interface RetentionPolicy {
  id: string;
  data_category: string;
  retention_period: string;
  archive_location: string;
  encryption: boolean;
  compliance_standard: string;
}

interface ArchiveJob {
  id: string;
  job_name: string;
  data_type: string;
  volume_gb: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress_percent: number;
  started_at?: string;
  completed_at?: string;
}

interface BackupVerification {
  id: string;
  backup_type: string;
  verification_status: 'passed' | 'failed' | 'pending';
  verified_at?: string;
  checksum_match: boolean;
  restore_tested: boolean;
}

const DataMigration: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const flowId = searchParams.get('flow_id');

  // API hooks
  const { data: flowStatus, isLoading, error } = useDecommissionFlowStatus(flowId);
  const resumeFlowMutation = useResumeDecommissionFlow();
  const pauseFlowMutation = usePauseDecommissionFlow();

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
  const retentionPolicies: RetentionPolicy[] = [
    {
      id: 'policy-001',
      data_category: 'Customer Records',
      retention_period: '7 years',
      archive_location: 'AWS Glacier Deep Archive',
      encryption: true,
      compliance_standard: 'GDPR, SOC 2',
    },
    {
      id: 'policy-002',
      data_category: 'Transaction Logs',
      retention_period: '10 years',
      archive_location: 'Azure Archive Storage',
      encryption: true,
      compliance_standard: 'PCI-DSS',
    },
    {
      id: 'policy-003',
      data_category: 'Application Logs',
      retention_period: '3 years',
      archive_location: 'S3 Intelligent-Tiering',
      encryption: true,
      compliance_standard: 'ISO 27001',
    },
  ];

  const archiveJobs: ArchiveJob[] = [
    {
      id: 'job-001',
      job_name: 'Customer Database Archive',
      data_type: 'Relational DB',
      volume_gb: 450,
      status: 'completed',
      progress_percent: 100,
      started_at: '2025-01-10T08:00:00Z',
      completed_at: '2025-01-10T14:30:00Z',
    },
    {
      id: 'job-002',
      job_name: 'Transaction Logs Archive',
      data_type: 'Log Files',
      volume_gb: 1200,
      status: 'in_progress',
      progress_percent: 67,
      started_at: '2025-01-11T09:00:00Z',
    },
    {
      id: 'job-003',
      job_name: 'Application Configs Archive',
      data_type: 'Configuration Files',
      volume_gb: 15,
      status: 'pending',
      progress_percent: 0,
    },
  ];

  const backupVerifications: BackupVerification[] = [
    {
      id: 'verify-001',
      backup_type: 'Full Database Backup',
      verification_status: 'passed',
      verified_at: '2025-01-09T16:00:00Z',
      checksum_match: true,
      restore_tested: true,
    },
    {
      id: 'verify-002',
      backup_type: 'Incremental Logs Backup',
      verification_status: 'passed',
      verified_at: '2025-01-10T10:00:00Z',
      checksum_match: true,
      restore_tested: false,
    },
    {
      id: 'verify-003',
      backup_type: 'Configuration Backup',
      verification_status: 'pending',
      checksum_match: false,
      restore_tested: false,
    },
  ];

  const dataVolumeMetrics = {
    total_data_gb: 1665,
    archived_gb: 450,
    remaining_gb: 1215,
    estimated_time_hours: 18,
  };

  const handleStartArchival = async () => {
    if (!flowId) return;

    try {
      await resumeFlowMutation.mutateAsync({
        flowId,
        params: {
          phase: 'data_migration',
          user_input: { archival_started: true },
        },
      });

      toast({
        title: 'Archival started',
        description: 'Data migration jobs are now running',
      });
    } catch (error) {
      toast({
        title: 'Failed to start archival',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handlePauseArchival = async () => {
    if (!flowId) return;

    try {
      await pauseFlowMutation.mutateAsync(flowId);

      toast({
        title: 'Archival paused',
        description: 'Data migration jobs have been paused',
      });
    } catch (error) {
      toast({
        title: 'Failed to pause archival',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleContinueToShutdown = () => {
    if (!flowId) return;
    navigate(`/decommission/shutdown?flow_id=${flowId}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading data migration status...</p>
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
  const phaseProgress = flowStatus.phase_progress?.data_migration || 'pending';
  const isPaused = isFlowPaused(flowStatus.status);

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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Migration</h1>
                  <p className="text-lg text-gray-600">
                    Archive critical data and verify backups before shutdown
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Flow ID: {flowStatus.flow_id} | Phase:{' '}
                    {getPhaseDisplayName(currentPhase)} | Status: {phaseProgress}
                  </p>
                </div>
                <div className="flex space-x-3">
                  {isPaused ? (
                    <button
                      onClick={handleStartArchival}
                      disabled={resumeFlowMutation.isPending}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                    >
                      <Play className="h-5 w-5" />
                      <span>Start Archival</span>
                    </button>
                  ) : (
                    <button
                      onClick={handlePauseArchival}
                      disabled={pauseFlowMutation.isPending}
                      className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                    >
                      <Pause className="h-5 w-5" />
                      <span>Pause Archival</span>
                    </button>
                  )}
                  <button
                    onClick={handleContinueToShutdown}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Continue to Shutdown
                  </button>
                </div>
              </div>
            </div>

            {/* Data Volume Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <HardDrive className="h-8 w-8 text-blue-600 mb-2" />
                <p className="text-sm text-gray-600">Total Data</p>
                <p className="text-2xl font-bold text-gray-900">
                  {dataVolumeMetrics.total_data_gb} GB
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <CheckCircle className="h-8 w-8 text-green-600 mb-2" />
                <p className="text-sm text-gray-600">Archived</p>
                <p className="text-2xl font-bold text-green-600">
                  {dataVolumeMetrics.archived_gb} GB
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{
                      width: `${
                        (dataVolumeMetrics.archived_gb / dataVolumeMetrics.total_data_gb) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <Database className="h-8 w-8 text-yellow-600 mb-2" />
                <p className="text-sm text-gray-600">Remaining</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {dataVolumeMetrics.remaining_gb} GB
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <Clock className="h-8 w-8 text-purple-600 mb-2" />
                <p className="text-sm text-gray-600">Est. Time</p>
                <p className="text-2xl font-bold text-purple-600">
                  {dataVolumeMetrics.estimated_time_hours}h
                </p>
              </div>
            </div>

            {/* Retention Policies */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Data Retention Policies</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Data Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Retention Period
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Archive Location
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Encryption
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Compliance
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {retentionPolicies.map((policy) => (
                      <tr key={policy.id}>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          {policy.data_category}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {policy.retention_period}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {policy.archive_location}
                        </td>
                        <td className="px-6 py-4">
                          {policy.encryption ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-600" />
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {policy.compliance_standard}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Archive Jobs */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Archive Job Status</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {archiveJobs.map((job) => (
                      <div key={job.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">{job.job_name}</h3>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              job.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : job.status === 'in_progress'
                                ? 'bg-blue-100 text-blue-800'
                                : job.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {job.status.toUpperCase().replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {job.data_type} • {job.volume_gb} GB
                        </p>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div
                            className={`h-2 rounded-full ${
                              job.status === 'completed'
                                ? 'bg-green-500'
                                : job.status === 'in_progress'
                                ? 'bg-blue-500'
                                : 'bg-gray-400'
                            }`}
                            style={{ width: `${job.progress_percent}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500">
                          {job.progress_percent}% complete
                          {job.started_at && ` • Started: ${new Date(job.started_at).toLocaleString()}`}
                          {job.completed_at && ` • Completed: ${new Date(job.completed_at).toLocaleString()}`}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Backup Verification */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Backup Verification Results
                  </h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {backupVerifications.map((verification) => (
                      <div key={verification.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900">
                            {verification.backup_type}
                          </h3>
                          {verification.verification_status === 'passed' ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : verification.verification_status === 'failed' ? (
                            <XCircle className="h-5 w-5 text-red-600" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-yellow-600" />
                          )}
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <div className="flex items-center space-x-2">
                            <span>Checksum Match:</span>
                            {verification.checksum_match ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-600" />
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <span>Restore Tested:</span>
                            {verification.restore_tested ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-gray-400" />
                            )}
                          </div>
                          {verification.verified_at && (
                            <p className="text-xs text-gray-500">
                              Verified: {new Date(verification.verified_at).toLocaleString()}
                            </p>
                          )}
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

export default DataMigration;
