
import type React from 'react';
import Sidebar from '../../components/Sidebar';
import { Shield, Database, Clock, AlertTriangle, CheckCircle, FileText } from 'lucide-react'
import { Archive, Trash2 } from 'lucide-react'

const DecommissionIndex = () => {
  const decommissionMetrics = [
    { label: 'Systems Queued', value: '45', total: '120', percentage: 38, color: 'text-red-600' },
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
      progress: 67,
      systems: 12,
      status: 'active'
    },
    {
      id: 'data-retention',
      name: 'Data Retention',
      icon: Database,
      description: 'Archive critical data according to compliance requirements',
      progress: 45,
      systems: 8,
      status: 'active'
    },
    {
      id: 'execution',
      name: 'Safe Decommission',
      icon: Trash2,
      description: 'Safely shut down and remove legacy systems',
      progress: 30,
      systems: 5,
      status: 'pending'
    },
    {
      id: 'validation',
      name: 'Validation & Cleanup',
      icon: CheckCircle,
      description: 'Verify decommission success and cleanup resources',
      progress: 15,
      systems: 3,
      status: 'pending'
    },
  ];

  const upcomingDecommissions = [
    {
      id: 'D001',
      system: 'Legacy Mainframe System',
      type: 'Application',
      scheduledDate: '2025-03-15',
      priority: 'High',
      estimatedSavings: '$120,000/year'
    },
    {
      id: 'D002',
      system: 'Old CRM Database',
      type: 'Database',
      scheduledDate: '2025-02-28',
      priority: 'Medium',
      estimatedSavings: '$45,000/year'
    },
    {
      id: 'D003',
      system: 'Legacy Web Server',
      type: 'Infrastructure',
      scheduledDate: '2025-04-10',
      priority: 'Low',
      estimatedSavings: '$30,000/year'
    },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Decommission Overview</h1>
                  <p className="text-lg text-gray-600">
                    Safely retire legacy systems with automated compliance and data retention
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Coming Soon: Enhanced by CloudBridge automation
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Archive className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </button>
                  <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2">
                    <Trash2 className="h-5 w-5" />
                    <span>Schedule Decommission</span>
                  </button>
                </div>
              </div>
            </div>

            {/* AI Assistant Panel */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Archive className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-blue-900">Decommission Assistant</h3>
              </div>
              <p className="text-blue-800 mb-3">
                AI recommends prioritizing 3 legacy systems for immediate decommission to achieve $300K annual savings
              </p>
              <div className="text-sm text-blue-600">
                // TODO: Enhance with CloudBridge AI insights
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
                    return (
                      <div 
                        key={phase.id}
                        className="p-4 rounded-lg border-2 border-gray-200 hover:border-red-300 transition-all cursor-pointer"
                      >
                        <div className="flex items-center space-x-3 mb-3">
                          <Icon className={`h-8 w-8 ${phase.status === 'active' ? 'text-red-600' : 'text-gray-400'}`} />
                          <h4 className="font-semibold text-gray-900">{phase.name}</h4>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{phase.description}</p>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Progress</span>
                            <span className="font-medium">{phase.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-red-500 h-2 rounded-full" 
                              style={{ width: `${phase.progress}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500">{phase.systems} systems</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Upcoming Decommissions */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Upcoming Decommissions</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {upcomingDecommissions.map((system) => (
                    <div key={system.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            system.priority === 'High' ? 'bg-red-500' :
                            system.priority === 'Medium' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}></div>
                          <h4 className="font-medium text-gray-900">{system.system}</h4>
                        </div>
                        <span className="text-sm text-green-600 font-medium">
                          {system.estimatedSavings}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Type:</span>
                          <span className="ml-2 font-medium">{system.type}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Scheduled:</span>
                          <span className="ml-2 font-medium">{system.scheduledDate}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Priority:</span>
                          <span className={`ml-2 font-medium ${
                            system.priority === 'High' ? 'text-red-600' :
                            system.priority === 'Medium' ? 'text-yellow-600' :
                            'text-green-600'
                          }`}>{system.priority}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DecommissionIndex;
