
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import { Trash2, AlertTriangle, CheckCircle, Clock, Pause, Play, Settings, Shield, Database, Server } from 'lucide-react';

const DecommissionExecution = () => {
  const [selectedExecution, setSelectedExecution] = useState('all');
  
  const executionMetrics = [
    { label: 'Systems Decommissioned', value: '23', total: '45', percentage: 51, color: 'text-red-600' },
    { label: 'In Progress', value: '8', color: 'text-blue-600' },
    { label: 'Failed/Rollback', value: '2', color: 'text-orange-600' },
    { label: 'Annual Savings', value: '$1.2M', color: 'text-green-600' },
  ];

  const executionQueue = [
    {
      id: 'EXE001',
      systemName: 'Legacy CRM Database',
      type: 'Database',
      status: 'In Progress',
      progress: 75,
      phase: 'Data Migration',
      startTime: '2025-01-15 09:00',
      estimatedCompletion: '2025-01-15 14:30',
      assignedTo: 'DB Team Alpha',
      dependencies: 0,
      riskLevel: 'Medium',
      rollbackReady: true
    },
    {
      id: 'EXE002',
      systemName: 'Old Email Server',
      type: 'Infrastructure',
      status: 'Scheduled',
      progress: 0,
      phase: 'Pre-execution Checks',
      startTime: '2025-01-16 08:00',
      estimatedCompletion: '2025-01-16 12:00',
      assignedTo: 'Infrastructure Team',
      dependencies: 1,
      riskLevel: 'Low',
      rollbackReady: true
    },
    {
      id: 'EXE003',
      systemName: 'Mainframe Application',
      type: 'Application',
      status: 'Failed',
      progress: 35,
      phase: 'Service Shutdown',
      startTime: '2025-01-14 10:00',
      estimatedCompletion: '2025-01-14 16:00',
      assignedTo: 'Mainframe Team',
      dependencies: 3,
      riskLevel: 'High',
      rollbackReady: false
    },
    {
      id: 'EXE004',
      systemName: 'Legacy Web Portal',
      type: 'Application',
      status: 'Completed',
      progress: 100,
      phase: 'Verification Complete',
      startTime: '2025-01-13 09:00',
      estimatedCompletion: '2025-01-13 15:00',
      assignedTo: 'Web Team',
      dependencies: 0,
      riskLevel: 'Low',
      rollbackReady: false
    },
  ];

  const executionPhases = [
    {
      id: 1,
      name: 'Pre-execution Validation',
      description: 'Final validation and dependency checks',
      status: 'completed',
      tasks: ['Dependency verification', 'Backup confirmation', 'Stakeholder approval']
    },
    {
      id: 2,
      name: 'Service Shutdown',
      description: 'Graceful shutdown of system services',
      status: 'in-progress',
      tasks: ['User notification', 'Service termination', 'Connection closure']
    },
    {
      id: 3,
      name: 'Data Migration/Archive',
      description: 'Migrate or archive critical data',
      status: 'in-progress',
      tasks: ['Data extraction', 'Archive storage', 'Integrity verification']
    },
    {
      id: 4,
      name: 'Infrastructure Removal',
      description: 'Remove hardware and infrastructure',
      status: 'pending',
      tasks: ['Hardware decommission', 'Network cleanup', 'Resource deallocation']
    },
    {
      id: 5,
      name: 'Verification & Cleanup',
      description: 'Final verification and cleanup',
      status: 'pending',
      tasks: ['Access verification', 'Documentation update', 'Monitoring removal']
    }
  ];

  const safetyChecks = [
    { check: 'Data Backup Verified', status: 'passed', critical: true },
    { check: 'Dependencies Resolved', status: 'passed', critical: true },
    { check: 'Rollback Plan Ready', status: 'passed', critical: true },
    { check: 'Business Approval', status: 'passed', critical: true },
    { check: 'Monitoring Disabled', status: 'warning', critical: false },
    { check: 'Access Logs Archived', status: 'passed', critical: false },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Decommission Execution</h1>
                  <p className="text-lg text-gray-600">
                    Execute safe system decommissioning with automated rollback capabilities
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Coming Soon: CloudBridge automated execution orchestration
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center space-x-2">
                    <Pause className="h-5 w-5" />
                    <span>Emergency Stop</span>
                  </button>
                  <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2">
                    <Trash2 className="h-5 w-5" />
                    <span>Execute Decommission</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Execution Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {executionMetrics.map((metric, index) => (
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

            {/* Safety Checks */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                  <Shield className="h-6 w-6 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Pre-Execution Safety Checks</h3>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {safetyChecks.map((check, index) => (
                    <div key={index} className={`p-4 rounded-lg border-2 ${
                      check.status === 'passed' ? 'border-green-200 bg-green-50' :
                      check.status === 'warning' ? 'border-yellow-200 bg-yellow-50' :
                      'border-red-200 bg-red-50'
                    }`}>
                      <div className="flex items-center space-x-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                          check.status === 'passed' ? 'bg-green-500 text-white' :
                          check.status === 'warning' ? 'bg-yellow-500 text-white' :
                          'bg-red-500 text-white'
                        }`}>
                          {check.status === 'passed' ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <AlertTriangle className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{check.check}</p>
                          {check.critical && (
                            <p className="text-xs text-red-600">Critical Check</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Execution Process */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Execution Process</h3>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {executionPhases.map((phase, index) => (
                    <div key={phase.id} className="flex space-x-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          phase.status === 'completed' ? 'bg-green-500 text-white' :
                          phase.status === 'in-progress' ? 'bg-blue-500 text-white' :
                          'bg-gray-300 text-gray-600'
                        }`}>
                          {phase.status === 'completed' ? (
                            <CheckCircle className="h-5 w-5" />
                          ) : phase.status === 'in-progress' ? (
                            <Clock className="h-5 w-5" />
                          ) : (
                            <span className="text-sm font-bold">{phase.id}</span>
                          )}
                        </div>
                        {index < executionPhases.length - 1 && (
                          <div className="w-px h-16 bg-gray-300 mt-2"></div>
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 mb-2">{phase.name}</h4>
                        <p className="text-gray-600 mb-3">{phase.description}</p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                          {phase.tasks.map((task, taskIndex) => (
                            <div key={taskIndex} className="text-sm text-gray-500 flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${
                                phase.status === 'completed' ? 'bg-green-400' :
                                phase.status === 'in-progress' ? 'bg-blue-400' :
                                'bg-gray-300'
                              }`}></div>
                              <span>{task}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Execution Queue */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Execution Queue</h3>
                  <select
                    value={selectedExecution}
                    onChange={(e) => setSelectedExecution(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Executions</option>
                    <option value="progress">In Progress</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">System</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phase</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned To</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {executionQueue
                      .filter(item => selectedExecution === 'all' || item.status.toLowerCase().includes(selectedExecution))
                      .map((execution) => (
                      <tr key={execution.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              execution.type === 'Database' ? 'bg-blue-500' :
                              execution.type === 'Application' ? 'bg-green-500' :
                              'bg-purple-500'
                            }`}></div>
                            <div>
                              <div className="text-sm font-medium text-gray-900">{execution.systemName}</div>
                              <div className="text-sm text-gray-500">{execution.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{execution.type}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            execution.status === 'Completed' ? 'bg-green-100 text-green-800' :
                            execution.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                            execution.status === 'Failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {execution.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  execution.status === 'Completed' ? 'bg-green-500' :
                                  execution.status === 'Failed' ? 'bg-red-500' :
                                  'bg-blue-500'
                                }`}
                                style={{ width: `${execution.progress}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-600">{execution.progress}%</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{execution.phase}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{execution.assignedTo}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex space-x-2">
                            {execution.status === 'In Progress' && (
                              <button className="text-orange-600 hover:text-orange-800">
                                <Pause className="h-4 w-4" />
                              </button>
                            )}
                            {execution.status === 'Scheduled' && (
                              <button className="text-green-600 hover:text-green-800">
                                <Play className="h-4 w-4" />
                              </button>
                            )}
                            <button className="text-gray-600 hover:text-gray-800">
                              <Settings className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DecommissionExecution;
