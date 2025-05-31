
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import { Activity, BarChart3, TrendingUp, Download, Filter, Calendar } from 'lucide-react';

const Reports = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const executionSummary = [
    { metric: 'Total Migrations', value: '47', change: '+12%', trend: 'up' },
    { metric: 'Success Rate', value: '91%', change: '+3%', trend: 'up' },
    { metric: 'Avg Migration Time', value: '4.2 days', change: '-8%', trend: 'down' },
    { metric: 'Cost Efficiency', value: '89%', change: '+5%', trend: 'up' },
  ];

  const treatmentBreakdown = [
    { treatment: 'Rehost', completed: 18, success: 17, rate: '94%', avgTime: '3.2 days' },
    { treatment: 'Replatform', completed: 14, success: 12, rate: '86%', avgTime: '6.5 weeks' },
    { treatment: 'Cutovers', completed: 15, success: 14, rate: '93%', avgTime: '2.8 hours' },
  ];

  const monthlyProgress = [
    { month: 'Sep 2024', completed: 8, planned: 10, success: 7 },
    { month: 'Oct 2024', completed: 12, planned: 15, success: 11 },
    { month: 'Nov 2024', completed: 15, planned: 18, success: 14 },
    { month: 'Dec 2024', completed: 18, planned: 20, success: 16 },
    { month: 'Jan 2025', completed: 12, planned: 16, success: 11 },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Execution Reports</h1>
                  <p className="text-lg text-gray-600">
                    Comprehensive migration execution analytics and insights
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                    <Filter className="h-5 w-5" />
                    <span>Filter</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Executive Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {executionSummary.map((item, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{item.metric}</p>
                      <p className="text-2xl font-bold text-gray-900">{item.value}</p>
                      <div className="flex items-center mt-1">
                        <TrendingUp className={`h-4 w-4 mr-1 ${
                          item.trend === 'up' ? 'text-green-500' : 'text-red-500'
                        }`} />
                        <span className={`text-sm ${
                          item.trend === 'up' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {item.change}
                        </span>
                      </div>
                    </div>
                    <Activity className="h-8 w-8 text-blue-600" />
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'overview', name: 'Execution Overview', icon: BarChart3 },
                    { id: 'treatments', name: 'By Treatment', icon: Activity },
                    { id: 'timeline', name: 'Timeline Analysis', icon: Calendar },
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
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-gray-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Migration Status Distribution</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Completed</span>
                            <div className="flex items-center">
                              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                                <div className="bg-green-500 h-2 rounded-full" style={{ width: '78%' }}></div>
                              </div>
                              <span className="text-sm font-medium">37</span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">In Progress</span>
                            <div className="flex items-center">
                              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '15%' }}></div>
                              </div>
                              <span className="text-sm font-medium">7</span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Planned</span>
                            <div className="flex items-center">
                              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '6%' }}></div>
                              </div>
                              <span className="text-sm font-medium">3</span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Failed</span>
                            <div className="flex items-center">
                              <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                                <div className="bg-red-500 h-2 rounded-full" style={{ width: '2%' }}></div>
                              </div>
                              <span className="text-sm font-medium">1</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Performance Metrics</h4>
                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Overall Success Rate</span>
                              <span className="font-medium">91%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-green-500 h-2 rounded-full" style={{ width: '91%' }}></div>
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">On-Time Delivery</span>
                              <span className="font-medium">87%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '87%' }}></div>
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-600">Budget Adherence</span>
                              <span className="font-medium">93%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-purple-500 h-2 rounded-full" style={{ width: '93%' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-blue-50 rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Key Insights</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white rounded p-4">
                          <h5 className="font-medium text-gray-900 mb-2">Top Performing Treatment</h5>
                          <p className="text-sm text-gray-600">Rehost migrations show highest success rate at 94% with fastest execution times</p>
                        </div>
                        <div className="bg-white rounded p-4">
                          <h5 className="font-medium text-gray-900 mb-2">Cost Optimization</h5>
                          <p className="text-sm text-gray-600">Replatform migrations achieving 32% cost reduction through platform optimization</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'treatments' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Treatment Analysis</h3>
                    <div className="space-y-4">
                      {treatmentBreakdown.map((treatment, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="font-medium text-gray-900">{treatment.treatment}</h4>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              treatment.rate === '94%' ? 'bg-green-100 text-green-800' :
                              treatment.rate === '93%' ? 'bg-green-100 text-green-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {treatment.rate} Success Rate
                            </span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-blue-600">{treatment.completed}</div>
                              <div className="text-sm text-gray-600">Completed</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-green-600">{treatment.success}</div>
                              <div className="text-sm text-gray-600">Successful</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-purple-600">{treatment.rate}</div>
                              <div className="text-sm text-gray-600">Success Rate</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-orange-600">{treatment.avgTime}</div>
                              <div className="text-sm text-gray-600">Avg Time</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'timeline' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Monthly Execution Timeline</h3>
                    <div className="bg-white border rounded-lg p-6">
                      <div className="space-y-4">
                        {monthlyProgress.map((month, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex justify-between items-center mb-2">
                                <span className="font-medium text-gray-900">{month.month}</span>
                                <span className="text-sm text-gray-600">
                                  {month.completed}/{month.planned} completed
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3">
                                <div 
                                  className="bg-blue-500 h-3 rounded-full"
                                  style={{ width: `${(month.completed / month.planned) * 100}%` }}
                                ></div>
                              </div>
                            </div>
                            <div className="ml-4 text-right">
                              <div className="text-sm font-medium text-green-600">
                                {month.success} successful
                              </div>
                              <div className="text-xs text-gray-500">
                                {Math.round((month.success / month.completed) * 100)}% rate
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-green-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-green-600 mb-2">65</div>
                        <div className="text-gray-600">Total Completions</div>
                        <div className="text-sm text-green-600 mt-1">+18% vs last quarter</div>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-blue-600 mb-2">79</div>
                        <div className="text-gray-600">Total Planned</div>
                        <div className="text-sm text-blue-600 mt-1">82% completion rate</div>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-6 text-center">
                        <div className="text-3xl font-bold text-purple-600 mb-2">59</div>
                        <div className="text-gray-600">Total Successful</div>
                        <div className="text-sm text-purple-600 mt-1">91% success rate</div>
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

export default Reports;
