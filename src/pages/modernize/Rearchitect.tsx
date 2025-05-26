
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Layers, Sparkles, Settings, Target, CheckCircle, ArrowRight } from 'lucide-react';

const Rearchitect = () => {
  const [activeTab, setActiveTab] = useState('design');

  const rearchitectProjects = [
    {
      id: 'ARCH001',
      application: 'E-commerce Platform',
      currentArch: 'Monolithic',
      targetArch: 'Microservices',
      status: 'Design Phase',
      progress: 25,
      complexity: 'High',
      aiRecommendation: 'Implement API Gateway pattern with service mesh'
    },
    {
      id: 'ARCH002',
      application: 'Data Analytics',
      currentArch: 'Traditional ETL',
      targetArch: 'Event-driven',
      status: 'Planning',
      progress: 10,
      complexity: 'Medium',
      aiRecommendation: 'Use event sourcing with CQRS pattern'
    },
    {
      id: 'ARCH003',
      application: 'User Management',
      currentArch: 'Coupled Services',
      targetArch: 'Serverless',
      status: 'In Progress',
      progress: 60,
      complexity: 'Medium',
      aiRecommendation: 'Implement OAuth 2.0 with JWT tokens'
    }
  ];

  const architecturalPatterns = [
    {
      name: 'Microservices',
      description: 'Break monolith into independent services',
      benefits: ['Scalability', 'Independent deployment', 'Technology diversity'],
      complexity: 'High',
      projects: 8
    },
    {
      name: 'Event-driven',
      description: 'Asynchronous communication via events',
      benefits: ['Loose coupling', 'Real-time processing', 'Resilience'],
      complexity: 'Medium',
      projects: 5
    },
    {
      name: 'Serverless',
      description: 'Function-as-a-Service architecture',
      benefits: ['Cost efficiency', 'Auto-scaling', 'Reduced ops'],
      complexity: 'Low',
      projects: 7
    },
    {
      name: 'CQRS',
      description: 'Command Query Responsibility Segregation',
      benefits: ['Performance', 'Scalability', 'Flexibility'],
      complexity: 'High',
      projects: 3
    }
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Architecture Design & Planning</h1>
                  <p className="text-lg text-gray-600">
                    Design and implement new system architectures with AI-guided patterns
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Architecture</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Settings className="h-5 w-5" />
                    <span>Design Tool</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Architecture Assistant - AI-powered architecture design and pattern recommendations
                </p>
              </div>
            </div>

            {/* AI Insights Panel */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6 mb-8">
              <div className="flex items-center space-x-3 mb-4">
                <Layers className="h-6 w-6 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">Architecture AI Assistant</h3>
              </div>
              <p className="text-purple-800 mb-3">
                AI recommends microservices pattern for 3 applications and suggests event-driven architecture for improved scalability. Domain decomposition analysis shows 85% compatibility.
              </p>
              <div className="text-sm text-purple-600">
                Architecture analysis: 4 hours ago | Pattern match confidence: 89%
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex">
                  {[
                    { id: 'design', name: 'Design', icon: Target },
                    { id: 'patterns', name: 'Patterns', icon: Layers },
                    { id: 'execution', name: 'Execution', icon: Settings }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 px-6 py-4 font-medium text-sm border-b-2 transition-colors ${
                          activeTab === tab.id
                            ? 'border-purple-500 text-purple-600'
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
                {activeTab === 'design' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Architecture Design Projects</h3>
                    <div className="space-y-6">
                      {rearchitectProjects.map((project) => (
                        <div key={project.id} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h4 className="font-semibold text-gray-900 text-lg">{project.application}</h4>
                              <p className="text-sm text-gray-600">{project.id}</p>
                            </div>
                            <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full">
                              {project.status}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                            <div className="flex items-center space-x-4">
                              <div className="bg-red-100 text-red-800 px-3 py-2 rounded-lg flex-1 text-center">
                                <div className="text-xs font-medium">Current</div>
                                <div className="font-semibold">{project.currentArch}</div>
                              </div>
                              <ArrowRight className="h-5 w-5 text-gray-400" />
                              <div className="bg-green-100 text-green-800 px-3 py-2 rounded-lg flex-1 text-center">
                                <div className="text-xs font-medium">Target</div>
                                <div className="font-semibold">{project.targetArch}</div>
                              </div>
                            </div>
                            
                            <div>
                              <div className="flex justify-between text-sm text-gray-600 mb-1">
                                <span>Progress</span>
                                <span>{project.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-purple-600 h-2 rounded-full" 
                                  style={{ width: `${project.progress}%` }}
                                ></div>
                              </div>
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

                {activeTab === 'patterns' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Architectural Patterns</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {architecturalPatterns.map((pattern) => (
                        <div key={pattern.name} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex justify-between items-start mb-4">
                            <h4 className="font-semibold text-gray-900">{pattern.name}</h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              pattern.complexity === 'High' ? 'bg-red-100 text-red-800' :
                              pattern.complexity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {pattern.complexity}
                            </span>
                          </div>
                          <p className="text-gray-600 text-sm mb-4">{pattern.description}</p>
                          <div className="mb-4">
                            <h5 className="font-medium text-gray-900 mb-2">Benefits:</h5>
                            <div className="flex flex-wrap gap-1">
                              {pattern.benefits.map((benefit, index) => (
                                <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                                  {benefit}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">{pattern.projects} projects</span>
                            <button className="text-purple-600 hover:text-purple-800 text-sm font-medium">
                              View Details →
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'execution' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Implementation Execution</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                        <h4 className="font-semibold text-purple-900 mb-3">Architecture Metrics</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-purple-700">Design Completeness</span>
                            <span className="font-medium">78%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-purple-700">Pattern Compliance</span>
                            <span className="font-medium">92%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-purple-700">Scalability Score</span>
                            <span className="font-medium">8.5/10</span>
                          </div>
                        </div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <h4 className="font-semibold text-green-900 mb-3">Implementation Status</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-green-700">Active Projects</span>
                            <span className="font-medium">5</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">Completed Designs</span>
                            <span className="font-medium">12</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-green-700">Success Rate</span>
                            <span className="font-medium">87%</span>
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
      <FeedbackWidget />
    </div>
  );
};

export default Rearchitect;
