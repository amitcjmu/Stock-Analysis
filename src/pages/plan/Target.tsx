
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { Target, Cloud, Layers, Zap, Shield, Globe, Brain } from 'lucide-react';

const TargetArchitecture = () => {
  const architectureOptions = [
    {
      title: 'Cloud-Native Design',
      description: 'Microservices architecture with containerization using Kubernetes',
      icon: Cloud,
      benefits: ['Scalability', 'Resilience', 'DevOps Integration'],
      complexity: 'High',
      cost: 'Medium',
      aiRecommendation: true
    },
    {
      title: 'Hybrid Architecture',
      description: 'Combination of cloud and on-premises components',
      icon: Layers,
      benefits: ['Flexibility', 'Compliance', 'Cost Control'],
      complexity: 'Medium',
      cost: 'Low',
      aiRecommendation: false
    },
    {
      title: 'Serverless Computing',
      description: 'Event-driven architecture with serverless functions',
      icon: Zap,
      benefits: ['Auto-scaling', 'Pay-per-use', 'No Infrastructure'],
      complexity: 'Low',
      cost: 'Variable',
      aiRecommendation: false
    }
  ];

  const designPatterns = [
    { name: 'Auto-scaling', description: 'Dynamic resource allocation based on demand', icon: Target },
    { name: 'Multi-region', description: 'Global deployment for high availability', icon: Globe },
    { name: 'Security First', description: 'Zero-trust security model implementation', icon: Shield }
  ];

  const getComplexityColor = (complexity) => {
    switch (complexity) {
      case 'High': return 'bg-red-100 text-red-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Target Architecture Design</h1>
                  <p className="text-gray-600">Design optimal cloud architecture patterns</p>
                </div>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>AI Recommend</span>
                </button>
              </div>
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>AI Insight:</strong> Cloud-Native architecture recommended for cost efficiency and scalability
                </p>
              </div>
            </div>

            {/* Architecture Options */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {architectureOptions.map((option, index) => {
                const Icon = option.icon;
                return (
                  <div key={index} className={`bg-white rounded-lg shadow-md p-6 relative ${
                    option.aiRecommendation ? 'ring-2 ring-blue-500' : ''
                  }`}>
                    {option.aiRecommendation && (
                      <div className="absolute top-4 right-4">
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                          <Brain className="h-3 w-3" />
                          <span>AI Pick</span>
                        </span>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-3 mb-4">
                      <Icon className="h-8 w-8 text-blue-500" />
                      <h3 className="text-lg font-semibold text-gray-900">{option.title}</h3>
                    </div>
                    
                    <p className="text-gray-600 mb-4">{option.description}</p>
                    
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Benefits</h4>
                        <div className="flex flex-wrap gap-1">
                          {option.benefits.map((benefit, idx) => (
                            <span key={idx} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                              {benefit}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex justify-between">
                        <div>
                          <span className="text-sm text-gray-600">Complexity</span>
                          <span className={`ml-2 px-2 py-1 text-xs rounded ${getComplexityColor(option.complexity)}`}>
                            {option.complexity}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm text-gray-600">Cost: </span>
                          <span className="font-medium">{option.cost}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Design Patterns */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Core Design Patterns</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {designPatterns.map((pattern, index) => {
                  const Icon = pattern.icon;
                  return (
                    <div key={index} className="text-center p-4 border border-gray-200 rounded-lg hover:border-blue-500 transition-colors">
                      <Icon className="h-12 w-12 text-blue-500 mx-auto mb-3" />
                      <h4 className="font-semibold text-gray-900 mb-2">{pattern.name}</h4>
                      <p className="text-sm text-gray-600">{pattern.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Implementation Timeline */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Implementation Timeline</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border-l-4 border-blue-500 bg-blue-50">
                  <div>
                    <h3 className="font-medium text-gray-900">Phase 1: Foundation Setup</h3>
                    <p className="text-sm text-gray-600">Core infrastructure and security baseline</p>
                  </div>
                  <span className="text-sm font-medium text-blue-600">Weeks 1-4</span>
                </div>
                
                <div className="flex items-center justify-between p-4 border-l-4 border-green-500 bg-green-50">
                  <div>
                    <h3 className="font-medium text-gray-900">Phase 2: Service Migration</h3>
                    <p className="text-sm text-gray-600">Application containerization and deployment</p>
                  </div>
                  <span className="text-sm font-medium text-green-600">Weeks 5-12</span>
                </div>
                
                <div className="flex items-center justify-between p-4 border-l-4 border-purple-500 bg-purple-50">
                  <div>
                    <h3 className="font-medium text-gray-900">Phase 3: Optimization</h3>
                    <p className="text-sm text-gray-600">Performance tuning and monitoring setup</p>
                  </div>
                  <span className="text-sm font-medium text-purple-600">Weeks 13-16</span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TargetArchitecture;
