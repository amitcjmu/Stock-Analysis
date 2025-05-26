
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Cloud, Sparkles, Play, Clock, CheckCircle, Settings, ArrowRight } from 'lucide-react';

const Replatform = () => {
  const [activeTab, setActiveTab] = useState('planning');

  const replatformProjects = [
    { 
      id: 'RP001', 
      name: 'E-commerce Platform Modernization', 
      status: 'In Progress', 
      progress: 60, 
      startDate: '2025-01-12',
      targetDate: '2025-02-15',
      platform: 'Container Platform',
      complexity: 'High'
    },
    { 
      id: 'RP002', 
      name: 'Analytics Dashboard Migration', 
      status: 'Completed', 
      progress: 100, 
      startDate: '2025-01-01',
      targetDate: '2025-01-20',
      platform: 'Serverless',
      complexity: 'Medium'
    },
    { 
      id: 'RP003', 
      name: 'Customer Portal Replatform', 
      status: 'Planning', 
      progress: 15, 
      startDate: '2025-02-05',
      targetDate: '2025-03-10',
      platform: 'PaaS',
      complexity: 'Medium'
    },
    { 
      id: 'RP004', 
      name: 'Legacy Reporting System', 
      status: 'In Progress', 
      progress: 35, 
      startDate: '2025-01-18',
      targetDate: '2025-02-28',
      platform: 'Managed Services',
      complexity: 'High'
    },
  ];

  const executionMetrics = [
    { label: 'Active Replatform Projects', value: '8', color: 'text-purple-600' },
    { label: 'Platform Migrations', value: '14', color: 'text-blue-600' },
    { label: 'Success Rate', value: '87%', color: 'text-green-600' },
    { label: 'Avg Modernization Time', value: '6.5 weeks', color: 'text-orange-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Replatform Migration Execution</h1>
                  <p className="text-lg text-gray-600">
                    Platform modernization with optimized cloud services
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Optimize</span>
                  </button>
                  <button className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2">
                    <Play className="h-5 w-5" />
                    <span>Start Migration</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-purple-800 text-sm">
                  <strong>AI Insight:</strong> Replatform migrations show 87% success rate with 6.5-week average completion. Container platforms preferred for 70% of projects.
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
                    <Cloud className={`h-8 w-8 ${metric.color}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'planning', name: 'Platform Planning', icon: Clock },
                    { id: 'execution', name: 'Active Modernizations', icon: Play },
                    { id: 'reports', name: 'Platform Reports', icon: CheckCircle },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                          activeTab === tab.id
                            ? 'border-purple-500 text-purple-600'
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
                    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <Sparkles className="h-6 w-6 text-purple-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Replatform Planning Assistant</h3>
                      </div>
                      <p className="text-purple-800 mb-3">
                        AI recommends Container Platform for E-commerce (RP001) and suggests Serverless approach for Customer Portal (RP003) to optimize costs and scalability.
                      </p>
                      <div className="text-sm text-purple-600">
                        Platform Optimization Score: 89% | Cost Savings: 32% projected
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900">Replatform Migration Pipeline</h3>
                    <div className="space-y-4">
                      {replatformProjects.map((project) => (
                        <div key={project.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                project.status === 'In Progress' ? 'bg-purple-500 animate-pulse' :
                                project.status === 'Completed' ? 'bg-green-500' :
                                project.status === 'Planning' ? 'bg-yellow-500' :
                                'bg-gray-300'
                              }`}></div>
                              <h4 className="font-medium text-gray-900">{project.name}</h4>
                            </div>
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                project.status === 'In Progress' ? 'bg-purple-100 text-purple-800' :
                                project.status === 'Completed' ? 'bg-green-100 text-green-800' :
                                project.status === 'Planning' ? 'bg-yellow-100 text-yellow-800' :
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
                              <span className="text-gray-600">Target Platform:</span>
                              <span className="ml-2 font-medium">{project.platform}</span>
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
                            <span className="text-gray-600">Modernization Progress</span>
                            <span className="font-medium">{project.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                project.status === 'Completed' ? 'bg-green-500' :
                                project.status === 'In Progress' ? 'bg-purple-500' :
                                'bg-yellow-500'
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
                    <h3 className="text-lg font-semibold text-gray-900">Active Replatform Executions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-purple-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">E-commerce Platform (RP001)</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Containerization:</span>
                            <span className="font-medium">60% Complete</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Current Phase:</span>
                            <span className="font-medium">Service Decomposition</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Target Platform:</span>
                            <span className="font-medium">Container Platform</span>
                          </div>
                        </div>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Legacy Reporting System (RP004)</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Migration:</span>
                            <span className="font-medium">35% Complete</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Current Phase:</span>
                            <span className="font-medium">Database Migration</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Target Platform:</span>
                            <span className="font-medium">Managed Services</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Platform Optimization Recommendations</h4>
                      <div className="space-y-2">
                        <div className="flex items-center text-sm">
                          <ArrowRight className="h-4 w-4 text-yellow-600 mr-2" />
                          <span>Consider auto-scaling for E-commerce platform during peak loads</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <ArrowRight className="h-4 w-4 text-yellow-600 mr-2" />
                          <span>Implement caching layer for Reporting System performance</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <ArrowRight className="h-4 w-4 text-yellow-600 mr-2" />
                          <span>Enable monitoring and alerting for all containerized services</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'reports' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Replatform Execution Reports</h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="bg-green-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-green-600 mb-2">6</div>
                        <div className="text-gray-600">Completed Platforms</div>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-purple-600 mb-2">2</div>
                        <div className="text-gray-600">In Progress</div>
                      </div>
                      <div className="bg-yellow-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-yellow-600 mb-2">32%</div>
                        <div className="text-gray-600">Cost Reduction</div>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-blue-600 mb-2">87%</div>
                        <div className="text-gray-600">Success Rate</div>
                      </div>
                    </div>
                    <div className="bg-white border rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Platform Distribution</h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">Container Platform</span>
                          <span className="text-purple-600 font-medium">40%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">Serverless</span>
                          <span className="text-blue-600 font-medium">25%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">PaaS</span>
                          <span className="text-green-600 font-medium">20%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-gray-900">Managed Services</span>
                          <span className="text-orange-600 font-medium">15%</span>
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
      <FeedbackWidget />
    </div>
  );
};

export default Replatform;
