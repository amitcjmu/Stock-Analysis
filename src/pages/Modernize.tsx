import React, { useState } from 'react'
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { Zap, Layers, Package, Code, Cloud } from 'lucide-react'
import { Sparkles, TrendingUp, RefreshCw } from 'lucide-react'

const Modernize = () => {
  const [selectedCategory, setSelectedCategory] = useState('containerization');
  
  const modernizationOpportunities = [
    {
      id: 'M001',
      application: 'Legacy ERP System',
      currentTech: 'Monolithic Java EE',
      recommendedApproach: 'Microservices + Containers',
      complexity: 'High',
      effort: '6 months',
      benefits: ['Scalability', 'Maintainability', 'Cost Reduction'],
      roi: '185%'
    },
    {
      id: 'M002',
      application: 'Customer Portal',
      currentTech: 'PHP Monolith',
      recommendedApproach: 'Serverless Functions',
      complexity: 'Medium',
      effort: '3 months',
      benefits: ['Auto-scaling', 'Cost Optimization', 'Performance'],
      roi: '220%'
    },
    {
      id: 'M003',
      application: 'Data Processing Pipeline',
      currentTech: 'Batch Processing',
      recommendedApproach: 'Event-driven Architecture',
      complexity: 'Medium',
      effort: '4 months',
      benefits: ['Real-time Processing', 'Reliability', 'Efficiency'],
      roi: '165%'
    },
  ];

  const modernizationMetrics = [
    { label: 'Applications Modernized', value: '12', total: '45', percentage: 27 },
    { label: 'Cost Reduction', value: '34%', color: 'text-green-600' },
    { label: 'Performance Improvement', value: '67%', color: 'text-blue-600' },
    { label: 'Technical Debt Reduction', value: '42%', color: 'text-purple-600' },
  ];

  const technicalPatterns = [
    {
      category: 'containerization',
      name: 'Containerization',
      icon: Package,
      applications: 23,
      completed: 15,
      description: 'Migrate applications to containerized environments'
    },
    {
      category: 'microservices',
      name: 'Microservices',
      icon: Layers,
      applications: 18,
      completed: 8,
      description: 'Break down monoliths into microservices'
    },
    {
      category: 'serverless',
      name: 'Serverless',
      icon: Zap,
      applications: 12,
      completed: 7,
      description: 'Convert to serverless functions'
    },
    {
      category: 'api-first',
      name: 'API-First',
      icon: Code,
      applications: 31,
      completed: 19,
      description: 'Implement API-first architecture'
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Application Modernization</h1>
                  <p className="text-lg text-gray-600">
                    Transform legacy applications with cloud-native patterns and AI recommendations
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center space-x-2">
                    <Sparkles className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <RefreshCw className="h-5 w-5" />
                    <span>Refresh Recommendations</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Modernization Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {modernizationMetrics.map((metric, index) => (
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
                              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full" 
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

            {/* Technical Patterns */}
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Modernization Patterns</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {technicalPatterns.map((pattern) => {
                    const Icon = pattern.icon;
                    const isSelected = selectedCategory === pattern.category;
                    return (
                      <div 
                        key={pattern.category}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedCategory(pattern.category)}
                      >
                        <div className="flex items-center space-x-3 mb-3">
                          <Icon className={`h-8 w-8 ${isSelected ? 'text-purple-600' : 'text-gray-600'}`} />
                          <h4 className="font-semibold text-gray-900">{pattern.name}</h4>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{pattern.description}</p>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Progress</span>
                            <span className="font-medium">{pattern.completed}/{pattern.applications}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full" 
                              style={{ width: `${(pattern.completed / pattern.applications) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Modernization Opportunities */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">AI-Recommended Modernization Opportunities</h3>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <TrendingUp className="h-4 w-4" />
                    <span>Sorted by ROI</span>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current State</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended Approach</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Complexity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Effort</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expected ROI</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key Benefits</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {modernizationOpportunities.map((opportunity) => (
                      <tr key={opportunity.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{opportunity.application}</div>
                            <div className="text-sm text-gray-500">{opportunity.id}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{opportunity.currentTech}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                            {opportunity.recommendedApproach}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            opportunity.complexity === 'High' ? 'bg-red-100 text-red-800' :
                            opportunity.complexity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {opportunity.complexity}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{opportunity.effort}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-lg font-bold text-green-600">{opportunity.roi}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1">
                            {opportunity.benefits.map((benefit, index) => (
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
          </div>
        </main>
      </div>
    </div>
  );
};

export default Modernize;
