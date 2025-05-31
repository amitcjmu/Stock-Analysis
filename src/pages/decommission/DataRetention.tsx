
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import { Database, Shield, Archive, Download, Calendar, AlertTriangle, CheckCircle, FileText, HardDrive } from 'lucide-react';

const DataRetention = () => {
  const [selectedPolicy, setSelectedPolicy] = useState('all');
  
  const retentionMetrics = [
    { label: 'Data Archived', value: '2.4 TB', color: 'text-blue-600', icon: Database },
    { label: 'Active Policies', value: '12', color: 'text-green-600', icon: Shield },
    { label: 'Compliance Requirements', value: '8', color: 'text-purple-600', icon: FileText },
    { label: 'Storage Saved', value: '$180K', color: 'text-orange-600', icon: HardDrive },
  ];

  const retentionPolicies = [
    {
      id: 'POL001',
      name: 'Financial Data Retention',
      description: 'SOX compliance for financial records',
      retentionPeriod: '7 years',
      complianceReqs: ['SOX', 'IRS'],
      dataTypes: ['Transaction Records', 'Audit Logs', 'Financial Reports'],
      storageLocation: 'S3 Glacier Deep Archive',
      status: 'Active',
      affectedSystems: 8
    },
    {
      id: 'POL002',
      name: 'Customer Data Retention',
      description: 'GDPR compliance for customer information',
      retentionPeriod: '5 years',
      complianceReqs: ['GDPR', 'CCPA'],
      dataTypes: ['Customer Records', 'Communications', 'Preferences'],
      storageLocation: 'Encrypted Cloud Storage',
      status: 'Active',
      affectedSystems: 12
    },
    {
      id: 'POL003',
      name: 'Healthcare Data Retention',
      description: 'HIPAA compliance for health records',
      retentionPeriod: '10 years',
      complianceReqs: ['HIPAA', 'HITECH'],
      dataTypes: ['Patient Records', 'Medical Images', 'Treatment Plans'],
      storageLocation: 'HIPAA Compliant Archive',
      status: 'Under Review',
      affectedSystems: 5
    },
    {
      id: 'POL004',
      name: 'Technical Documentation',
      description: 'System documentation and logs',
      retentionPeriod: '3 years',
      complianceReqs: ['Internal Policy'],
      dataTypes: ['System Logs', 'Documentation', 'Configuration Files'],
      storageLocation: 'S3 Standard',
      status: 'Draft',
      affectedSystems: 15
    },
  ];

  const archiveJobs = [
    {
      id: 'JOB001',
      systemName: 'Legacy CRM Database',
      dataSize: '450 GB',
      status: 'In Progress',
      progress: 65,
      startDate: '2025-01-15',
      estimatedCompletion: '2025-01-20',
      priority: 'High',
      policy: 'Customer Data Retention'
    },
    {
      id: 'JOB002',
      systemName: 'Financial Reporting System',
      dataSize: '1.2 TB',
      status: 'Queued',
      progress: 0,
      startDate: '2025-01-22',
      estimatedCompletion: '2025-01-28',
      priority: 'High',
      policy: 'Financial Data Retention'
    },
    {
      id: 'JOB003',
      systemName: 'Old Email Server',
      dataSize: '800 GB',
      status: 'Completed',
      progress: 100,
      startDate: '2025-01-10',
      estimatedCompletion: '2025-01-14',
      priority: 'Medium',
      policy: 'Technical Documentation'
    },
  ];

  const dataRetentionSteps = [
    {
      step: 1,
      title: 'Data Classification',
      description: 'Classify data based on compliance requirements',
      status: 'completed'
    },
    {
      step: 2,
      title: 'Policy Definition',
      description: 'Define retention policies for each data type',
      status: 'completed'
    },
    {
      step: 3,
      title: 'Archive Preparation',
      description: 'Prepare data for archival storage',
      status: 'in-progress'
    },
    {
      step: 4,
      title: 'Data Migration',
      description: 'Move data to compliant archive storage',
      status: 'in-progress'
    },
    {
      step: 5,
      title: 'Verification',
      description: 'Verify data integrity and accessibility',
      status: 'pending'
    }
  ];

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
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export Policies</span>
                  </button>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Archive className="h-5 w-5" />
                    <span>Create Archive Job</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Retention Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {retentionMetrics.map((metric, index) => {
                const Icon = metric.icon;
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
                        <div className="text-sm text-gray-600">
                          <div className="flex justify-between">
                            <span>Started: {job.startDate}</span>
                            <span>ETC: {job.estimatedCompletion}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Retention Policies */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">Retention Policies</h3>
                    <select
                      value={selectedPolicy}
                      onChange={(e) => setSelectedPolicy(e.target.value)}
                      className="border border-gray-300 rounded-lg px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Policies</option>
                      <option value="active">Active</option>
                      <option value="review">Under Review</option>
                      <option value="draft">Draft</option>
                    </select>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {retentionPolicies
                      .filter(policy => selectedPolicy === 'all' || policy.status.toLowerCase().includes(selectedPolicy))
                      .map((policy) => (
                      <div key={policy.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-medium text-gray-900">{policy.name}</h4>
                            <p className="text-sm text-gray-600">{policy.description}</p>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            policy.status === 'Active' ? 'bg-green-100 text-green-800' :
                            policy.status === 'Under Review' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {policy.status}
                          </span>
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Retention Period:</span>
                            <span className="font-medium">{policy.retentionPeriod}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Affected Systems:</span>
                            <span className="font-medium">{policy.affectedSystems}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Compliance:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {policy.complianceReqs.map((req, index) => (
                                <span key={index} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                                  {req}
                                </span>
                              ))}
                            </div>
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

export default DataRetention;
