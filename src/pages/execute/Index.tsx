
import type React from 'react';
import Sidebar from '../../components/Sidebar';
import type { Server, Cloud, Activity, Calendar } from 'lucide-react'
import { Wrench, Sparkles, RefreshCw, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom';

const ExecuteIndex = () => {
  const executionMetrics = [
    { label: 'Total Executions', value: '32', color: 'text-blue-600' },
    { label: 'Rehost Projects', value: '18', color: 'text-green-600' },
    { label: 'Replatform Projects', value: '14', color: 'text-purple-600' },
    { label: 'Active Cutovers', value: '5', color: 'text-orange-600' },
  ];

  const executionProgress = [
    { treatment: 'Rehost', total: 18, completed: 12, inProgress: 4, planned: 2, color: 'bg-green-500' },
    { treatment: 'Replatform', total: 14, completed: 8, inProgress: 3, planned: 3, color: 'bg-purple-500' },
    { treatment: 'Cutovers', total: 25, completed: 18, inProgress: 5, planned: 2, color: 'bg-orange-500' },
  ];

  const quickActions = [
    { name: 'Rehost Execution', path: '/execute/rehost', icon: Server, description: 'Plan and execute lift-and-shift migrations' },
    { name: 'Replatform Execution', path: '/execute/replatform', icon: Cloud, description: 'Execute platform modernization projects' },
    { name: 'Migration Cutovers', path: '/execute/cutovers', icon: Calendar, description: 'Manage migration cutover activities' },
    { name: 'Execution Reports', path: '/execute/reports', icon: Activity, description: 'Track execution progress and metrics' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Execution Overview</h1>
                  <p className="text-lg text-gray-600">
                    Execute Rehost and Replatform treatments with AI-driven migration management
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <RefreshCw className="h-5 w-5" />
                    <span>Refresh Data</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> Enhanced by CloudBridge AI agents - Live execution insights expected September 2025
                </p>
              </div>
            </div>

            {/* AI Assistant Panel */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Execution AI Assistant</h3>
              </div>
              <p className="text-blue-800 mb-3">
                AI recommends prioritizing 6 Rehost migrations with minimal dependencies and suggests automated cutover scheduling for 3 upcoming Replatform projects.
              </p>
              <div className="text-sm text-blue-600">
                Last updated: Today | Confidence: 94%
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
                    <Wrench className={`h-8 w-8 ${metric.color}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Treatment Progress */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Execution Progress by Treatment</h3>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {executionProgress.map((treatment) => (
                    <div key={treatment.treatment}>
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-gray-900">{treatment.treatment}</h4>
                        <span className="text-sm text-gray-600">
                          {treatment.completed + treatment.inProgress}/{treatment.total} projects
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div className="flex h-3 rounded-full overflow-hidden">
                          <div 
                            className={`${treatment.color} h-full`}
                            style={{ width: `${(treatment.completed / treatment.total) * 100}%` }}
                          ></div>
                          <div 
                            className={`${treatment.color} opacity-60 h-full`}
                            style={{ width: `${(treatment.inProgress / treatment.total) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>{treatment.completed} Completed</span>
                        <span>{treatment.inProgress} In Progress</span>
                        <span>{treatment.planned} Planned</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Execution Areas</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {quickActions.map((action) => {
                    const Icon = action.icon;
                    return (
                      <Link
                        key={action.name}
                        to={action.path}
                        className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
                      >
                        <Icon className="h-8 w-8 text-blue-600 mr-4" />
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 group-hover:text-blue-900">{action.name}</h4>
                          <p className="text-sm text-gray-600">{action.description}</p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-600" />
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ExecuteIndex;
