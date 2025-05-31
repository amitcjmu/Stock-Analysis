
import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { Search, Database, Network, Server, Activity, Download, Filter } from 'lucide-react';

const Discovery = () => {
  const [selectedFilter, setSelectedFilter] = useState('all');
  
  const discoveredAssets = [
    { id: 'AS001', name: 'CRM Database', type: 'Database', environment: 'Production', status: 'Active', dependencies: 3, risk: 'Medium' },
    { id: 'AS002', name: 'Web Frontend', type: 'Application', environment: 'Production', status: 'Active', dependencies: 5, risk: 'Low' },
    { id: 'AS003', name: 'API Gateway', type: 'Service', environment: 'Production', status: 'Active', dependencies: 8, risk: 'High' },
    { id: 'AS004', name: 'Legacy ERP', type: 'Application', environment: 'Production', status: 'Critical', dependencies: 12, risk: 'High' },
    { id: 'AS005', name: 'Analytics DB', type: 'Database', environment: 'Staging', status: 'Active', dependencies: 2, risk: 'Low' },
  ];

  const infrastructureMetrics = [
    { metric: 'Total Servers', value: '156', change: '+12%' },
    { metric: 'Applications', value: '247', change: '+8%' },
    { metric: 'Databases', value: '89', change: '+5%' },
    { metric: 'Dependencies', value: '1,247', change: '+15%' },
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
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Discovery Phase</h1>
                  <p className="text-lg text-gray-600">
                    AI-powered discovery and inventory of your IT landscape
                  </p>
                </div>
                <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                  <Download className="h-5 w-5" />
                  <span>Export Report</span>
                </button>
              </div>
            </div>

            {/* Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {infrastructureMetrics.map((metric) => (
                <div key={metric.metric} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{metric.metric}</p>
                      <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                    </div>
                    <span className="text-sm font-medium text-green-600">{metric.change}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Discovery Status */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Database className="h-8 w-8 text-blue-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Application Discovery</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Scanned</span>
                    <span className="font-medium">247/250</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '98.8%' }}></div>
                  </div>
                  <p className="text-sm text-gray-500">3 applications remaining</p>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Network className="h-8 w-8 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Dependency Mapping</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Mapped</span>
                    <span className="font-medium">1,247/1,300</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '95.9%' }}></div>
                  </div>
                  <p className="text-sm text-gray-500">53 dependencies remaining</p>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-8 w-8 text-purple-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Performance Analysis</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Analyzed</span>
                    <span className="font-medium">156/156</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                  <p className="text-sm text-gray-500">Analysis complete</p>
                </div>
              </div>
            </div>

            {/* Discovered Assets Table */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Discovered Assets</h3>
                  <div className="flex items-center space-x-3">
                    <select 
                      value={selectedFilter} 
                      onChange={(e) => setSelectedFilter(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="all">All Types</option>
                      <option value="application">Applications</option>
                      <option value="database">Databases</option>
                      <option value="service">Services</option>
                    </select>
                    <button className="bg-gray-100 text-gray-700 px-3 py-2 rounded-md hover:bg-gray-200 transition-colors flex items-center space-x-2">
                      <Filter className="h-4 w-4" />
                      <span>Filter</span>
                    </button>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Environment</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dependencies</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Level</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {discoveredAssets.map((asset) => (
                      <tr key={asset.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{asset.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.environment}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            asset.status === 'Active' ? 'bg-green-100 text-green-800' :
                            asset.status === 'Critical' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {asset.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.dependencies}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            asset.risk === 'High' ? 'bg-red-100 text-red-800' :
                            asset.risk === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {asset.risk}
                          </span>
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

export default Discovery;
