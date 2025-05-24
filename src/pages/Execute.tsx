
import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import FeedbackWidget from '../components/FeedbackWidget';
import { Wrench, Play, CheckCircle, AlertTriangle, Clock, Monitor, Activity } from 'lucide-react';

const Execute = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  const migrationTasks = [
    { 
      id: 'T001', 
      name: 'Database Migration - CRM', 
      status: 'Running', 
      progress: 67, 
      startTime: '2025-01-15 09:00',
      estimatedCompletion: '2025-01-15 15:30',
      assignee: 'John Smith'
    },
    { 
      id: 'T002', 
      name: 'Application Deployment - Web Portal', 
      status: 'Completed', 
      progress: 100, 
      startTime: '2025-01-15 08:00',
      estimatedCompletion: '2025-01-15 12:00',
      assignee: 'Sarah Johnson'
    },
    { 
      id: 'T003', 
      name: 'Network Configuration', 
      status: 'Pending', 
      progress: 0, 
      startTime: '2025-01-15 16:00',
      estimatedCompletion: '2025-01-15 18:00',
      assignee: 'Mike Chen'
    },
    { 
      id: 'T004', 
      name: 'Security Policy Setup', 
      status: 'Failed', 
      progress: 45, 
      startTime: '2025-01-15 10:00',
      estimatedCompletion: '2025-01-15 14:00',
      assignee: 'Emily Davis'
    },
  ];

  const executionMetrics = [
    { label: 'Tasks Completed', value: '23', total: '45', percentage: 51 },
    { label: 'Success Rate', value: '89%', color: 'text-green-600' },
    { label: 'Active Migrations', value: '8', color: 'text-blue-600' },
    { label: 'Failed Tasks', value: '3', color: 'text-red-600' },
  ];

  const liveMetrics = [
    { name: 'CPU Usage', value: '67%', status: 'normal' },
    { name: 'Memory Usage', value: '45%', status: 'normal' },
    { name: 'Network I/O', value: '234 MB/s', status: 'high' },
    { name: 'Disk Usage', value: '12%', status: 'normal' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Execution</h1>
                  <p className="text-lg text-gray-600">
                    Real-time monitoring and execution of migration tasks
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Play className="h-5 w-5" />
                    <span>Start Migration</span>
                  </button>
                  <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors">
                    Emergency Stop
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
                      <p className={`text-2xl font-bold ${metric.color || 'text-gray-900'}`}>
                        {metric.value}
                      </p>
                      {metric.total && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full" 
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

            {/* Navigation Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'overview', name: 'Task Overview', icon: Wrench },
                    { id: 'monitoring', name: 'Live Monitoring', icon: Monitor },
                    { id: 'logs', name: 'Execution Logs', icon: Activity },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                          activeTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                        <span>{tab.name}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Active Migration Tasks</h3>
                    <div className="space-y-4">
                      {migrationTasks.map((task) => (
                        <div key={task.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                task.status === 'Running' ? 'bg-blue-500 animate-pulse' :
                                task.status === 'Completed' ? 'bg-green-500' :
                                task.status === 'Failed' ? 'bg-red-500' :
                                'bg-gray-300'
                              }`}></div>
                              <h4 className="font-medium text-gray-900">{task.name}</h4>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              task.status === 'Running' ? 'bg-blue-100 text-blue-800' :
                              task.status === 'Completed' ? 'bg-green-100 text-green-800' :
                              task.status === 'Failed' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {task.status}
                            </span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Task ID:</span>
                              <span className="ml-2 font-medium">{task.id}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Assignee:</span>
                              <span className="ml-2 font-medium">{task.assignee}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Started:</span>
                              <span className="ml-2 font-medium">{task.startTime}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">ETA:</span>
                              <span className="ml-2 font-medium">{task.estimatedCompletion}</span>
                            </div>
                          </div>
                          <div className="mt-3">
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Progress</span>
                              <span className="font-medium">{task.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  task.status === 'Failed' ? 'bg-red-500' :
                                  task.status === 'Completed' ? 'bg-green-500' :
                                  'bg-blue-500'
                                }`}
                                style={{ width: `${task.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'monitoring' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">System Performance Monitoring</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {liveMetrics.map((metric, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-600">{metric.name}</span>
                            <div className={`w-3 h-3 rounded-full ${
                              metric.status === 'normal' ? 'bg-green-500' :
                              metric.status === 'high' ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}></div>
                          </div>
                          <p className="text-xl font-bold text-gray-900 mt-2">{metric.value}</p>
                        </div>
                      ))}
                    </div>
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Real-time Migration Status</h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Data Transfer Rate</span>
                          <span className="font-medium">1.2 GB/min</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Concurrent Connections</span>
                          <span className="font-medium">47</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Queue Size</span>
                          <span className="font-medium">12 tasks</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'logs' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Execution Logs</h3>
                    <div className="bg-gray-900 rounded-lg p-4 text-sm font-mono">
                      <div className="text-green-400 mb-2">[2025-01-15 14:32:15] INFO: Starting database migration for CRM system</div>
                      <div className="text-blue-400 mb-2">[2025-01-15 14:32:22] DEBUG: Establishing connection to source database</div>
                      <div className="text-green-400 mb-2">[2025-01-15 14:32:28] INFO: Connection established successfully</div>
                      <div className="text-blue-400 mb-2">[2025-01-15 14:32:35] DEBUG: Beginning data transfer for table 'customers'</div>
                      <div className="text-yellow-400 mb-2">[2025-01-15 14:33:02] WARN: Large table detected, estimating 45 minutes for completion</div>
                      <div className="text-blue-400 mb-2">[2025-01-15 14:33:15] DEBUG: 10% complete - 125,000 records transferred</div>
                      <div className="text-red-400 mb-2">[2025-01-15 14:33:42] ERROR: Timeout on record 130,247, retrying...</div>
                      <div className="text-green-400">[2025-01-15 14:33:45] INFO: Retry successful, continuing transfer</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Execute;
