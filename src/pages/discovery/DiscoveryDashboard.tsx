import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import FeedbackWidget from '../../components/FeedbackWidget';
import { 
  BarChart3, TrendingUp, Activity, AlertTriangle, CheckCircle,
  FileText, Database, Server, Network, Shield, Cloud,
  Clock, LineChart, Bug, Zap, Users, Sparkles, Settings, ArrowRight
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';
import { Link } from 'react-router-dom';

interface DiscoveryMetrics {
  totalAssets: number;
  totalApplications: number;
  applicationToServerMapping: number;
  dependencyMappingComplete: number;
  techDebtItems: number;
  criticalIssues: number;
  discoveryCompleteness: number;
  dataQuality: number;
}

interface ApplicationLandscape {
  applications: Array<{
    id: string;
    name: string;
    environment: string;
    criticality: string;
    techStack: string[];
    serverCount: number;
    databaseCount: number;
    dependencyCount: number;
    techDebtScore: number;
    cloudReadiness: number;
  }>;
  summary: {
    byEnvironment: { [key: string]: number };
    byCriticality: { [key: string]: number };
    byTechStack: { [key: string]: number };
  };
}

interface InfrastructureLandscape {
  servers: {
    total: number;
    physical: number;
    virtual: number;
    cloud: number;
    supportedOS: number;
    deprecatedOS: number;
  };
  databases: {
    total: number;
    supportedVersions: number;
    deprecatedVersions: number;
    endOfLife: number;
  };
  networks: {
    devices: number;
    securityDevices: number;
    storageDevices: number;
  };
}

const DiscoveryDashboard = () => {
  const [metrics, setMetrics] = useState<DiscoveryMetrics>({
    totalAssets: 0,
    totalApplications: 0,
    applicationToServerMapping: 0,
    dependencyMappingComplete: 0,
    techDebtItems: 0,
    criticalIssues: 0,
    discoveryCompleteness: 0,
    dataQuality: 0
  });
  
  const [applicationLandscape, setApplicationLandscape] = useState<ApplicationLandscape>({
    applications: [],
    summary: {
      byEnvironment: {},
      byCriticality: {},
      byTechStack: {}
    }
  });
  
  const [infrastructureLandscape, setInfrastructureLandscape] = useState<InfrastructureLandscape>({
    servers: {
      total: 0,
      physical: 0,
      virtual: 0,
      cloud: 0,
      supportedOS: 0,
      deprecatedOS: 0
    },
    databases: {
      total: 0,
      supportedVersions: 0,
      deprecatedVersions: 0,
      endOfLife: 0
    },
    networks: {
      devices: 0,
      securityDevices: 0,
      storageDevices: 0
    }
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [activeView, setActiveView] = useState('overview');

  useEffect(() => {
    fetchDiscoveryMetrics();
    fetchApplicationLandscape();
    fetchInfrastructureLandscape();
  }, []);

  const fetchDiscoveryMetrics = async () => {
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/discovery-metrics`);
      setMetrics(response.metrics || metrics);
    } catch (error) {
      console.error('Failed to fetch discovery metrics:', error);
    }
  };

  const fetchApplicationLandscape = async () => {
    try {
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/application-landscape`);
      setApplicationLandscape(response.landscape || applicationLandscape);
    } catch (error) {
      console.error('Failed to fetch application landscape:', error);
    }
  };

  const fetchInfrastructureLandscape = async () => {
    try {
      setIsLoading(true);
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/infrastructure-landscape`);
      setInfrastructureLandscape(response.landscape || infrastructureLandscape);
    } catch (error) {
      console.error('Failed to fetch infrastructure landscape:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCompletenessColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompletenessIcon = (percentage: number) => {
    if (percentage >= 90) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (percentage >= 70) return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <Bug className="h-5 w-5 text-red-600" />;
  };

  const CloudReadinessChart = ({ applications }: { applications: any[] }) => {
    const readinessLevels = {
      high: applications.filter(app => app.cloudReadiness >= 80).length,
      medium: applications.filter(app => app.cloudReadiness >= 50 && app.cloudReadiness < 80).length,
      low: applications.filter(app => app.cloudReadiness < 50).length
    };

    return (
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{readinessLevels.high}</div>
          <div className="text-sm text-gray-600">High Readiness</div>
          <div className="text-xs text-gray-500">≥80%</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{readinessLevels.medium}</div>
          <div className="text-sm text-gray-600">Medium Readiness</div>
          <div className="text-xs text-gray-500">50-79%</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{readinessLevels.low}</div>
          <div className="text-sm text-gray-600">Low Readiness</div>
          <div className="text-xs text-gray-500">&lt;50%</div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Discovery Dashboard</h1>
              <p className="text-lg text-gray-600">
                Complete view of your IT landscape for cloud modernization planning
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="mb-8">
              <nav className="flex space-x-8">
                {[
                  { id: 'overview', label: 'Overview', icon: BarChart3 },
                  { id: 'applications', label: 'Applications', icon: FileText },
                  { id: 'infrastructure', label: 'Infrastructure', icon: Server },
                  { id: 'readiness', label: 'Cloud Readiness', icon: Cloud }
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveView(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium ${
                        activeView === tab.id
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Overview Tab */}
            {activeView === 'overview' && (
              <div className="space-y-8">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics.totalAssets}</h3>
                        <p className="text-sm text-gray-600">Total Assets Discovered</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-blue-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics.totalApplications}</h3>
                        <p className="text-sm text-gray-600">Applications Identified</p>
                      </div>
                      <FileText className="h-8 w-8 text-green-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-2xl font-bold text-red-600">{metrics.criticalIssues}</h3>
                        <p className="text-sm text-gray-600">Critical Issues</p>
                      </div>
                      <AlertTriangle className="h-8 w-8 text-red-500" />
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className={`text-2xl font-bold ${getCompletenessColor(metrics.discoveryCompleteness)}`}>
                          {metrics.discoveryCompleteness}%
                        </h3>
                        <p className="text-sm text-gray-600">Discovery Complete</p>
                      </div>
                      {getCompletenessIcon(metrics.discoveryCompleteness)}
                    </div>
                  </div>
                </div>

                {/* Discovery Progress */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Discovery Progress</h2>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Application-Server Mapping</span>
                          <span className="text-sm font-medium">{metrics.applicationToServerMapping}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${metrics.applicationToServerMapping}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Dependency Mapping</span>
                          <span className="text-sm font-medium">{metrics.dependencyMappingComplete}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${metrics.dependencyMappingComplete}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Data Quality</span>
                          <span className="text-sm font-medium">{metrics.dataQuality}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-purple-600 h-2 rounded-full" 
                            style={{ width: `${metrics.dataQuality}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Tech Debt Overview</h2>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-orange-600 mb-2">{metrics.techDebtItems}</div>
                      <p className="text-gray-600 mb-4">Items requiring attention</p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="text-center">
                          <div className="text-lg font-semibold text-red-600">{Math.round(metrics.techDebtItems * 0.3)}</div>
                          <div className="text-gray-600">End of Life</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-yellow-600">{Math.round(metrics.techDebtItems * 0.7)}</div>
                          <div className="text-gray-600">Deprecated</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Applications Tab */}
            {activeView === 'applications' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">By Environment</h3>
                    <div className="space-y-2">
                      {Object.entries(applicationLandscape.summary.byEnvironment).map(([env, count]) => (
                        <div key={env} className="flex justify-between">
                          <span className="text-gray-600">{env}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">By Criticality</h3>
                    <div className="space-y-2">
                      {Object.entries(applicationLandscape.summary.byCriticality).map(([crit, count]) => (
                        <div key={crit} className="flex justify-between">
                          <span className="text-gray-600">{crit}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Cloud Readiness</h3>
                    <CloudReadinessChart applications={applicationLandscape.applications} />
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Application Portfolio</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Environment</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tech Stack</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Servers</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dependencies</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cloud Readiness</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {applicationLandscape.applications.slice(0, 10).map((app) => (
                          <tr key={app.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{app.name}</div>
                              <div className="text-sm text-gray-500">{app.criticality}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{app.environment}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex flex-wrap gap-1">
                                {app.techStack.slice(0, 2).map((tech, idx) => (
                                  <span key={idx} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                    {tech}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{app.serverCount}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{app.dependencyCount}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full ${
                                    app.cloudReadiness >= 80 ? 'bg-green-600' :
                                    app.cloudReadiness >= 50 ? 'bg-yellow-600' : 'bg-red-600'
                                  }`}
                                  style={{ width: `${app.cloudReadiness}%` }}
                                ></div>
                              </div>
                              <span className="text-xs text-gray-500">{app.cloudReadiness}%</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Infrastructure Tab */}
            {activeView === 'infrastructure' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Server Infrastructure</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Servers</span>
                        <span className="font-bold">{infrastructureLandscape.servers.total}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Physical</span>
                        <span className="font-medium">{infrastructureLandscape.servers.physical}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Virtual</span>
                        <span className="font-medium">{infrastructureLandscape.servers.virtual}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Cloud</span>
                        <span className="font-medium">{infrastructureLandscape.servers.cloud}</span>
                      </div>
                      <hr />
                      <div className="flex justify-between">
                        <span className="text-green-600">Supported OS</span>
                        <span className="font-medium text-green-600">{infrastructureLandscape.servers.supportedOS}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-red-600">Deprecated OS</span>
                        <span className="font-medium text-red-600">{infrastructureLandscape.servers.deprecatedOS}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Landscape</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Databases</span>
                        <span className="font-bold">{infrastructureLandscape.databases.total}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-600">Supported Versions</span>
                        <span className="font-medium text-green-600">{infrastructureLandscape.databases.supportedVersions}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-yellow-600">Deprecated</span>
                        <span className="font-medium text-yellow-600">{infrastructureLandscape.databases.deprecatedVersions}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-red-600">End of Life</span>
                        <span className="font-medium text-red-600">{infrastructureLandscape.databases.endOfLife}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Network & Devices</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Network Devices</span>
                        <span className="font-medium">{infrastructureLandscape.networks.devices}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Security Devices</span>
                        <span className="font-medium">{infrastructureLandscape.networks.securityDevices}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Storage Devices</span>
                        <span className="font-medium">{infrastructureLandscape.networks.storageDevices}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Cloud Readiness Tab */}
            {activeView === 'readiness' && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Cloud Modernization Readiness</h2>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Application Readiness Distribution</h3>
                      <CloudReadinessChart applications={applicationLandscape.applications} />
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Readiness by Environment</h3>
                      <div className="space-y-3">
                        {Object.entries(applicationLandscape.summary.byEnvironment).map(([env, count]) => {
                          const envReadiness = applicationLandscape.applications
                            .filter(app => app.environment === env)
                            .reduce((sum, app) => sum + app.cloudReadiness, 0) / count || 0;
                          
                          return (
                            <div key={env} className="flex justify-between items-center">
                              <span className="text-gray-600">{env}</span>
                              <div className="flex items-center space-x-2">
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className={`h-2 rounded-full ${
                                      envReadiness >= 80 ? 'bg-green-600' :
                                      envReadiness >= 50 ? 'bg-yellow-600' : 'bg-red-600'
                                    }`}
                                    style={{ width: `${envReadiness}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-medium">{Math.round(envReadiness)}%</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Cloud Readiness Tab */}
            {activeView === 'cloudReadiness' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Readiness Distribution</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-green-600">High (80-100%)</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness >= 80).length}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-yellow-600">Medium (50-79%)</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness >= 50 && app.cloudReadiness < 80).length}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-red-600">Low (&lt;50%)</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness < 50).length}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">By Environment</h3>
                    <div className="space-y-3">
                      {Object.entries(applicationLandscape.summary.byEnvironment).map(([env, count]) => {
                        const envApps = applicationLandscape.applications.filter(app => app.environment === env);
                        const avgReadiness = envApps.length > 0 
                          ? Math.round(envApps.reduce((sum, app) => sum + app.cloudReadiness, 0) / envApps.length)
                          : 0;
                        
                        return (
                          <div key={env} className="flex justify-between">
                            <span className="text-gray-600">{env}</span>
                            <span className="font-medium">{avgReadiness}% avg</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Migration Priority</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-green-600">Ready to Migrate</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness >= 80).length}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-yellow-600">Needs Preparation</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness >= 50 && app.cloudReadiness < 80).length}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-red-600">Requires Modernization</span>
                        <span className="font-medium">
                          {applicationLandscape.applications.filter(app => app.cloudReadiness < 50).length}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Assessment Score</h3>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600 mb-2">
                        {Math.round(applicationLandscape.applications.reduce((sum, app) => sum + app.cloudReadiness, 0) / applicationLandscape.applications.length || 0)}%
                      </div>
                      <p className="text-gray-600">Overall Readiness</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Readiness Assessment Details</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blocking Factors</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended Actions</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Migration Priority</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {applicationLandscape.applications.slice(0, 10).map((app) => (
                          <tr key={app.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{app.name}</div>
                              <div className="text-sm text-gray-500">{app.environment}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-16 bg-gray-200 rounded-full h-2 mr-3">
                                  <div 
                                    className={`h-2 rounded-full ${
                                      app.cloudReadiness >= 80 ? 'bg-green-600' :
                                      app.cloudReadiness >= 50 ? 'bg-yellow-600' : 'bg-red-600'
                                    }`}
                                    style={{ width: `${app.cloudReadiness}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-medium text-gray-900">{app.cloudReadiness}%</span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-wrap gap-1">
                                {app.techDebtScore > 70 && (
                                  <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Tech Debt</span>
                                )}
                                {app.techStack.some(tech => tech.includes('Legacy')) && (
                                  <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Legacy Tech</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-600">
                              {app.cloudReadiness < 50 ? 'Modernize first' : 
                               app.cloudReadiness < 80 ? 'Minor updates needed' : 'Ready to migrate'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                app.cloudReadiness >= 80 ? 'bg-green-100 text-green-800' :
                                app.cloudReadiness >= 50 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {app.cloudReadiness >= 80 ? 'High' :
                                 app.cloudReadiness >= 50 ? 'Medium' : 'Low'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Discovery Tools Section */}
            <div className="mt-12">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Discovery Tools</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Link
                    to="/discovery/data-cleansing"
                    className="group block p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="bg-yellow-500 p-3 rounded-lg text-white">
                        <Sparkles className="h-6 w-6" />
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                    <h3 className="font-medium text-gray-900 group-hover:text-blue-600 mb-2">
                      Data Cleansing
                    </h3>
                    <p className="text-sm text-gray-600">
                      Human-in-the-loop data quality improvement with AI assistance
                    </p>
                  </Link>

                  <Link
                    to="/discovery/attribute-mapping"
                    className="group block p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="bg-indigo-500 p-3 rounded-lg text-white">
                        <Settings className="h-6 w-6" />
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                    <h3 className="font-medium text-gray-900 group-hover:text-blue-600 mb-2">
                      Attribute Mapping
                    </h3>
                    <p className="text-sm text-gray-600">
                      Train AI crew on field mappings and attribute associations
                    </p>
                  </Link>

                  <Link
                    to="/discovery/tech-debt-analysis"
                    className="group block p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="bg-red-500 p-3 rounded-lg text-white">
                        <BarChart3 className="h-6 w-6" />
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                    <h3 className="font-medium text-gray-900 group-hover:text-blue-600 mb-2">
                      Tech Debt Analysis
                    </h3>
                    <p className="text-sm text-gray-600">
                      Analyze technology stack support and modernization needs
                    </p>
                  </Link>

                  <Link
                    to="/discovery/dependencies"
                    className="group block p-6 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="bg-teal-500 p-3 rounded-lg text-white">
                        <Activity className="h-6 w-6" />
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
                    </div>
                    <h3 className="font-medium text-gray-900 group-hover:text-blue-600 mb-2">
                      Dependency Map
                    </h3>
                    <p className="text-sm text-gray-600">
                      Explore relationships and dependencies between assets
                    </p>
                  </Link>
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

export default DiscoveryDashboard; 