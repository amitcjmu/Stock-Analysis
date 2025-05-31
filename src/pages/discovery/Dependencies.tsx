
import React from 'react';
import Sidebar from '../../components/Sidebar';
import { Network, Database, Server, ArrowRight } from 'lucide-react';

const Dependencies = () => {
  const dependencies = [
    { source: 'CRM System (APP001)', target: 'Web Server 01 (SRV001)', type: 'Network', strength: 'High' },
    { source: 'Web Server 01 (SRV001)', target: 'Customer DB (DB001)', type: 'Data', strength: 'Critical' },
    { source: 'HR Portal (APP002)', target: 'App Server 01 (SRV002)', type: 'Network', strength: 'Medium' },
    { source: 'App Server 01 (SRV002)', target: 'Analytics DB (DB002)', type: 'Data', strength: 'Low' },
    { source: 'Legacy ERP (APP003)', target: 'Database Server (SRV003)', type: 'Network', strength: 'Critical' },
    { source: 'Database Server (SRV003)', target: 'Customer DB (DB001)', type: 'Data', strength: 'High' }
  ];

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'Critical': return 'bg-red-100 text-red-800';
      case 'High': return 'bg-orange-100 text-orange-800';
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Dependency Mapping</h1>
              <p className="text-lg text-gray-600">
                Visualize relationships and dependencies between IT assets
              </p>
              <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>Coming Soon:</strong> Dependency Mapping via CloudBridge - Automated discovery of application dependencies
                </p>
              </div>
            </div>

            {/* Dependency Visualization Placeholder */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Dependency Graph</h2>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center bg-gray-50">
                <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Interactive Dependency Graph</h3>
                <p className="text-gray-600 mb-4">
                  Visual representation of asset relationships and dependencies
                </p>
                <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-blue-500 rounded"></div>
                    <span>Applications</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-green-500 rounded"></div>
                    <span>Servers</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-purple-500 rounded"></div>
                    <span>Databases</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Dependency Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Network className="h-8 w-8 text-blue-500" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Total Dependencies</h3>
                    <p className="text-2xl font-bold text-gray-900">{dependencies.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">C</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Critical</h3>
                    <p className="text-2xl font-bold text-red-600">{dependencies.filter(d => d.strength === 'Critical').length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm font-bold">H</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">High Risk</h3>
                    <p className="text-2xl font-bold text-orange-600">{dependencies.filter(d => d.strength === 'High').length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Database className="h-8 w-8 text-purple-500" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Data Flows</h3>
                    <p className="text-2xl font-bold text-purple-600">{dependencies.filter(d => d.type === 'Data').length}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Dependencies Table */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Discovered Dependencies</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source Asset</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Relationship</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target Asset</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dependency Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strength</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dependencies.map((dep, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{dep.source}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <ArrowRight className="h-4 w-4" />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{dep.target}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            dep.type === 'Network' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                          }`}>
                            {dep.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${getStrengthColor(dep.strength)}`}>
                            {dep.strength}
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

export default Dependencies;
