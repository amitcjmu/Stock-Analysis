
import type React from 'react';
import Sidebar from '../../components/Sidebar';
import { Activity, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const Scan = (): JSX.Element => {
  const scanProgress = 75;
  const scannedApps = 200;
  const totalApps = 250;
  const scannedServers = 375;
  const totalServers = 500;
  const scannedDatabases = 38;
  const totalDatabases = 50;

  const recentLogs = [
    { id: 1, message: 'CRM System (APP001) discovered', status: 'success', timestamp: '2 minutes ago' },
    { id: 2, message: 'Web Server 01 (SRV001) scanned successfully', status: 'success', timestamp: '5 minutes ago' },
    { id: 3, message: 'Database connection test for DB001 completed', status: 'success', timestamp: '8 minutes ago' },
    { id: 4, message: 'Network scan for subnet 192.168.1.0/24 in progress', status: 'progress', timestamp: '12 minutes ago' },
    { id: 5, message: 'Legacy ERP (APP003) metadata extraction completed', status: 'success', timestamp: '15 minutes ago' },
    { id: 6, message: 'Authentication failed for Server SRV004', status: 'error', timestamp: '18 minutes ago' },
    { id: 7, message: 'HR Portal (APP002) dependency analysis started', status: 'progress', timestamp: '22 minutes ago' },
    { id: 8, message: 'Database inventory scan completed for Finance dept', status: 'success', timestamp: '25 minutes ago' }
  ];

  const getStatusIcon = (status): JSX.Element => {
    switch (status) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'progress': return <Clock className="h-4 w-4 text-blue-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Scanning Progress</h1>
              <p className="text-lg text-gray-600">
                Monitor real-time discovery and scanning operations
              </p>
              <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>Coming Soon:</strong> CloudBridge Agent-Based Scanning - Enhanced automated discovery with detailed asset profiling
                </p>
              </div>
            </div>

            {/* Overall Progress */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Overall Scanning Progress</h2>
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-lg font-medium text-gray-900">Discovery Progress</span>
                  <span className="text-lg font-bold text-blue-600">{scanProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-blue-500 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${scanProgress}%` }}
                  ></div>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                Scanning in progress across all environments and asset types
              </p>
            </div>

            {/* Detailed Progress */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-8 w-8 text-blue-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Applications</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Scanned</span>
                    <span className="font-medium">{scannedApps}/{totalApps}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(scannedApps / totalApps) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-500">{totalApps - scannedApps} applications remaining</p>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-8 w-8 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Servers</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Scanned</span>
                    <span className="font-medium">{scannedServers}/{totalServers}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(scannedServers / totalServers) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-500">{totalServers - scannedServers} servers remaining</p>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-8 w-8 text-purple-500" />
                  <h3 className="text-lg font-semibold text-gray-900">Databases</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Scanned</span>
                    <span className="font-medium">{scannedDatabases}/{totalDatabases}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(scannedDatabases / totalDatabases) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-500">{totalDatabases - scannedDatabases} databases remaining</p>
                </div>
              </div>
            </div>

            {/* Scan Activity Log */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Real-time Scan Activity</h3>
              </div>
              <div className="p-6">
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {recentLogs.map((log) => (
                    <div key={log.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="flex-shrink-0 mt-0.5">
                        {getStatusIcon(log.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900">{log.message}</p>
                        <p className="text-xs text-gray-500">{log.timestamp}</p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          log.status === 'success' ? 'bg-green-100 text-green-800' :
                          log.status === 'progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {log.status === 'success' ? 'Completed' :
                           log.status === 'progress' ? 'In Progress' : 'Error'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Scan;
