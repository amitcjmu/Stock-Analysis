import type React from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { BarChart3, Eye, Search } from 'lucide-react';

const Index = (): JSX.Element => {
  // Primary modules - Stock Analysis
  const primaryPhases = [
    {
      title: 'Stock Analysis',
      description: 'Search and analyze stocks with AI-powered insights',
      icon: Search,
      path: '/discovery',
      color: 'bg-green-500',
      status: 'Active'
    },
  ];

  const secondaryModules = [
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
      status: 'In Progress'
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
                Stock Analysis Platform
              </h1>
              <p className="text-xl text-gray-600">
                Search and analyze stocks with AI-powered insights and real-time market data
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {primaryPhases.map((phase) => {
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

            <div className="mt-16">
              <div className="border-t border-gray-200 pt-8 mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">Operations & Management</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {secondaryModules.map((mod) => {
                const Icon = mod.icon;
                return (
                  <Link
                    key={mod.title}
                    to={mod.path}
                    className="group block"
                  >
                    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 p-6 border-l-4 border-gray-200 hover:border-blue-500">
                      <div className="flex items-center justify-between mb-4">
                        <div className={`${mod.color} p-3 rounded-lg text-white`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          mod.status === 'Active'
                            ? 'bg-green-100 text-green-800'
                            : mod.status === 'In Progress'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-600'
                        }`}>
                          {mod.status}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                        {mod.title}
                      </h3>
                      <p className="text-gray-600 text-sm">
                        {mod.description}
                      </p>
                    </div>
                  </Link>
                );
                })}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Index;
