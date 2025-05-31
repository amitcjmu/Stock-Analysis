
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import { Activity, Sparkles, TrendingUp, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

const Progress = () => {
  const [timeframe, setTimeframe] = useState('month');

  const progressMetrics = [
    { label: 'Total Projects', value: '45', change: '+3', trend: 'up' },
    { label: 'Completed', value: '17', change: '+5', trend: 'up' },
    { label: 'In Progress', value: '14', change: '-2', trend: 'down' },
    { label: 'Success Rate', value: '94%', change: '+2%', trend: 'up' },
  ];

  const projectsByTreatment = [
    { treatment: 'Refactor', total: 18, completed: 7, inProgress: 6, delayed: 1, onTrack: 10 },
    { treatment: 'Rearchitect', total: 15, completed: 3, inProgress: 5, delayed: 2, onTrack: 10 },
    { treatment: 'Rewrite', total: 12, completed: 2, inProgress: 3, delayed: 0, onTrack: 7 },
  ];

  const recentActivities = [
    {
      id: 1,
      type: 'completion',
      project: 'Inventory System Refactor',
      time: '2 hours ago',
      status: 'success'
    },
    {
      id: 2,
      type: 'milestone',
      project: 'E-commerce Rearchitect',
      time: '4 hours ago',
      status: 'info'
    },
    {
      id: 3,
      type: 'delay',
      project: 'Legacy CRM Rewrite',
      time: '1 day ago',
      status: 'warning'
    },
    {
      id: 4,
      type: 'start',
      project: 'Analytics Engine Refactor',
      time: '2 days ago',
      status: 'info'
    },
  ];

  const upcomingMilestones = [
    {
      project: 'User Management Serverless',
      milestone: 'Production Deployment',
      date: '2025-06-01',
      daysLeft: 5
    },
    {
      project: 'Data Pipeline Rearchitect',
      milestone: 'Architecture Review',
      date: '2025-06-05',
      daysLeft: 9
    },
    {
      project: 'Financial Reports Rewrite',
      milestone: 'UAT Completion',
      date: '2025-06-10',
      daysLeft: 14
    },
  ];

  const getActivityIcon = (type) => {
    switch (type) {
      case 'completion':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'delay':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      default:
        return <Activity className="h-5 w-5 text-blue-600" />;
    }
  };

  const getActivityColor = (status) => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Modernization Progress</h1>
                  <p className="text-lg text-gray-600">
                    Track and monitor modernization project progress with AI-powered insights
                  </p>
                </div>
                <div className="flex space-x-3">
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="quarter">This Quarter</option>
                  </select>
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Insights</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Progress Analytics - Real-time project tracking and predictive insights
                </p>
              </div>
            </div>

            {/* AI Insights Panel */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Activity className="h-6 w-6 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Progress AI Assistant</h3>
              </div>
              <p className="text-green-800 mb-3">
                AI predicts 89% on-time delivery for current sprint. Recommends prioritizing 2 delayed refactor projects to maintain overall timeline. Resource allocation optimization suggests 15% efficiency gain.
              </p>
              <div className="text-sm text-green-600">
                Predictive analysis: 30 minutes ago | Forecast accuracy: 94%
              </div>
            </div>

            {/* Progress Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {progressMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                      <div className="flex items-center mt-2">
                        <TrendingUp className={`h-4 w-4 ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`} />
                        <span className={`text-sm font-medium ml-1 ${metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                          {metric.change}
                        </span>
                        <span className="text-sm text-gray-500 ml-1">vs last {timeframe}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Progress by Treatment */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Progress by Treatment</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-6">
                    {projectsByTreatment.map((treatment) => (
                      <div key={treatment.treatment}>
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-medium text-gray-900">{treatment.treatment}</h4>
                          <span className="text-sm text-gray-600">
                            {treatment.completed}/{treatment.total} completed
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                          <div className="flex h-3 rounded-full overflow-hidden">
                            <div 
                              className="bg-green-500 h-full"
                              style={{ width: `${(treatment.completed / treatment.total) * 100}%` }}
                            ></div>
                            <div 
                              className="bg-blue-500 h-full"
                              style={{ width: `${(treatment.inProgress / treatment.total) * 100}%` }}
                            ></div>
                            <div 
                              className="bg-yellow-500 h-full"
                              style={{ width: `${(treatment.delayed / treatment.total) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-xs">
                          <div className="text-center">
                            <div className="font-medium text-green-600">{treatment.completed}</div>
                            <div className="text-gray-500">Completed</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-blue-600">{treatment.inProgress}</div>
                            <div className="text-gray-500">In Progress</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-yellow-600">{treatment.delayed}</div>
                            <div className="text-gray-500">Delayed</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recent Activities */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Activities</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {recentActivities.map((activity) => (
                      <div key={activity.id} className={`border rounded-lg p-4 ${getActivityColor(activity.status)}`}>
                        <div className="flex items-center space-x-3">
                          {getActivityIcon(activity.type)}
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{activity.project}</p>
                            <p className="text-sm text-gray-600">{activity.time}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Upcoming Milestones */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Upcoming Milestones</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {upcomingMilestones.map((milestone, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <Clock className="h-5 w-5 text-blue-600" />
                        <span className="font-medium text-gray-900">{milestone.project}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{milestone.milestone}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">{milestone.date}</span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          milestone.daysLeft <= 7 ? 'bg-red-100 text-red-800' :
                          milestone.daysLeft <= 14 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {milestone.daysLeft} days
                        </span>
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

export default Progress;
