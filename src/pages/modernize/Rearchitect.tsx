import React, { useState } from 'react'
import { Target } from 'lucide-react'
import { Layers, Sparkles, Settings, CheckCircle, ArrowRight, Loader2, AlertTriangle } from 'lucide-react'
import { useRearchitect } from '@/hooks/useRearchitect';
import { Sidebar } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

const Rearchitect = () => {
  const [activeTab, setActiveTab] = useState('design');
  const { data, isLoading, isError, error } = useRearchitect();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading architecture data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 p-8">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <p>Error loading architecture data: {error?.message}</p>
          </Alert>
        </div>
      </div>
    );
  }

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
                  <Button
                    variant="gradient"
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Architecture
                  </Button>
                  <Button variant="success">
                    <Settings className="h-5 w-5 mr-2" />
                    Design Tool
                  </Button>
                </div>
              </div>
              <Alert className="mt-4" variant="info">
                <p className="text-blue-800 text-sm">
                  <strong>Coming Soon:</strong> CloudBridge Architecture Assistant - AI-powered architecture design and pattern recommendations
                </p>
              </Alert>
            </div>

            {/* AI Insights Panel */}
            <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200 mb-8">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Layers className="h-6 w-6 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Architecture AI Assistant</h3>
                </div>
                <p className="text-purple-800 mb-3">{data?.aiInsights.analysis}</p>
                <div className="text-sm text-purple-600">
                  Architecture analysis: {data?.aiInsights.lastUpdated} | Pattern match confidence: {data?.aiInsights.confidence}%
                </div>
              </div>
            </Card>

            {/* Tab Navigation */}
            <Card>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="border-b border-gray-200">
                  {[
                    { id: 'design', name: 'Design', icon: Target },
                    { id: 'patterns', name: 'Patterns', icon: Layers },
                    { id: 'execution', name: 'Execution', icon: Settings }
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <TabsTrigger
                        key={tab.id}
                        value={tab.id}
                        className="flex items-center space-x-2 px-6 py-4"
                      >
                        <Icon className="h-4 w-4" />
                        <span>{tab.name}</span>
                      </TabsTrigger>
                    );
                  })}
                </TabsList>

                <div className="p-6">
                  {activeTab === 'design' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-6">Architecture Design Projects</h3>
                      <div className="space-y-6">
                        {data?.projects.map((project) => (
                          <Card key={project.id} className="p-6">
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
                                <Progress value={project.progress} />
                              </div>
                            </div>

                            <Alert variant="info" className="mt-4">
                              <div className="flex items-center space-x-2 mb-2">
                                <Sparkles className="h-4 w-4 text-blue-600" />
                                <span className="text-sm font-medium text-blue-800">AI Recommendation</span>
                              </div>
                              <p className="text-blue-700 text-sm">{project.aiRecommendation}</p>
                            </Alert>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab === 'patterns' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-6">Architectural Patterns</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {data?.patterns.map((pattern) => (
                          <Card key={pattern.name} className="p-6">
                            <h4 className="font-semibold text-gray-900 mb-2">{pattern.name}</h4>
                            <p className="text-sm text-gray-600 mb-4">{pattern.description}</p>
                            <div className="space-y-3">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">Complexity</span>
                                <span className={`font-medium ${
                                  pattern.complexity === 'High' ? 'text-red-600' :
                                  pattern.complexity === 'Medium' ? 'text-yellow-600' :
                                  'text-green-600'
                                }`}>{pattern.complexity}</span>
                              </div>
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">Active Projects</span>
                                <span className="font-medium text-blue-600">{pattern.projects}</span>
                              </div>
                            </div>
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <h5 className="text-sm font-medium text-gray-900 mb-2">Benefits</h5>
                              <ul className="space-y-1">
                                {pattern.benefits.map((benefit, index) => (
                                  <li key={index} className="text-sm text-gray-600 flex items-center">
                                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                                    {benefit}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab === 'execution' && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-6">Execution Plan</h3>
                      <Alert variant="warning">
                        <p>Execution planning features coming soon...</p>
                      </Alert>
                    </div>
                  )}
                </div>
              </Tabs>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Rearchitect;
