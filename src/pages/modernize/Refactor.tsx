
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Code, Sparkles, Play, Clock, CheckCircle, AlertTriangle, Filter } from 'lucide-react';

const Refactor = () => {
  const [activeTab, setActiveTab] = useState('planning');
  const [filterStatus, setFilterStatus] = useState('All');

  const refactorProjects = [
    {
      id: 'REF001',
      application: 'Customer Portal',
      complexity: 'Medium',
      status: 'Planning',
      progress: 15,
      effort: '3 months',
      benefits: ['Performance', 'Maintainability'],
      aiRecommendation: 'Optimize database queries and implement caching'
    },
    {
      id: 'REF002',
      application: 'Order Management',
      complexity: 'High',
      status: 'In Progress',
      progress: 45,
      effort: '4 months',
      benefits: ['Scalability', 'Code Quality'],
      aiRecommendation: 'Break monolith into microservices'
    },
    {
      id: 'REF003',
      application: 'Inventory System',
      complexity: 'Low',
      status: 'Completed',
      progress: 100,
      effort: '2 months',
      benefits: ['Performance', 'Security'],
      aiRecommendation: 'Implement automated testing'
    }
  ];

  const filteredProjects = refactorProjects.filter(project => 
    filterStatus === 'All' || project.status === filterStatus
  );

  const getStatusColor = (status) => {
    const colors = {
      'Planning': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Completed': 'bg-green-100 text-green-800',
      'On Hold': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getComplexityColor = (complexity) => {
    const colors = {
      'Low': 'bg-green-100 text-green-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'High': 'bg-red-100 text-red-800'
    };
    return colors[complexity] || 'bg-gray-100 text-gray-800';
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Refactor Planning & Execution</h1>
                  <p className="text-lg text-gray-600">
                    Plan and execute code refactoring projects with AI-driven recommendations
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Play className="h-5 w-5" />
                    <span>Start Refactor</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Refactor Assistant - Automated code analysis and optimization recommendations
                </p>
              </div>
            </div>

            {/* AI Insights Panel */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Code className="h-6 w-6 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Refactor AI Assistant</h3>
              </div>
              <p className="text-green-800 mb-3">
                AI identifies 5 critical code smell patterns across refactor candidates. Recommends prioritizing Customer Portal for immediate performance gains.
              </p>
              <div className="text-sm text-green-600">
                Analysis completed: 2 hours ago | Code quality improvement potential: 67%
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex">
                  {[
                    { id: 'planning', name: 'Planning', icon: Clock },
                    { id: 'execution', name: 'Execution', icon: Play },
                    { id: 'progress', name: 'Progress', icon: CheckCircle }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 px-6 py-4 font-medium text-sm border-b-2 transition-colors ${
                          activeTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{tab.name}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'planning' && (
                  <div>
                    <div className="flex justify-between items-center mb-6">
                      <h3 className="text-lg font-semibold text-gray-900">Refactor Planning</h3>
                      <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="border border-gray-300 rounded-md px-3 py-2"
                      >
                        <option value="All">All Status</option>
                        <option value="Planning">Planning</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                      </select>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Complexity</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Effort</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AI Recommendation</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Benefits</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredProjects.map((project) => (
                            <tr key={project.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{project.application}</div>
                                  <div className="text-sm text-gray-500">{project.id}</div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getComplexityColor(project.complexity)}`}>
                                  {project.complexity}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                                  {project.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{project.effort}</td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded">
                                  {project.aiRecommendation}
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex flex-wrap gap-1">
                                  {project.benefits.map((benefit, index) => (
                                    <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                      {benefit}
                                    </span>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {activeTab === 'execution' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Execution Dashboard</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <h4 className="font-semibold text-blue-900 mb-3">Code Quality Metrics</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-blue-700">Technical Debt Reduction</span>
                            <span className="font-medium">23%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-blue-700">Code Coverage</span>
                            <span className="font-medium">78%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-blue-700">Performance Improvement</span>
                            <span className="font-medium">34%</span>
                          </div>
                        </div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <h4 className="font-semibold text-green-900 mb-3">Execution Status</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-green-700">Active Refactors</span>
                            <span className="font-medium">3</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">Completed This Month</span>
                            <span className="font-medium">2</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">Success Rate</span>
                            <span className="font-medium">94%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'progress' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Progress Tracking</h3>
                    <div className="space-y-6">
                      {refactorProjects.map((project) => (
                        <div key={project.id} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-center mb-4">
                            <div>
                              <h4 className="font-semibold text-gray-900">{project.application}</h4>
                              <p className="text-sm text-gray-600">{project.id}</p>
                            </div>
                            <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(project.status)}`}>
                              {project.status}
                            </span>
                          </div>
                          <div className="mb-2">
                            <div className="flex justify-between text-sm text-gray-600 mb-1">
                              <span>Progress</span>
                              <span>{project.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${project.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
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

export default Refactor;
