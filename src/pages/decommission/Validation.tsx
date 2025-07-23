
import type React, { useState } from 'react'
import Sidebar from '../../components/Sidebar';
import type { FileText, Database, Shield, Clock } from 'lucide-react'
import { CheckCircle, AlertTriangle, X, Search, Download } from 'lucide-react'

const DecommissionValidation = () => {
  const [selectedTab, setSelectedTab] = useState('validation');
  
  const validationMetrics = [
    { label: 'Validations Complete', value: '18', total: '23', percentage: 78, color: 'text-green-600' },
    { label: 'Pending Validation', value: '5', color: 'text-orange-600' },
    { label: 'Failed Validation', value: '2', color: 'text-red-600' },
    { label: 'Cleanup Complete', value: '15', color: 'text-blue-600' },
  ];

  const validationItems = [
    {
      id: 'VAL001',
      systemName: 'Legacy CRM Database',
      type: 'Database',
      validationType: 'Data Integrity',
      status: 'Passed',
      validatedBy: 'DB Team Alpha',
      validationDate: '2025-01-15',
      issues: 0,
      details: 'All data successfully archived with integrity verification complete'
    },
    {
      id: 'VAL002',
      systemName: 'Old Email Server',
      type: 'Infrastructure',
      validationType: 'Access Removal',
      status: 'Failed',
      validatedBy: 'Security Team',
      validationDate: '2025-01-14',
      issues: 3,
      details: '3 user accounts still have residual access permissions'
    },
    {
      id: 'VAL003',
      systemName: 'Legacy Web Portal',
      type: 'Application',
      validationType: 'Service Termination',
      status: 'Passed',
      validatedBy: 'Web Team',
      validationDate: '2025-01-13',
      issues: 0,
      details: 'All services successfully terminated and monitoring removed'
    },
    {
      id: 'VAL004',
      systemName: 'Mainframe Application',
      type: 'Application',
      validationType: 'Dependency Check',
      status: 'In Progress',
      validatedBy: 'Architecture Team',
      validationDate: '2025-01-16',
      issues: 1,
      details: 'Validating that no downstream systems are affected'
    },
  ];

  const cleanupTasks = [
    {
      id: 'CLN001',
      task: 'Remove DNS Entries',
      system: 'Legacy Web Portal',
      status: 'Completed',
      assignedTo: 'Network Team',
      completedDate: '2025-01-13',
      priority: 'High'
    },
    {
      id: 'CLN002',
      task: 'Revoke SSL Certificates',
      system: 'Old Email Server',
      status: 'Pending',
      assignedTo: 'Security Team',
      completedDate: null,
      priority: 'Medium'
    },
    {
      id: 'CLN003',
      task: 'Update Network ACLs',
      system: 'Legacy CRM Database',
      status: 'Completed',
      assignedTo: 'Network Team',
      completedDate: '2025-01-15',
      priority: 'High'
    },
    {
      id: 'CLN004',
      task: 'Remove Monitoring Rules',
      system: 'Mainframe Application',
      status: 'In Progress',
      assignedTo: 'Operations Team',
      completedDate: null,
      priority: 'Low'
    },
  ];

  const validationChecklist = [
    {
      category: 'Data Validation',
      checks: [
        { item: 'Data backup verification', status: 'passed', critical: true },
        { item: 'Archive integrity check', status: 'passed', critical: true },
        { item: 'Data retention compliance', status: 'passed', critical: true },
        { item: 'Recovery test execution', status: 'warning', critical: false }
      ]
    },
    {
      category: 'Security Validation',
      checks: [
        { item: 'Access revocation verification', status: 'failed', critical: true },
        { item: 'Certificate cleanup', status: 'passed', critical: false },
        { item: 'Security group updates', status: 'passed', critical: true },
        { item: 'Audit log archival', status: 'passed', critical: false }
      ]
    },
    {
      category: 'Infrastructure Validation',
      checks: [
        { item: 'Service termination confirmation', status: 'passed', critical: true },
        { item: 'Resource deallocation', status: 'passed', critical: true },
        { item: 'Network connectivity removal', status: 'passed', critical: true },
        { item: 'DNS cleanup', status: 'passed', critical: false }
      ]
    },
    {
      category: 'Business Validation',
      checks: [
        { item: 'Stakeholder sign-off', status: 'passed', critical: true },
        { item: 'User notification completion', status: 'passed', critical: false },
        { item: 'Process documentation update', status: 'warning', critical: false },
        { item: 'Knowledge transfer completion', status: 'passed', critical: false }
      ]
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Validation & Cleanup</h1>
                  <p className="text-lg text-gray-600">
                    Verify successful decommission and complete system cleanup
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Coming Soon: CloudBridge automated validation and compliance reporting
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export Report</span>
                  </button>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5" />
                    <span>Run Validation</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Validation Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {validationMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                      {metric.total && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full" 
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

            {/* Tabs */}
            <div className="mb-8">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setSelectedTab('validation')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      selectedTab === 'validation'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Validation Results
                  </button>
                  <button
                    onClick={() => setSelectedTab('cleanup')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      selectedTab === 'cleanup'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Cleanup Tasks
                  </button>
                  <button
                    onClick={() => setSelectedTab('checklist')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      selectedTab === 'checklist'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Validation Checklist
                  </button>
                </nav>
              </div>
            </div>

            {/* Tab Content */}
            {selectedTab === 'validation' && (
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">Validation Results</h3>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <input
                        type="text"
                        placeholder="Search validations..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">System</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validation Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issues</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validated By</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {validationItems.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{item.systemName}</div>
                              <div className="text-sm text-gray-500">{item.type}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.validationType}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              item.status === 'Passed' ? 'bg-green-100 text-green-800' :
                              item.status === 'Failed' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {item.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`text-sm font-medium ${
                              item.issues === 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {item.issues}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.validatedBy}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.validationDate}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {selectedTab === 'cleanup' && (
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Cleanup Tasks</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {cleanupTasks.map((task) => (
                      <div key={task.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              task.status === 'Completed' ? 'bg-green-500' :
                              task.status === 'In Progress' ? 'bg-blue-500' :
                              'bg-gray-400'
                            }`}></div>
                            <h4 className="font-medium text-gray-900">{task.task}</h4>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              task.priority === 'High' ? 'bg-red-100 text-red-800' :
                              task.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {task.priority}
                            </span>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              task.status === 'Completed' ? 'bg-green-100 text-green-800' :
                              task.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {task.status}
                            </span>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <div>
                            <span className="text-gray-600">System:</span>
                            <span className="ml-2 font-medium">{task.system}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Assigned To:</span>
                            <span className="ml-2 font-medium">{task.assignedTo}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Completed:</span>
                            <span className="ml-2 font-medium">{task.completedDate || 'Pending'}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {selectedTab === 'checklist' && (
              <div className="space-y-6">
                {validationChecklist.map((category, index) => (
                  <div key={index} className="bg-white rounded-lg shadow-md">
                    <div className="p-6 border-b border-gray-200">
                      <h3 className="text-lg font-semibold text-gray-900">{category.category}</h3>
                    </div>
                    <div className="p-6">
                      <div className="space-y-3">
                        {category.checks.map((check, checkIndex) => (
                          <div key={checkIndex} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                check.status === 'passed' ? 'bg-green-100 text-green-600' :
                                check.status === 'warning' ? 'bg-yellow-100 text-yellow-600' :
                                'bg-red-100 text-red-600'
                              }`}>
                                {check.status === 'passed' ? (
                                  <CheckCircle className="h-4 w-4" />
                                ) : check.status === 'warning' ? (
                                  <AlertTriangle className="h-4 w-4" />
                                ) : (
                                  <X className="h-4 w-4" />
                                )}
                              </div>
                              <span className="font-medium text-gray-900">{check.item}</span>
                              {check.critical && (
                                <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                                  Critical
                                </span>
                              )}
                            </div>
                            <span className={`text-sm font-medium ${
                              check.status === 'passed' ? 'text-green-600' :
                              check.status === 'warning' ? 'text-yellow-600' :
                              'text-red-600'
                            }`}>
                              {check.status.charAt(0).toUpperCase() + check.status.slice(1)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default DecommissionValidation;
