import type React from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { Building2, BarChart3, Eye, Search, FileText, Wrench, Archive, Sparkles } from 'lucide-react';

const Index = () => {
  const phases = [
    {
      title: 'Discovery',
      description: 'Discover and inventory your applications and infrastructure',
      icon: Search,
      path: '/discovery',
      color: 'bg-green-500',
      status: 'Active'
    },
    {
      title: 'Assess',
      description: '6R treatments, migration grouping, and wave planning',
      icon: FileText,
      path: '/assess',
      color: 'bg-blue-500',
      status: 'In Progress'
    },
    {
      title: 'Plan',
      description: 'Create detailed migration plans and timelines',
      icon: Building2,
      path: '/plan',
      color: 'bg-purple-500',
      status: 'Planned'
    },
    {
      title: 'Execute',
      description: 'Execute migration tasks and monitor progress',
      icon: Wrench,
      path: '/execute',
      color: 'bg-orange-500',
      status: 'Planned'
    },
    {
      title: 'Modernize',
      description: 'Modernize applications post-migration',
      icon: Sparkles,
      path: '/modernize',
      color: 'bg-indigo-500',
      status: 'Planned'
    },
    {
      title: 'Decommission',
      description: 'Safely decommission legacy systems',
      icon: Archive,
      path: '/decommission',
      color: 'bg-red-500',
      status: 'Planned'
    },
    {
      title: 'FinOps',
      description: 'Track costs and optimize financial operations',
      icon: BarChart3,
      path: '/finops',
      color: 'bg-yellow-500',
      status: 'Planned'
    },
    {
      title: 'Observability',
      description: 'Monitor metrics and application performance',
      icon: Eye,
      path: '/observability',
      color: 'bg-emerald-500',
      status: 'Planned'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                AI Modernize Migration Platform
              </h1>
              <p className="text-xl text-gray-600">
                Manage your entire cloud migration journey from discovery to decommission with AI-powered automation
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {phases.map((phase) => {
                const Icon = phase.icon;
                return (
                  <Link
                    key={phase.title}
                    to={phase.path}
                    className="group block"
                  >
                    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 p-6 border-l-4 border-gray-200 hover:border-blue-500">
                      <div className="flex items-center justify-between mb-4">
                        <div className={`${phase.color} p-3 rounded-lg text-white`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          phase.status === 'Active' 
                            ? 'bg-green-100 text-green-800' 
                            : phase.status === 'In Progress'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-600'
                        }`}>
                          {phase.status}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                        {phase.title}
                      </h3>
                      <p className="text-gray-600 text-sm">
                        {phase.description}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>

            <div className="mt-12 bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Migration Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">247</div>
                  <div className="text-gray-600">Total Applications</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">89</div>
                  <div className="text-gray-600">Assessed</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">34</div>
                  <div className="text-gray-600">In Progress</div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
