import React, { useState } from 'react'
import Sidebar from '../../components/Sidebar';
import { Database, Shield, Calendar, AlertTriangle, FileText, HardDrive } from 'lucide-react'
import { Archive, Download, CheckCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext';
import { useDataRetention, useCreateArchiveJob, useUpdateRetentionPolicy } from '@/hooks/decommission/useDataRetention';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';

const DataRetention = (): JSX.Element => {
  const { isAuthenticated } = useAuth();
  const [selectedPolicy, setSelectedPolicy] = useState('all');

  const {
    data: retentionData,
    isLoading,
    error
  } = useDataRetention();

  const { mutate: createArchiveJob } = useCreateArchiveJob();
  const { mutate: updatePolicy } = useUpdateRetentionPolicy();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Authentication Required</AlertTitle>
        <AlertDescription>
          Please log in to access the data retention management.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner className="w-8 h-8" />
        <span className="ml-2">Loading data retention information...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load data retention information'}
        </AlertDescription>
      </Alert>
    );
  }

  const { metrics: retentionMetrics, policies: retentionPolicies, archiveJobs, retentionSteps: dataRetentionSteps } = retentionData || {
    metrics: [],
    policies: [],
    archiveJobs: [],
    retentionSteps: []
  };

  const handleCreateArchiveJob = (): void => {
    // Implementation for creating a new archive job
    createArchiveJob({
      systemName: 'New System',
      dataSize: '0 GB',
      status: 'Queued',
      progress: 0,
      startDate: new Date().toISOString(),
      estimatedCompletion: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      priority: selectedPolicy
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Retention & Archival</h1>
                  <p className="text-lg text-gray-600">
                    Manage data archival and compliance requirements for decommissioned systems
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Coming Soon: CloudBridge automated data classification and archival
                  </p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="secondary"
                    className="flex items-center space-x-2"
                    onClick={() => {/* Export functionality */}}
                  >
                    <Download className="h-5 w-5" />
                    <span>Export Policies</span>
                  </Button>
                  <Button
                    variant="default"
                    className="flex items-center space-x-2"
                    onClick={handleCreateArchiveJob}
                  >
                    <Archive className="h-5 w-5" />
                    <span>Create Archive Job</span>
                  </Button>
                </div>
              </div>
            </div>

            {/* Retention Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {retentionMetrics.map((metric, index) => {
                const Icon = metric.icon === 'Database' ? Database :
                           metric.icon === 'Shield' ? Shield :
                           metric.icon === 'FileText' ? FileText :
                           HardDrive;
                return (
                  <div key={index} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                        <p className={`text-2xl font-bold ${metric.color}`}>
                          {metric.value}
                        </p>
                      </div>
                      <Icon className={`h-8 w-8 ${metric.color}`} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Data Retention Process */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Data Retention Process</h3>
              </div>
              <div className="p-6">
                <div className="flex items-center justify-between">
                  {dataRetentionSteps.map((step, index) => (
                    <div key={step.step} className="flex flex-col items-center text-center">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 ${
                        step.status === 'completed' ? 'bg-green-500 text-white' :
                        step.status === 'in-progress' ? 'bg-blue-500 text-white' :
                        'bg-gray-300 text-gray-600'
                      }`}>
                        {step.status === 'completed' ? (
                          <CheckCircle className="h-6 w-6" />
                        ) : (
                          <span className="font-bold">{step.step}</span>
                        )}
                      </div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-1">{step.title}</h4>
                      <p className="text-xs text-gray-600 max-w-24">{step.description}</p>
                      {index < dataRetentionSteps.length - 1 && (
                        <div className="absolute h-px bg-gray-300 w-16 mt-6" style={{ marginLeft: '4rem' }}></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Archive Jobs and Retention Policies */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Active Archive Jobs */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Active Archive Jobs</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {archiveJobs.map((job) => (
                      <div key={job.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-medium text-gray-900">{job.systemName}</h4>
                            <p className="text-sm text-gray-600">{job.dataSize} • {job.policy}</p>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            job.status === 'Completed' ? 'bg-green-100 text-green-800' :
                            job.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {job.status}
                          </span>
                        </div>
                        {job.status === 'In Progress' && (
                          <div className="mb-3">
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Progress</span>
                              <span className="font-medium">{job.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${job.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>Started: {new Date(job.startDate).toLocaleDateString()}</span>
                          <span>ETA: {new Date(job.estimatedCompletion).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Retention Policies */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Retention Policies</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {retentionPolicies.map((policy) => (
                      <div key={policy.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{policy.name}</h4>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            policy.status === 'Active' ? 'bg-green-100 text-green-800' :
                            policy.status === 'Under Review' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {policy.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{policy.description}</p>
                        <div className="text-sm text-gray-600">
                          <p>Retention Period: {policy.retentionPeriod}</p>
                          <p>Storage: {policy.storageLocation}</p>
                          <p>Affected Systems: {policy.affectedSystems}</p>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {policy.complianceReqs.map((req, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              {req}
                            </span>
                          ))}
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

export default DataRetention;
