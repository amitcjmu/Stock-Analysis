
import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { Database, Network, Activity, Download, Filter, RefreshCw, AlertCircle, Menu, X } from 'lucide-react';
import { AssetAPI } from '../lib/api/assets';
import type { Asset } from '../types/asset';
import { getUserFriendlyErrorMessage, getErrorTitle, isRetryableError } from '../utils/errorHandling';
import { withRetry } from '../utils/retry';

const Discovery = (): JSX.Element => {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [discoveredAssets, setDiscoveredAssets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<{ title: string; message: string; canRetry: boolean } | null>(null);
  const [totalAssets, setTotalAssets] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dashboardMetrics, setDashboardMetrics] = useState({
    servers: 0,
    applications: 0,
    databases: 0,
    dependencies: 0
  });

  useEffect(() => {
    fetchAssets();
    fetchDashboardMetrics();
  }, [selectedFilter]);

  const fetchDashboardMetrics = async () => {
    try {
      const { apiCall } = await import('../config/api');
      const response = await apiCall('/unified-discovery/assets/summary');
      
      if (response && response.dashboard_metrics) {
        setDashboardMetrics(response.dashboard_metrics);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      // Keep default zeros on error
    }
  };

  const fetchAssets = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = selectedFilter !== 'all' ? { asset_type: selectedFilter } : {};

      // Use retry wrapper for the API call
      const response = await withRetry(
        () => AssetAPI.getAssets({ ...params, page_size: 100 }),
        { maxAttempts: 3 }
      );

      if (response.assets && Array.isArray(response.assets)) {
        // Transform API response to match existing format
        const transformedAssets = response.assets.slice(0, 20).map((asset: Asset) => ({
          id: asset.asset_id || asset.id || `AS${Math.random().toString(36).substr(2, 9)}`,
          name: asset.asset_name || asset.hostname || 'Unknown Asset',
          type: asset.asset_type || 'Unknown',
          environment: asset.environment || 'Production',
          status: asset.lifecycle_stage || 'Active',
          dependencies: asset.dependency_count || 0,
          risk: asset.business_criticality || 'Medium'
        }));
        setDiscoveredAssets(transformedAssets);
        setTotalAssets(response.total || transformedAssets.length);
      } else {
        setDiscoveredAssets([]);
        setTotalAssets(0);
        setError({
          title: 'No Data Available',
          message: 'No asset data received from the server. The discovery service may not be configured yet.',
          canRetry: true
        });
      }
    } catch (apiError: any) {
      console.error('Failed to fetch assets:', apiError);
      setDiscoveredAssets([]);
      setTotalAssets(0);

      // Use centralized error handling
      setError({
        title: getErrorTitle(apiError),
        message: getUserFriendlyErrorMessage(apiError),
        canRetry: isRetryableError(apiError)
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    fetchAssets();
  };

  const infrastructureMetrics = [
    { metric: 'Total Servers', value: dashboardMetrics.servers.toString(), change: '' },
    { metric: 'Applications', value: dashboardMetrics.applications.toString(), change: '' },
    { metric: 'Databases', value: dashboardMetrics.databases.toString(), change: '' },
    { metric: 'Dependencies', value: dashboardMetrics.dependencies.toString(), change: '' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 lg:ml-64 transition-all duration-300">
        <main className="p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-6 lg:mb-8">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-6 lg:mb-8">
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
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 mb-6 lg:mb-8">
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
              <div className="p-4 lg:p-6 border-b border-gray-200">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <h3 className="text-lg font-semibold text-gray-900">Discovered Assets</h3>
                  <div className="flex flex-wrap items-center gap-2 lg:gap-3">
                    <select
                      value={selectedFilter}
                      onChange={(e) => setSelectedFilter(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                      disabled={isLoading}
                    >
                      <option value="all">All Types</option>
                      <option value="application">Applications</option>
                      <option value="database">Databases</option>
                      <option value="service">Services</option>
                    </select>
                    <button
                      className="bg-gray-100 text-gray-700 px-3 py-2 rounded-md hover:bg-gray-200 transition-colors flex items-center space-x-2 disabled:opacity-50"
                      disabled={isLoading}
                    >
                      <Filter className="h-4 w-4" />
                      <span>Filter</span>
                    </button>
                    {error && (
                      <button
                        onClick={handleRetry}
                        className="bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
                        disabled={isLoading}
                      >
                        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                        <span>Retry</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Loading State */}
              {isLoading && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                    <p className="text-gray-600">Loading assets...</p>
                    <p className="text-sm text-gray-500 mt-1">This may take a moment while we fetch your data</p>
                  </div>
                </div>
              )}

              {/* Error State */}
              {error && !isLoading && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center max-w-md">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">{error.title}</h3>
                    <p className="text-gray-600 mb-4">{error.message}</p>
                    {error.canRetry && (
                      <button
                        onClick={handleRetry}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
                      >
                        <RefreshCw className="h-4 w-4" />
                        <span>Try Again</span>
                      </button>
                    )}
                    {!error.canRetry && (
                      <p className="text-sm text-gray-500 mt-2">
                        Please contact support if this issue persists.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!isLoading && !error && discoveredAssets.length === 0 && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Assets Found</h3>
                    <p className="text-gray-600 mb-4">No assets match your current filter criteria.</p>
                    <button
                      onClick={() => setSelectedFilter('all')}
                      className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      Clear Filters
                    </button>
                  </div>
                </div>
              )}

              {/* Assets Table */}
              {!isLoading && !error && discoveredAssets.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-full">
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
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Discovery;
