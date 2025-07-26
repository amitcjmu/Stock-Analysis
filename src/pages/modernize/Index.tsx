
import type React from 'react';
import Sidebar from '../../components/Sidebar';
import { Code, Layers, Zap, Activity } from 'lucide-react'
import { Sparkles, TrendingUp, RefreshCw, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom';

const ModernizeIndex = (): JSX.Element => {
  const modernizationMetrics = [
    { label: 'Applications to Modernize', value: '45', color: 'text-blue-600' },
    { label: 'Refactor Projects', value: '18', color: 'text-green-600' },
    { label: 'Rearchitect Projects', value: '15', color: 'text-purple-600' },
    { label: 'Rewrite Projects', value: '12', color: 'text-orange-600' },
  ];

  const modernizationProgress = [
    { treatment: 'Refactor', total: 18, completed: 7, inProgress: 6, planned: 5, color: 'bg-green-500' },
    { treatment: 'Rearchitect', total: 15, completed: 3, inProgress: 5, planned: 7, color: 'bg-purple-500' },
    { treatment: 'Rewrite', total: 12, completed: 2, inProgress: 3, planned: 7, color: 'bg-orange-500' },
  ];

  const quickActions = [
    { name: 'Refactor Planning', path: '/modernize/refactor', icon: Code, description: 'Plan and execute code refactoring projects' },
    { name: 'Rearchitect Design', path: '/modernize/rearchitect', icon: Layers, description: 'Design new system architectures' },
    { name: 'Rewrite Strategy', path: '/modernize/rewrite', icon: Zap, description: 'Plan complete application rewrites' },
    { name: 'Progress Tracking', path: '/modernize/progress', icon: Activity, description: 'Monitor modernization progress' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Modernization Overview</h1>
                  <p className="text-lg text-gray-600">
                    AI-driven modernization planning and execution for Refactor, Rearchitect, and Rewrite treatments
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
                  <strong>Coming Soon:</strong> Enhanced by CloudBridge AI agents - Live modernization insights expected September 2025
                </p>
              </div>
            </div>

            {/* AI Assistant Panel */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Sparkles className="h-6 w-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Modernization AI Assistant</h3>
              </div>
              <p className="text-blue-800 mb-3">
                AI recommends prioritizing 8 Refactor projects with high ROI potential and suggests microservices architecture for 5 Rearchitect candidates.
              </p>
              <div className="text-sm text-blue-600">
                Last updated: Today | Confidence: 92%
              </div>
            </div>

            {/* Modernization Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {modernizationMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                    </div>
                    <TrendingUp className={`h-8 w-8 ${metric.color}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Treatment Progress */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Modernization Progress by Treatment</h3>
              </div>
              <div className="p-6">
                <div className="space-y-6">
                  {modernizationProgress.map((treatment) => (
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
                <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
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

export default ModernizeIndex;
