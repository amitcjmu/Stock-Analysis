
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import { Server, Sparkles, Play, Clock, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

const Rehost = () => {
  const [activeTab, setActiveTab] = useState('planning');

  const rehostProjects = [
    { 
      id: 'RH001', 
      name: 'CRM Database Migration', 
      status: 'In Progress', 
      progress: 75, 
      startDate: '2025-01-10',
      targetDate: '2025-01-25',
      environment: 'Production',
      complexity: 'Medium'
    },
    { 
      id: 'RH002', 
      name: 'Web Portal Migration', 
      status: 'Completed', 
      progress: 100, 
      startDate: '2025-01-05',
      targetDate: '2025-01-15',
      environment: 'Production',
      complexity: 'Low'
    },
    { 
      id: 'RH003', 
      name: 'File Server Migration', 
      status: 'Planned', 
      progress: 0, 
      startDate: '2025-02-01',
      targetDate: '2025-02-10',
      environment: 'Non-Production',
      complexity: 'Low'
    },
    { 
      id: 'RH004', 
      name: 'Legacy ERP System', 
      status: 'Blocked', 
      progress: 30, 
      startDate: '2025-01-15',
      targetDate: '2025-02-05',
      environment: 'Production',
      complexity: 'High'
    },
  ];

  const executionMetrics = [
    { label: 'Active Rehost Projects', value: '12', color: 'text-blue-600' },
    { label: 'Completed This Month', value: '8', color: 'text-green-600' },
    { label: 'Success Rate', value: '94%', color: 'text-green-600' },
    { label: 'Avg Migration Time', value: '3.2 days', color: 'text-purple-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Rehost Migration Execution</h1>
                  <p className="text-lg text-gray-600">
                    Lift-and-shift migrations with minimal code changes
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Optimize</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Play className="h-5 w-5" />
                    <span>Start Migration</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> Rehost migrations show 94% success rate with average 3.2-day completion time
                </p>
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
                    </div>
                    <Server className={`h-8 w-8 ${metric.color}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'planning', name: 'Migration Planning', icon: Clock },
                    { id: 'execution', name: 'Active Executions', icon: Play },
                    { id: 'reports', name: 'Execution Reports', icon: CheckCircle },
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
                {activeTab === 'planning' && (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <Sparkles className="h-6 w-6 text-blue-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Rehost Planning Assistant</h3>
                      </div>
                      <p className="text-blue-800 mb-3">
                        AI recommends prioritizing File Server Migration (RH003) due to low complexity and minimal dependencies. Suggests resolving ERP system blockers before proceeding.
                      </p>
                      <div className="text-sm text-blue-600">
                        Optimization Score: 92% | Suggested Order: RH003 → RH001 → RH004
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900">Rehost Migration Pipeline</h3>
                    <div className="space-y-4">
                      {rehostProjects.map((project) => (
                        <div key={project.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                project.status === 'In Progress' ? 'bg-blue-500 animate-pulse' :
                                project.status === 'Completed' ? 'bg-green-500' :
                                project.status === 'Blocked' ? 'bg-red-500' :
                                'bg-gray-300'
                              }`}></div>
                              <h4 className="font-medium text-gray-900">{project.name}</h4>
                            </div>
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                project.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                                project.status === 'Completed' ? 'bg-green-100 text-green-800' :
                                project.status === 'Blocked' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {project.status}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                project.complexity === 'High' ? 'bg-red-100 text-red-800' :
                                project.complexity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {project.complexity}
                              </span>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm mb-3">
                            <div>
                              <span className="text-gray-600">Project ID:</span>
                              <span className="ml-2 font-medium">{project.id}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Environment:</span>
                              <span className="ml-2 font-medium">{project.environment}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Start Date:</span>
                              <span className="ml-2 font-medium">{project.startDate}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Target Date:</span>
                              <span className="ml-2 font-medium">{project.targetDate}</span>
                            </div>
                          </div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Migration Progress</span>
                            <span className="font-medium">{project.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                project.status === 'Blocked' ? 'bg-red-500' :
                                project.status === 'Completed' ? 'bg-green-500' :
                                'bg-blue-500'
                              }`}
                              style={{ width: `${project.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'execution' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Active Rehost Executions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-blue-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">CRM Database Migration (RH001)</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Data Transfer:</span>
                            <span className="font-medium">75% Complete</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Estimated Completion:</span>
                            <span className="font-medium">2 hours</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Current Phase:</span>
                            <span className="font-medium">Database Sync</span>
                          </div>
                        </div>
                      </div>
                      <div className="bg-yellow-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Legacy ERP System (RH004)</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Status:</span>
                            <span className="font-medium text-red-600">Blocked</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Issue:</span>
                            <span className="font-medium">Dependency Resolution</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Action Required:</span>
                            <span className="font-medium">Network Config</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'reports' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Rehost Execution Reports</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-green-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-green-600 mb-2">8</div>
                        <div className="text-gray-600">Completed This Month</div>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-blue-600 mb-2">4</div>
                        <div className="text-gray-600">In Progress</div>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-gray-600 mb-2">2</div>
                        <div className="text-gray-600">Planned</div>
                      </div>
                    </div>
                    <div className="bg-white border rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Recent Completions</h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">Web Portal Migration (RH002)</span>
                          <span className="text-green-600 flex items-center">
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Completed
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">Email Server Migration</span>
                          <span className="text-green-600 flex items-center">
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Completed
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">File Share Migration</span>
                          <span className="text-green-600 flex items-center">
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Completed
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Rehost;
