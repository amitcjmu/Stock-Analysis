import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import { Zap, Sparkles, Code, Rocket, AlertCircle, TrendingUp } from 'lucide-react';

const Rewrite = () => {
  const [activeTab, setActiveTab] = useState('strategy');

  const rewriteProjects = [
    {
      id: 'REW001',
      application: 'Legacy CRM',
      currentTech: 'VB.NET + SQL Server',
      targetTech: 'React + Node.js + PostgreSQL',
      status: 'Planning',
      progress: 20,
      risk: 'High',
      timeline: '8 months',
      budget: '$450K',
      aiRecommendation: 'Implement in phases with parallel run strategy'
    },
    {
      id: 'REW002',
      application: 'Financial Reports',
      currentTech: 'COBOL + DB2',
      targetTech: 'Python + FastAPI + Cloud SQL',
      status: 'In Progress',
      progress: 35,
      risk: 'Medium',
      timeline: '6 months',
      budget: '$320K',
      aiRecommendation: 'Prioritize data migration and validation workflows'
    },
    {
      id: 'REW003',
      application: 'Inventory Tracker',
      currentTech: 'PHP 5.6 + MySQL',
      targetTech: 'Vue.js + Express + MongoDB',
      status: 'Testing',
      progress: 85,
      risk: 'Low',
      timeline: '4 months',
      budget: '$180K',
      aiRecommendation: 'Focus on performance optimization and user training'
    }
  ];

  const rewriteStrategies = [
    {
      name: 'Big Bang',
      description: 'Complete replacement in one deployment',
      pros: ['Faster delivery', 'Clean cut-over'],
      cons: ['High risk', 'Extended downtime'],
      riskLevel: 'High',
      suitability: 'Small applications'
    },
    {
      name: 'Phased Approach',
      description: 'Gradual module-by-module replacement',
      pros: ['Lower risk', 'Continuous feedback'],
      cons: ['Longer timeline', 'Integration complexity'],
      riskLevel: 'Medium',
      suitability: 'Large applications'
    },
    {
      name: 'Parallel Run',
      description: 'Run old and new systems simultaneously',
      pros: ['Zero downtime', 'Safe rollback'],
      cons: ['Higher cost', 'Data synchronization'],
      riskLevel: 'Low',
      suitability: 'Critical systems'
    },
    {
      name: 'Strangler Fig',
      description: 'Gradually replace functionality',
      pros: ['Minimal disruption', 'Incremental value'],
      cons: ['Complex routing', 'Extended maintenance'],
      riskLevel: 'Medium',
      suitability: 'Monolithic systems'
    }
  ];

  const getRiskColor = (risk) => {
    const colors = {
      'Low': 'bg-green-100 text-green-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'High': 'bg-red-100 text-red-800'
    };
    return colors[risk] || 'bg-gray-100 text-gray-800';
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Application Rewrite Strategy</h1>
                  <p className="text-lg text-gray-600">
                    Plan and execute complete application rewrites with AI-driven risk assessment
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Strategy</span>
                  </button>
                  <button className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center space-x-2">
                    <Rocket className="h-5 w-5" />
                    <span>Start Rewrite</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Rewrite Assistant - AI-powered technology selection and risk assessment
                </p>
              </div>
            </div>

            {/* AI Insights Panel */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Zap className="h-6 w-6 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">Rewrite AI Assistant</h3>
              </div>
              <p className="text-orange-800 mb-3">
                AI recommends phased approach for Legacy CRM rewrite. Risk analysis suggests 73% success probability with current timeline. Technology stack compatibility score: 8.5/10.
              </p>
              <div className="text-sm text-orange-600">
                Risk assessment: 1 hour ago | Technology recommendation confidence: 91%
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex">
                  {[
                    { id: 'strategy', name: 'Strategy', icon: Zap },
                    { id: 'projects', name: 'Projects', icon: Code },
                    { id: 'execution', name: 'Execution', icon: Rocket }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 px-6 py-4 font-medium text-sm border-b-2 transition-colors ${
                          activeTab === tab.id
                            ? 'border-orange-500 text-orange-600'
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
                {activeTab === 'strategy' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Rewrite Strategies</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {rewriteStrategies.map((strategy) => (
                        <div key={strategy.name} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-start mb-4">
                            <h4 className="font-semibold text-gray-900">{strategy.name}</h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskColor(strategy.riskLevel)}`}>
                              {strategy.riskLevel} Risk
                            </span>
                          </div>
                          <p className="text-gray-600 text-sm mb-4">{strategy.description}</p>
                          
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div>
                              <h5 className="font-medium text-green-700 mb-2">Pros:</h5>
                              <ul className="text-sm text-green-600 space-y-1">
                                {strategy.pros.map((pro, index) => (
                                  <li key={index}>• {pro}</li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h5 className="font-medium text-red-700 mb-2">Cons:</h5>
                              <ul className="text-sm text-red-600 space-y-1">
                                {strategy.cons.map((con, index) => (
                                  <li key={index}>• {con}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                          
                          <div className="border-t border-gray-200 pt-4">
                            <span className="text-sm text-gray-600">
                              <strong>Best for:</strong> {strategy.suitability}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'projects' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Rewrite Projects</h3>
                    <div className="space-y-6">
                      {rewriteProjects.map((project) => (
                        <div key={project.id} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h4 className="font-semibold text-gray-900 text-lg">{project.application}</h4>
                              <p className="text-sm text-gray-600">{project.id}</p>
                            </div>
                            <div className="flex space-x-3">
                              <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full">
                                {project.status}
                              </span>
                              <span className={`px-3 py-1 text-sm font-medium rounded-full ${getRiskColor(project.risk)}`}>
                                {project.risk} Risk
                              </span>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                            <div>
                              <h5 className="font-medium text-gray-900 mb-2">Technology Migration</h5>
                              <div className="space-y-2">
                                <div className="flex items-center justify-between text-sm">
                                  <span className="text-red-600">From:</span>
                                  <span className="font-medium">{project.currentTech}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                  <span className="text-green-600">To:</span>
                                  <span className="font-medium">{project.targetTech}</span>
                                </div>
                              </div>
                            </div>

                            <div>
                              <h5 className="font-medium text-gray-900 mb-2">Project Details</h5>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Timeline:</span>
                                  <span className="font-medium">{project.timeline}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Budget:</span>
                                  <span className="font-medium">{project.budget}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="mb-4">
                            <div className="flex justify-between text-sm text-gray-600 mb-1">
                              <span>Progress</span>
                              <span>{project.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-orange-600 h-2 rounded-full" 
                                style={{ width: `${project.progress}%` }}
                              ></div>
                            </div>
                          </div>

                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex items-center space-x-2 mb-2">
                              <Sparkles className="h-4 w-4 text-blue-600" />
                              <span className="text-sm font-medium text-blue-800">AI Recommendation</span>
                            </div>
                            <p className="text-blue-700 text-sm">{project.aiRecommendation}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'execution' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Execution Dashboard</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                        <h4 className="font-semibold text-orange-900 mb-3">Project Metrics</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-orange-700">On-time Delivery</span>
                            <span className="font-medium">67%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-orange-700">Budget Adherence</span>
                            <span className="font-medium">89%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-orange-700">Quality Score</span>
                            <span className="font-medium">8.2/10</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <h4 className="font-semibold text-blue-900 mb-3">Risk Management</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-blue-700">High Risk Projects</span>
                            <span className="font-medium">2</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-blue-700">Risk Mitigation</span>
                            <span className="font-medium">85%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-blue-700">Issues Resolved</span>
                            <span className="font-medium">94%</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <h4 className="font-semibold text-green-900 mb-3">Success Metrics</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-green-700">Completed Rewrites</span>
                            <span className="font-medium">8</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">Success Rate</span>
                            <span className="font-medium">91%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">ROI Achievement</span>
                            <span className="font-medium">156%</span>
                          </div>
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

export default Rewrite;
