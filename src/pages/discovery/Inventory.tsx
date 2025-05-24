
import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Download, Filter, Database, Server, HardDrive } from 'lucide-react';

const Inventory = () => {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedDept, setSelectedDept] = useState('all');

  const assets = [
    { id: 'APP001', type: 'Application', name: 'CRM System', techStack: 'Java 8', dept: 'Finance', status: 'Discovered' },
    { id: 'APP002', type: 'Application', name: 'HR Portal', techStack: '.NET Core', dept: 'HR', status: 'Discovered' },
    { id: 'SRV001', type: 'Server', name: 'Web Server 01', techStack: 'Linux RHEL 8', dept: 'IT', status: 'Discovered' },
    { id: 'SRV002', type: 'Server', name: 'App Server 01', techStack: 'Windows Server 2019', dept: 'IT', status: 'Pending' },
    { id: 'DB001', type: 'Database', name: 'Customer DB', techStack: 'MySQL 8.0', dept: 'Finance', status: 'Discovered' },
    { id: 'DB002', type: 'Database', name: 'Analytics DB', techStack: 'PostgreSQL 13', dept: 'Marketing', status: 'Pending' },
    { id: 'APP003', type: 'Application', name: 'Legacy ERP', techStack: 'COBOL', dept: 'Finance', status: 'Discovered' },
    { id: 'SRV003', type: 'Server', name: 'Database Server', techStack: 'Linux Ubuntu 20.04', dept: 'IT', status: 'Discovered' }
  ];

  const getTypeIcon = (type) => {
    switch (type) {
      case 'Application': return Database;
      case 'Server': return Server;
      case 'Database': return HardDrive;
      default: return Database;
    }
  };

  const filteredAssets = assets.filter(asset => {
    const typeMatch = selectedFilter === 'all' || asset.type.toLowerCase() === selectedFilter;
    const deptMatch = selectedDept === 'all' || asset.dept === selectedDept;
    return typeMatch && deptMatch;
  });

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Asset Inventory</h1>
                  <p className="text-lg text-gray-600">
                    Comprehensive inventory of discovered IT assets
                  </p>
                </div>
                <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                  <Download className="h-5 w-5" />
                  <span>Export CSV</span>
                </button>
              </div>
              <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>Coming Soon:</strong> CloudBridge Scanning - Enhanced asset discovery with automated classification
                </p>
              </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Database className="h-8 w-8 text-blue-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Applications</h3>
                    <p className="text-2xl font-bold text-blue-600">{assets.filter(a => a.type === 'Application').length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Server className="h-8 w-8 text-green-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Servers</h3>
                    <p className="text-2xl font-bold text-green-600">{assets.filter(a => a.type === 'Server').length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <HardDrive className="h-8 w-8 text-purple-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Databases</h3>
                    <p className="text-2xl font-bold text-purple-600">{assets.filter(a => a.type === 'Database').length}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Asset Table */}
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
                      <option value="server">Servers</option>
                      <option value="database">Databases</option>
                    </select>
                    <select 
                      value={selectedDept} 
                      onChange={(e) => setSelectedDept(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="all">All Departments</option>
                      <option value="Finance">Finance</option>
                      <option value="HR">HR</option>
                      <option value="IT">IT</option>
                      <option value="Marketing">Marketing</option>
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
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tech Stack</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredAssets.map((asset) => {
                      const Icon = getTypeIcon(asset.type);
                      return (
                        <tr key={asset.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{asset.id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center space-x-2">
                              <Icon className="h-4 w-4 text-gray-500" />
                              <span>{asset.type}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.techStack}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.dept}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              asset.status === 'Discovered' ? 'bg-green-100 text-green-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {asset.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
      <FeedbackWidget />
    </div>
  );
};

export default Inventory;
