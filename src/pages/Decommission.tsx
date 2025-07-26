
import React, { useState } from 'react'
import Sidebar from '../components/Sidebar';
import { Archive, Database, FileText } from 'lucide-react'
import { Shield, Trash2, Clock, CheckCircle, AlertTriangle } from 'lucide-react'

const Decommission = (): JSX.Element => {
  const [selectedPhase, setSelectedPhase] = useState('planning');

  const decommissionQueue = [
    {
      id: 'D001',
      system: 'Legacy Mainframe System',
      type: 'Application',
      dataRetention: '7 years',
      decommissionDate: '2025-03-15',
      status: 'Planning',
      dependencies: 3,
      complianceReqs: ['SOX', 'HIPAA'],
      estimatedSavings: '$120,000/year'
    },
    {
      id: 'D002',
      system: 'Old CRM Database',
      type: 'Database',
      dataRetention: '5 years',
      decommissionDate: '2025-02-28',
      status: 'Ready',
      dependencies: 0,
      complianceReqs: ['GDPR'],
      estimatedSavings: '$45,000/year'
    },
    {
      id: 'D003',
      system: 'Legacy Web Server',
      type: 'Infrastructure',
      dataRetention: '3 years',
      decommissionDate: '2025-04-10',
      status: 'In Progress',
      dependencies: 1,
      complianceReqs: ['PCI DSS'],
      estimatedSavings: '$30,000/year'
    },
  ];

  const decommissionMetrics = [
    { label: 'Systems Decommissioned', value: '18', total: '45', percentage: 40 },
    { label: 'Annual Savings', value: '$2.4M', color: 'text-green-600' },
    { label: 'Data Archived', value: '1.2 TB', color: 'text-blue-600' },
    { label: 'Compliance Score', value: '98%', color: 'text-purple-600' },
  ];

  const decommissionPhases = [
    {
      id: 'planning',
      name: 'Planning & Assessment',
      icon: FileText,
      description: 'Identify systems for decommission and assess dependencies',
      systems: 12,
      completed: 8
    },
    {
      id: 'data-retention',
      name: 'Data Retention',
      icon: Database,
      description: 'Archive critical data according to compliance requirements',
      systems: 8,
      completed: 5
    },
    {
      id: 'execution',
      name: 'Safe Decommission',
      icon: Trash2,
      description: 'Safely shut down and remove legacy systems',
      systems: 5,
      completed: 3
    },
    {
      id: 'validation',
      name: 'Validation & Cleanup',
      icon: CheckCircle,
      description: 'Verify decommission success and cleanup resources',
      systems: 3,
      completed: 2
    },
  ];

  const complianceChecklist = [
    { item: 'Data Backup Verification', status: 'completed', requirement: 'SOX' },
    { item: 'Security Clearance', status: 'completed', requirement: 'HIPAA' },
    { item: 'Regulatory Approval', status: 'in-progress', requirement: 'GDPR' },
    { item: 'Data Destruction Certificate', status: 'pending', requirement: 'PCI DSS' },
    { item: 'Audit Trail Documentation', status: 'completed', requirement: 'SOX' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">System Decommissioning</h1>
                  <p className="text-lg text-gray-600">
                    Safely retire legacy systems with automated compliance and data retention
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2">
                    <Trash2 className="h-5 w-5" />
                    <span>Schedule Decommission</span>
                  </button>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Shield className="h-5 w-5" />
                    <span>Compliance Report</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Decommission Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {decommissionMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color || 'text-gray-900'}`}>
                        {metric.value}
                      </p>
                      {metric.total && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-500 h-2 rounded-full"
                              style={{ width: `${metric.percentage}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">of {metric.total} total</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Decommission Phases */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Decommission Pipeline</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {decommissionPhases.map((phase) => {
                    const Icon = phase.icon;
                    const isSelected = selectedPhase === phase.id;
                    return (
                      <div
                        key={phase.id}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedPhase(phase.id)}
                      >
                        <div className="flex items-center space-x-3 mb-3">
                          <Icon className={`h-8 w-8 ${isSelected ? 'text-red-600' : 'text-gray-600'}`} />
                          <h4 className="font-semibold text-gray-900">{phase.name}</h4>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{phase.description}</p>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Progress</span>
                            <span className="font-medium">{phase.completed}/{phase.systems}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-500 h-2 rounded-full"
                              style={{ width: `${(phase.completed / phase.systems) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Systems Queue and Compliance */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
              {/* Decommission Queue */}
              <div className="lg:col-span-2 bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Decommission Queue</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {decommissionQueue.map((system) => (
                      <div key={system.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              system.status === 'Planning' ? 'bg-yellow-500' :
                              system.status === 'Ready' ? 'bg-green-500' :
                              system.status === 'In Progress' ? 'bg-blue-500' :
                              'bg-gray-300'
                            }`}></div>
                            <h4 className="font-medium text-gray-900">{system.system}</h4>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            system.status === 'Planning' ? 'bg-yellow-100 text-yellow-800' :
                            system.status === 'Ready' ? 'bg-green-100 text-green-800' :
                            system.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {system.status}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                          <div>
                            <span className="text-gray-600">Type:</span>
                            <span className="ml-2 font-medium">{system.type}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Dependencies:</span>
                            <span className="ml-2 font-medium">{system.dependencies}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Retention:</span>
                            <span className="ml-2 font-medium">{system.dataRetention}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Target Date:</span>
                            <span className="ml-2 font-medium">{system.decommissionDate}</span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-gray-600">Compliance:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {system.complianceReqs.map((req, index) => (
                                <span key={index} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                                  {req}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 flex justify-between items-center">
                          <span className="text-sm text-green-600 font-medium">
                            Savings: {system.estimatedSavings}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Compliance Checklist */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <Shield className="h-6 w-6 text-blue-500" />
                    <h3 className="text-lg font-semibold text-gray-900">Compliance Checklist</h3>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-3">
                    {complianceChecklist.map((item, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center mt-0.5 ${
                          item.status === 'completed' ? 'bg-green-100 text-green-600' :
                          item.status === 'in-progress' ? 'bg-blue-100 text-blue-600' :
                          'bg-gray-100 text-gray-400'
                        }`}>
                          {item.status === 'completed' ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : item.status === 'in-progress' ? (
                            <Clock className="h-3 w-3" />
                          ) : (
                            <AlertTriangle className="h-3 w-3" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{item.item}</p>
                          <p className="text-xs text-gray-600">{item.requirement}</p>
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

export default Decommission;
