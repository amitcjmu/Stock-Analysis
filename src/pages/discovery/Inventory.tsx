
import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Download, Filter, Database, Server, HardDrive, RefreshCw } from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

const Inventory = () => {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedDept, setSelectedDept] = useState('all');
  const [assets, setAssets] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    applications: 0,
    servers: 0,
    databases: 0,
    discovered: 0,
    pending: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  // Fetch assets from API
  const fetchAssets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS);
      
      setAssets(response.assets || []);
      setSummary(response.summary || {
        total: 0,
        applications: 0,
        servers: 0,
        databases: 0,
        discovered: 0,
        pending: 0
      });
      setLastUpdated(response.lastUpdated);
      
    } catch (error) {
      console.error('Failed to fetch assets:', error);
      setError(error.message);
      
      // Fallback to sample data if API fails
      const fallbackAssets = [
        { id: 'APP001', type: 'Application', name: 'CRM System', techStack: 'Java 8', department: 'Finance', status: 'Discovered' },
        { id: 'APP002', type: 'Application', name: 'HR Portal', techStack: '.NET Core', department: 'HR', status: 'Discovered' },
        { id: 'SRV001', type: 'Server', name: 'Web Server 01', techStack: 'Linux RHEL 8', department: 'IT', status: 'Discovered' },
        { id: 'SRV002', type: 'Server', name: 'App Server 01', techStack: 'Windows Server 2019', department: 'IT', status: 'Pending' },
        { id: 'DB001', type: 'Database', name: 'Customer DB', techStack: 'MySQL 8.0', department: 'Finance', status: 'Discovered' },
        { id: 'DB002', type: 'Database', name: 'Analytics DB', techStack: 'PostgreSQL 13', department: 'Marketing', status: 'Pending' },
        { id: 'APP003', type: 'Application', name: 'Legacy ERP', techStack: 'COBOL', department: 'Finance', status: 'Discovered' },
        { id: 'SRV003', type: 'Server', name: 'Database Server', techStack: 'Linux Ubuntu 20.04', department: 'IT', status: 'Discovered' }
      ];
      
      setAssets(fallbackAssets);
      setSummary({
        total: fallbackAssets.length,
        applications: fallbackAssets.filter(a => a.type === 'Application').length,
        servers: fallbackAssets.filter(a => a.type === 'Server').length,
        databases: fallbackAssets.filter(a => a.type === 'Database').length,
        discovered: fallbackAssets.filter(a => a.status === 'Discovered').length,
        pending: fallbackAssets.filter(a => a.status === 'Pending').length
      });
      
    } finally {
      setIsLoading(false);
    }
  };

  // Load assets on component mount
  useEffect(() => {
    fetchAssets();
  }, []);

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
    const deptMatch = selectedDept === 'all' || asset.department === selectedDept;
    return typeMatch && deptMatch;
  });

  // Get unique departments for filter dropdown
  const uniqueDepartments = [...new Set(assets.map(asset => asset.department).filter(dept => dept && dept !== 'Unknown'))];

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
                <div className="flex items-center space-x-3">
                  <button 
                    onClick={fetchAssets}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                    <Download className="h-5 w-5" />
                    <span>Export CSV</span>
                  </button>
                </div>
              </div>
              <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-700">
                    {error ? (
                      <span className="text-red-600">
                        <strong>Error:</strong> {error} - Showing sample data
                      </span>
                    ) : assets.length > 0 ? (
                      <span className="text-green-600">
                        <strong>Live Data:</strong> Showing {assets.length} processed assets from CMDB import
                      </span>
                    ) : (
                      <span>
                        <strong>No Data:</strong> Upload and process CMDB files to see your assets here
                      </span>
                    )}
                  </p>
                  {lastUpdated && (
                    <p className="text-xs text-gray-500">
                      Last updated: {new Date(lastUpdated).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Database className="h-8 w-8 text-blue-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Applications</h3>
                    <p className="text-2xl font-bold text-blue-600">
                      {isLoading ? '...' : summary.applications}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <Server className="h-8 w-8 text-green-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Servers</h3>
                    <p className="text-2xl font-bold text-green-600">
                      {isLoading ? '...' : summary.servers}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3">
                  <HardDrive className="h-8 w-8 text-purple-500" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Databases</h3>
                    <p className="text-2xl font-bold text-purple-600">
                      {isLoading ? '...' : summary.databases}
                    </p>
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
                      {uniqueDepartments.map(dept => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
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
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-8 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <RefreshCw className="h-5 w-5 animate-spin text-gray-400" />
                            <span className="text-gray-500">Loading assets...</span>
                          </div>
                        </td>
                      </tr>
                    ) : filteredAssets.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-8 text-center">
                          <div className="text-gray-500">
                            {assets.length === 0 ? (
                              <div>
                                <p className="mb-2">No assets found</p>
                                <p className="text-sm">Upload and process CMDB files to see your assets here</p>
                              </div>
                            ) : (
                              <p>No assets match the current filters</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    ) : (
                      filteredAssets.map((asset) => {
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
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{asset.department}</td>
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
                      })
                    )}
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
