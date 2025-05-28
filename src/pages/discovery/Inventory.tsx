import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { Download, Filter, Database, Server, HardDrive, RefreshCw, Router, Shield, Cpu, Cloud, Zap } from 'lucide-react';
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
    devices: 0,
    unknown: 0,
    discovered: 0,
    pending: 0,
    device_breakdown: {
      network: 0,
      storage: 0,
      security: 0,
      infrastructure: 0,
      virtualization: 0
    }
  });
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('test');
  const [suggestedHeaders, setSuggestedHeaders] = useState([]);

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
        devices: 0,
        unknown: 0,
        discovered: 0,
        pending: 0,
        device_breakdown: {
          network: 0,
          storage: 0,
          security: 0,
          infrastructure: 0,
          virtualization: 0
        }
      });
      setLastUpdated(response.lastUpdated);
      setDataSource(response.dataSource || 'test');
      setSuggestedHeaders(response.suggestedHeaders || []);
      
    } catch (error) {
      console.error('Failed to fetch assets:', error);
      setError(error.message);
      
      // Set error state - the backend will return test data by default
      setDataSource('error');
      setAssets([]);
      setSummary({
        total: 0,
        applications: 0,
        servers: 0,
        databases: 0,
        devices: 0,
        unknown: 0,
        discovered: 0,
        pending: 0,
        device_breakdown: {
          network: 0,
          storage: 0,
          security: 0,
          infrastructure: 0,
          virtualization: 0
        }
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
      case 'Network Device': return Router;
      case 'Storage Device': return HardDrive;
      case 'Security Device': return Shield;
      case 'Infrastructure Device': return Cpu;
      case 'Virtualization Platform': return Cloud;
      case 'Unknown': return Zap;
      default: return Database;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'Application': return 'text-blue-500';
      case 'Server': return 'text-green-500';
      case 'Database': return 'text-purple-500';
      case 'Network Device': return 'text-orange-500';
      case 'Storage Device': return 'text-yellow-500';
      case 'Security Device': return 'text-red-500';
      case 'Infrastructure Device': return 'text-gray-500';
      case 'Virtualization Platform': return 'text-indigo-500';
      case 'Unknown': return 'text-gray-400';
      default: return 'text-gray-500';
    }
  };

  const getSixRReadinessColor = (readiness) => {
    switch (readiness) {
      case 'Ready': return 'bg-green-100 text-green-800';
      case 'Not Applicable': return 'bg-gray-100 text-gray-600';
      case 'Needs Owner Info':
      case 'Needs Infrastructure Data':
      case 'Needs Version Info': return 'bg-yellow-100 text-yellow-800';
      case 'Insufficient Data':
      case 'Type Classification Needed': return 'bg-red-100 text-red-800';
      case 'Complex Analysis Required': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getComplexityColor = (complexity) => {
    switch (complexity) {
      case 'Low': return 'bg-green-100 text-green-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'High': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const filteredAssets = assets.filter(asset => {
    const typeMatch = selectedFilter === 'all' || asset.type.toLowerCase().replace(' ', '_') === selectedFilter;
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
                        <strong>Error:</strong> {error} - Unable to load data
                      </span>
                    ) : dataSource === 'live' ? (
                      <span className="text-green-600">
                        <strong>Live Data:</strong> Showing {assets.length} processed assets from CMDB import
                      </span>
                    ) : dataSource === 'test' ? (
                      <span className="text-blue-600">
                        <strong>Test Data:</strong> Showing sample data for UI development - Upload and process CMDB files to see your real assets
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

            {/* Enhanced Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
              {/* Primary Asset Types */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <Database className="h-6 w-6 text-blue-500" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Applications</h4>
                    <p className="text-xl font-bold text-blue-600">
                      {isLoading ? '...' : summary.applications}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <Server className="h-6 w-6 text-green-500" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Servers</h4>
                    <p className="text-xl font-bold text-green-600">
                      {isLoading ? '...' : summary.servers}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <HardDrive className="h-6 w-6 text-purple-500" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Databases</h4>
                    <p className="text-xl font-bold text-purple-600">
                      {isLoading ? '...' : summary.databases}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Device Summary */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <Router className="h-6 w-6 text-orange-500" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Devices</h4>
                    <p className="text-xl font-bold text-orange-600">
                      {isLoading ? '...' : summary.devices}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Unknown Assets */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <Zap className="h-6 w-6 text-gray-400" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Unknown</h4>
                    <p className="text-xl font-bold text-gray-600">
                      {isLoading ? '...' : summary.unknown}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Total */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center space-x-2">
                  <div className="h-6 w-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-blue-600">T</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">Total</h4>
                    <p className="text-xl font-bold text-gray-900">
                      {isLoading ? '...' : summary.total}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Device Breakdown */}
            {summary.devices > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Device Breakdown</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center">
                    <Router className="h-8 w-8 text-orange-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Network</p>
                    <p className="text-lg font-bold text-orange-600">{summary.device_breakdown.network}</p>
                  </div>
                  <div className="text-center">
                    <HardDrive className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Storage</p>
                    <p className="text-lg font-bold text-yellow-600">{summary.device_breakdown.storage}</p>
                  </div>
                  <div className="text-center">
                    <Shield className="h-8 w-8 text-red-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Security</p>
                    <p className="text-lg font-bold text-red-600">{summary.device_breakdown.security}</p>
                  </div>
                  <div className="text-center">
                    <Cpu className="h-8 w-8 text-gray-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Infrastructure</p>
                    <p className="text-lg font-bold text-gray-600">{summary.device_breakdown.infrastructure}</p>
                  </div>
                  <div className="text-center">
                    <Cloud className="h-8 w-8 text-indigo-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Virtualization</p>
                    <p className="text-lg font-bold text-indigo-600">{summary.device_breakdown.virtualization}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Suggested Headers Info */}
            {suggestedHeaders.length > 0 && dataSource === 'test' && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-blue-800">AI-Generated Table Headers</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      The table columns below are dynamically generated based on your data structure. 
                      When you process real CMDB data, the headers will automatically adjust to show the most relevant fields.
                    </p>
                    <p className="text-xs text-blue-600 mt-2">
                      Current headers: {suggestedHeaders.map(h => h.label).join(', ')}
                    </p>
                  </div>
                </div>
              </div>
            )}

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
                      <option value="network_device">Network Devices</option>
                      <option value="storage_device">Storage Devices</option>
                      <option value="security_device">Security Devices</option>
                      <option value="infrastructure_device">Infrastructure</option>
                      <option value="virtualization_platform">Virtualization</option>
                      <option value="unknown">Unknown</option>
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
                      {suggestedHeaders.length > 0 ? (
                        suggestedHeaders.map((header) => (
                          <th 
                            key={header.key} 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            title={header.description}
                          >
                            {header.label}
                          </th>
                        ))
                      ) : (
                        // Fallback headers if no suggested headers available
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tech Stack</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        </>
                      )}
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
                            {suggestedHeaders.length > 0 ? (
                              suggestedHeaders.map((header) => (
                                <td key={header.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  {header.key === 'type' ? (
                                    <div className="flex items-center space-x-2">
                                      <Icon className={`h-4 w-4 ${getTypeColor(asset[header.key])}`} />
                                      <span>{asset[header.key]}</span>
                                    </div>
                                  ) : header.key === 'status' ? (
                                    <span className={`px-2 py-1 text-xs rounded-full ${
                                      asset.status === 'Discovered' ? 'bg-green-100 text-green-800' :
                                      'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {asset[header.key]}
                                    </span>
                                  ) : header.key === 'sixr_ready' ? (
                                    <span className={`px-2 py-1 text-xs rounded-full ${getSixRReadinessColor(asset[header.key])}`}>
                                      {asset[header.key] || 'Unknown'}
                                    </span>
                                  ) : header.key === 'migration_complexity' ? (
                                    <span className={`px-2 py-1 text-xs rounded-full ${getComplexityColor(asset[header.key])}`}>
                                      {asset[header.key] || 'Unknown'}
                                    </span>
                                  ) : header.key === 'cpuCores' || header.key === 'memoryGb' || header.key === 'storageGb' ? (
                                    asset[header.key] ? `${asset[header.key]}${header.key === 'cpuCores' ? '' : ' GB'}` : '-'
                                  ) : (
                                    asset[header.key] || '-'
                                  )}
                                </td>
                              ))
                            ) : (
                              // Fallback static columns with enhanced type display
                              <>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{asset.id}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  <div className="flex items-center space-x-2">
                                    <Icon className={`h-4 w-4 ${getTypeColor(asset.type)}`} />
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
                              </>
                            )}
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
