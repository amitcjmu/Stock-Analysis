
import React from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Database, Server, HardDrive, Activity, ArrowRight } from 'lucide-react';

const DiscoveryIndex = () => {
  const summaryCards = [
    { title: 'Total Apps Discovered', value: '250', subtitle: 'Applications', icon: Database, color: 'bg-blue-500' },
    { title: 'Total Servers Discovered', value: '500', subtitle: 'Servers', icon: Server, color: 'bg-green-500' },
    { title: 'Databases Discovered', value: '50', subtitle: 'Databases', icon: HardDrive, color: 'bg-purple-500' },
    { title: 'Scanning Progress', value: '75%', subtitle: 'Complete', icon: Activity, color: 'bg-orange-500' }
  ];

  const quickActions = [
    { title: 'View Inventory', description: 'Browse discovered assets and their details', path: '/discovery/inventory' },
    { title: 'Dependency Map', description: 'Explore relationships between assets', path: '/discovery/dependencies' },
    { title: 'Scanning Status', description: 'Monitor ongoing discovery scans', path: '/discovery/scan' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Discovery Overview</h1>
              <p className="text-lg text-gray-600">
                AI-powered discovery and inventory of your IT landscape
              </p>
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Coming Soon:</strong> Enhanced discovery powered by CloudBridge agents (September 2025)
                </p>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {summaryCards.map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.title} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`${card.color} p-3 rounded-lg text-white`}>
                        <Icon className="h-6 w-6" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{card.value}</h3>
                    <p className="text-sm text-gray-600">{card.title}</p>
                    <p className="text-xs text-gray-500">{card.subtitle}</p>
                  </div>
                );
              })}
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {quickActions.map((action) => (
                  <Link
                    key={action.title}
                    to={action.path}
                    className="group block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
                          {action.title}
                        </h3>
                        <p className="text-sm text-gray-600">{action.description}</p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Discovery Activity</h2>
              <div className="space-y-3">
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">App discovery completed for Finance department</span>
                  <span className="text-xs text-gray-500">2 hours ago</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Server scan initiated for datacenter DC-01</span>
                  <span className="text-xs text-gray-500">4 hours ago</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">Database inventory updated for HR systems</span>
                  <span className="text-xs text-gray-500">6 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default DiscoveryIndex;
