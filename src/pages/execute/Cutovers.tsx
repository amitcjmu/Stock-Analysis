
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Calendar, Sparkles, Clock, CheckCircle, AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react';

const Cutovers = () => {
  const [activeTab, setActiveTab] = useState('scheduled');

  const cutoverEvents = [
    { 
      id: 'CO001', 
      name: 'CRM Production Cutover', 
      status: 'Scheduled', 
      type: 'Production',
      date: '2025-01-25',
      time: '02:00 AM',
      duration: '4 hours',
      applications: ['CRM Main', 'CRM Reports'],
      riskLevel: 'Medium'
    },
    { 
      id: 'CO002', 
      name: 'Web Portal Non-Prod Test', 
      status: 'Completed', 
      type: 'Non-Production',
      date: '2025-01-20',
      time: '10:00 AM',
      duration: '2 hours',
      applications: ['Web Portal'],
      riskLevel: 'Low'
    },
    { 
      id: 'CO003', 
      name: 'ERP System Production Cutover', 
      status: 'In Progress', 
      type: 'Production',
      date: '2025-01-22',
      time: '01:00 AM',
      duration: '6 hours',
      applications: ['ERP Core', 'ERP Financials', 'ERP Inventory'],
      riskLevel: 'High'
    },
    { 
      id: 'CO004', 
      name: 'File Server Migration', 
      status: 'Failed', 
      type: 'Production',
      date: '2025-01-18',
      time: '03:00 AM',
      duration: '3 hours',
      applications: ['File Server'],
      riskLevel: 'Medium'
    },
  ];

  const lessonsLearned = [
    {
      cutover: 'Web Portal Non-Prod Test (CO002)',
      issue: 'DNS propagation delay',
      resolution: 'Pre-configured DNS changes 24h in advance',
      impact: 'Reduced cutover time by 30 minutes',
      category: 'Network'
    },
    {
      cutover: 'File Server Migration (CO004)',
      issue: 'Insufficient storage allocation',
      resolution: 'Implemented automated storage monitoring',
      impact: 'Prevented future storage-related failures',
      category: 'Infrastructure'
    },
    {
      cutover: 'Previous Email Migration',
      issue: 'User authentication timeout',
      resolution: 'Extended session timeout during cutover window',
      impact: 'Improved user experience during migration',
      category: 'Security'
    }
  ];

  const cutoverMetrics = [
    { label: 'Scheduled Cutovers', value: '8', color: 'text-blue-600' },
    { label: 'Successful This Month', value: '12', color: 'text-green-600' },
    { label: 'Success Rate', value: '89%', color: 'text-green-600' },
    { label: 'Avg Downtime', value: '2.3 hours', color: 'text-orange-600' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Migration Cutovers</h1>
                  <p className="text-lg text-gray-600">
                    Manage cutover activities and track lessons learned
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Schedule</span>
                  </button>
                  <button className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center space-x-2">
                    <Calendar className="h-5 w-5" />
                    <span>Schedule Cutover</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-orange-800 text-sm">
                  <strong>AI Insight:</strong> Optimal cutover window identified: Saturday 2:00-6:00 AM based on historical traffic patterns and success rates
                </p>
              </div>
            </div>

            {/* Cutover Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {cutoverMetrics.map((metric, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                      <p className={`text-2xl font-bold ${metric.color}`}>
                        {metric.value}
                      </p>
                    </div>
                    <Calendar className={`h-8 w-8 ${metric.color}`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {[
                    { id: 'scheduled', name: 'Scheduled Cutovers', icon: Calendar },
                    { id: 'history', name: 'Cutover History', icon: Clock },
                    { id: 'lessons', name: 'Lessons Learned', icon: CheckCircle },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                          activeTab === tab.id
                            ? 'border-orange-500 text-orange-600'
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
                {activeTab === 'scheduled' && (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <Sparkles className="h-6 w-6 text-orange-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Cutover Planning Assistant</h3>
                      </div>
                      <p className="text-orange-800 mb-3">
                        AI recommends scheduling CRM Production Cutover (CO001) for Saturday 2:00 AM to minimize business impact. ERP System cutover requires additional 2-hour buffer due to complexity.
                      </p>
                      <div className="text-sm text-orange-600">
                        Risk Assessment: Medium | Recommended Window: Weekends 2:00-6:00 AM
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900">Upcoming Cutovers</h3>
                    <div className="space-y-4">
                      {cutoverEvents.filter(cutover => cutover.status === 'Scheduled' || cutover.status === 'In Progress').map((cutover) => (
                        <div key={cutover.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                cutover.status === 'In Progress' ? 'bg-orange-500 animate-pulse' :
                                cutover.status === 'Scheduled' ? 'bg-blue-500' :
                                'bg-gray-300'
                              }`}></div>
                              <h4 className="font-medium text-gray-900">{cutover.name}</h4>
                            </div>
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                cutover.status === 'In Progress' ? 'bg-orange-100 text-orange-800' :
                                cutover.status === 'Scheduled' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {cutover.status}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                cutover.type === 'Production' ? 'bg-red-100 text-red-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {cutover.type}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                cutover.riskLevel === 'High' ? 'bg-red-100 text-red-800' :
                                cutover.riskLevel === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {cutover.riskLevel} Risk
                              </span>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm mb-3">
                            <div>
                              <span className="text-gray-600">Cutover ID:</span>
                              <span className="ml-2 font-medium">{cutover.id}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Date & Time:</span>
                              <span className="ml-2 font-medium">{cutover.date} {cutover.time}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Duration:</span>
                              <span className="ml-2 font-medium">{cutover.duration}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Applications:</span>
                              <span className="ml-2 font-medium">{cutover.applications.length} apps</span>
                            </div>
                          </div>
                          <div className="bg-gray-50 rounded p-3">
                            <span className="text-sm text-gray-600">Applications: </span>
                            <span className="text-sm font-medium">{cutover.applications.join(', ')}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'history' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Cutover History</h3>
                    <div className="space-y-4">
                      {cutoverEvents.map((cutover) => (
                        <div key={cutover.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <div className={`w-3 h-3 rounded-full ${
                                cutover.status === 'Completed' ? 'bg-green-500' :
                                cutover.status === 'Failed' ? 'bg-red-500' :
                                cutover.status === 'In Progress' ? 'bg-orange-500 animate-pulse' :
                                'bg-blue-500'
                              }`}></div>
                              <h4 className="font-medium text-gray-900">{cutover.name}</h4>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              cutover.status === 'Completed' ? 'bg-green-100 text-green-800' :
                              cutover.status === 'Failed' ? 'bg-red-100 text-red-800' :
                              cutover.status === 'In Progress' ? 'bg-orange-100 text-orange-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {cutover.status}
                            </span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Date:</span>
                              <span className="ml-2 font-medium">{cutover.date}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Duration:</span>
                              <span className="ml-2 font-medium">{cutover.duration}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Type:</span>
                              <span className="ml-2 font-medium">{cutover.type}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">Risk Level:</span>
                              <span className="ml-2 font-medium">{cutover.riskLevel}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'lessons' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-900">Lessons Learned Repository</h3>
                    <div className="bg-blue-50 rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Knowledge Base Integration</h4>
                      <p className="text-blue-800 text-sm mb-3">
                        AI automatically captures and categorizes lessons learned from each cutover to improve future migration planning and execution.
                      </p>
                    </div>
                    <div className="space-y-4">
                      {lessonsLearned.map((lesson, index) => (
                        <div key={index} className="bg-white border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium text-gray-900">{lesson.cutover}</h4>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              lesson.category === 'Network' ? 'bg-blue-100 text-blue-800' :
                              lesson.category === 'Infrastructure' ? 'bg-purple-100 text-purple-800' :
                              lesson.category === 'Security' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {lesson.category}
                            </span>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <span className="text-sm font-medium text-red-600">Issue: </span>
                              <span className="text-sm text-gray-700">{lesson.issue}</span>
                            </div>
                            <div>
                              <span className="text-sm font-medium text-green-600">Resolution: </span>
                              <span className="text-sm text-gray-700">{lesson.resolution}</span>
                            </div>
                            <div>
                              <span className="text-sm font-medium text-blue-600">Impact: </span>
                              <span className="text-sm text-gray-700">{lesson.impact}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="bg-green-50 rounded-lg p-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Best Practices Identified</h4>
                      <div className="space-y-2">
                        <div className="flex items-center text-sm">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span>Pre-configure DNS changes 24 hours before cutover</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span>Implement automated storage monitoring for large data migrations</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span>Extend session timeouts during migration windows</span>
                        </div>
                        <div className="flex items-center text-sm">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span>Schedule high-risk cutovers during weekend maintenance windows</span>
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

export default Cutovers;
