import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Filter, AlertCircle, RefreshCw, Download, TrendingUp, Layers, Wrench, Cloud, Archive, Package, CheckSquare, Square } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '../../services/api';
import { PlanningInitializationWizard } from '@/components/plan/PlanningInitializationWizard';
import type { Application as ApplicationType } from '@/lib/api/applicationsService';

interface Application {
  id: string;
  name: string;
  assetName?: string | null;  // Preserve original asset_name from API
  techStack: string;
  criticality: 'High' | 'Medium' | 'Low';
  department: string;
  sixRTreatment?: string;
  complexity: 'High' | 'Medium' | 'Low';
  cloudReadiness?: number;
  dependencies?: number;
}

interface SixRMetrics {
  rehost: number;
  replatform: number;
  refactor: number;
  rearchitect: number;
  repurchase: number;
  retire: number;
  total: number;
}

const SixRAnalysis: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const [filterDept, setFilterDept] = useState('All');
  const [filterCriticality, setFilterCriticality] = useState('All');

  // Application selection state for planning flow
  const [selectedAppIds, setSelectedAppIds] = useState<Set<string>>(new Set());
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  // Engagement ID - TODO: Get from context when available
  const engagement_id = 1;

  // Fetch applications from /api/v1/applications endpoint
  const { data: applications = [], isLoading, error, refetch } = useQuery<Application[]>({
    queryKey: ['sixr-applications', filterDept, filterCriticality],
    queryFn: async (): Promise<Application[]> => {
      const headers = getAuthHeaders();

      try {
        // Use the standard /api/v1/applications endpoint
        const response = await apiCall('/api/v1/applications?page=1&page_size=100', { headers });
        const apps = response.applications || [];

        // Transform the data to match our Application interface
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
        return apps.map((app: any) => ({
          id: app.id,
          name: app.application_name || app.asset_name || 'Unknown',
          assetName: app.asset_name,  // Preserve original asset_name for Planning Flow
          techStack: app.tech_stack || 'Unknown',
          criticality: app.criticality || 'Medium',
          department: app.department || 'IT', // Removed business_unit - doesn't exist in DB
          sixRTreatment: app.six_r_strategy || determineSixRStrategy(app),
          complexity: determineComplexity(app),
          cloudReadiness: app.complexity_score ? app.complexity_score * 100 : calculateCloudReadiness(app),
          dependencies: app.dependencies || 0
        }));
      } catch (error) {
        console.error('Failed to fetch applications:', error);
        // Return empty array instead of throwing to show empty state
        return [];
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false
  });

  // Helper function to determine 6R strategy based on application attributes
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
  const determineSixRStrategy = (app: any): string => {
    const techAge = app.tech_age || app.attributes?.tech_age;
    const complexity = app.complexity || app.attributes?.complexity;
    const cloudReady = app.cloud_readiness_score || app.attributes?.cloud_readiness;

    if (techAge === 'Legacy' || techAge === 'End-of-Life') {
      return 'Retire';
    } else if (cloudReady > 80) {
      return 'Rehost';
    } else if (cloudReady > 60) {
      return 'Replatform';
    } else if (complexity === 'High') {
      return 'Refactor';
    } else if (app.is_saas_available) {
      return 'Repurchase';
    } else {
      return 'Rearchitect';
    }
  };

  // Helper function to determine complexity
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
  const determineComplexity = (app: any): 'High' | 'Medium' | 'Low' => {
    const deps = app.dependency_count || app.relationships?.length || 0;
    if (deps > 10) return 'High';
    if (deps > 5) return 'Medium';
    return 'Low';
  };

  // Helper function to calculate cloud readiness
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
  const calculateCloudReadiness = (app: any): number => {
    // Simple heuristic based on available data
    let score = 50; // Base score

    if (app.containerized) score += 20;
    if (app.stateless) score += 15;
    if (app.uses_cloud_services) score += 15;
    if (app.tech_age === 'Modern') score += 10;
    if (app.tech_age === 'Legacy') score -= 20;

    return Math.min(100, Math.max(0, score));
  };

  // Filter applications based on selected filters
  const filteredApplications = applications.filter(app => {
    return (filterDept === 'All' || app.department === filterDept) &&
           (filterCriticality === 'All' || app.criticality === filterCriticality);
  });

  // Calculate 6R metrics
  const sixRMetrics: SixRMetrics = filteredApplications.reduce((acc, app) => {
    const treatment = app.sixRTreatment?.toLowerCase() || 'unknown';
    if (treatment.includes('rehost')) acc.rehost++;
    else if (treatment.includes('replatform')) acc.replatform++;
    else if (treatment.includes('refactor')) acc.refactor++;
    else if (treatment.includes('rearchitect')) acc.rearchitect++;
    else if (treatment.includes('repurchase')) acc.repurchase++;
    else if (treatment.includes('retire')) acc.retire++;
    acc.total++;
    return acc;
  }, {
    rehost: 0,
    replatform: 0,
    refactor: 0,
    rearchitect: 0,
    repurchase: 0,
    retire: 0,
    total: 0
  });

  const getTreatmentColor = (treatment: string): string => {
    const colors: Record<string, string> = {
      'Rehost': 'bg-blue-100 text-blue-800',
      'Replatform': 'bg-green-100 text-green-800',
      'Refactor': 'bg-yellow-100 text-yellow-800',
      'Rearchitect': 'bg-purple-100 text-purple-800',
      'Repurchase': 'bg-indigo-100 text-indigo-800',
      'Retire': 'bg-red-100 text-red-800'
    };
    return colors[treatment] || 'bg-gray-100 text-gray-800';
  };

  const getCriticalityColor = (criticality: string): string => {
    const colors: Record<string, string> = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return colors[criticality] || 'bg-gray-100 text-gray-800';
  };

  // Selection handlers
  const handleToggleSelection = (appId: string) => {
    setSelectedAppIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(appId)) {
        newSet.delete(appId);
      } else {
        newSet.add(appId);
      }
      return newSet;
    });
  };

  const handleToggleAllFiltered = () => {
    const allFilteredSelected = filteredApplications.every((app) =>
      selectedAppIds.has(app.id)
    );

    setSelectedAppIds((prev) => {
      const newSet = new Set(prev);
      if (allFilteredSelected) {
        // Deselect all filtered
        filteredApplications.forEach((app) => newSet.delete(app.id));
      } else {
        // Select all filtered
        filteredApplications.forEach((app) => newSet.add(app.id));
      }
      return newSet;
    });
  };

  const handleInitializePlanning = () => {
    if (selectedAppIds.size === 0) {
      return; // Button should be disabled, but just in case
    }
    setIsWizardOpen(true);
  };

  // Transform selected applications to match ApplicationType interface for wizard
  const selectedApplications: ApplicationType[] = filteredApplications
    .filter((app) => selectedAppIds.has(app.id))
    .map((app) => ({
      id: app.id,
      application_name: app.name,
      asset_name: app.assetName || null,  // Preserve asset_name from API response (no longer hardcoded to null)
      six_r_strategy: app.sixRTreatment || null,
      tech_stack: app.techStack,
      complexity_score: app.cloudReadiness || null,
      asset_type: null,
    }));

  const exportToCSV = () => {
    const csvHeaders = ['Application Name', 'Tech Stack', 'Criticality', 'Department', '6R Treatment', 'Complexity', 'Cloud Readiness'];
    const csvRows = filteredApplications.map(app => [
      app.name,
      app.techStack,
      app.criticality,
      app.department,
      app.sixRTreatment || 'Not Assigned',
      app.complexity,
      `${app.cloudReadiness || 0}%`
    ]);

    const csvContent = [csvHeaders.join(','), ...csvRows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `6r-analysis-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  // Get unique departments from applications
  const departments = Array.from(new Set(applications.map(app => app.department))).filter(Boolean);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <ContextBreadcrumbs />

            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">6R Analysis</h1>
              <p className="text-gray-600">Analyze and assign 6R migration strategies to your applications</p>
            </div>

            {/* 6R Strategy Distribution Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <Cloud className="h-5 w-5 text-blue-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.rehost}</span>
                </div>
                <p className="text-sm text-gray-600">Rehost</p>
                <p className="text-xs text-gray-500">Lift & Shift</p>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <Layers className="h-5 w-5 text-green-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.replatform}</span>
                </div>
                <p className="text-sm text-gray-600">Replatform</p>
                <p className="text-xs text-gray-500">Lift & Optimize</p>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <Wrench className="h-5 w-5 text-yellow-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.refactor}</span>
                </div>
                <p className="text-sm text-gray-600">Refactor</p>
                <p className="text-xs text-gray-500">Re-architect</p>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <TrendingUp className="h-5 w-5 text-purple-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.rearchitect}</span>
                </div>
                <p className="text-sm text-gray-600">Rearchitect</p>
                <p className="text-xs text-gray-500">Rebuild</p>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <Package className="h-5 w-5 text-indigo-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.repurchase}</span>
                </div>
                <p className="text-sm text-gray-600">Repurchase</p>
                <p className="text-xs text-gray-500">Replace</p>
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <Archive className="h-5 w-5 text-red-500" />
                  <span className="text-2xl font-bold text-gray-900">{sixRMetrics.retire}</span>
                </div>
                <p className="text-sm text-gray-600">Retire</p>
                <p className="text-xs text-gray-500">Decommission</p>
              </div>
            </div>

            {/* Applications Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Application Analysis</h2>
                    {selectedAppIds.size > 0 && (
                      <p className="text-sm text-blue-600 mt-1">
                        {selectedAppIds.size} application{selectedAppIds.size !== 1 ? 's' : ''} selected for planning
                      </p>
                    )}
                  </div>
                  <button
                    onClick={handleInitializePlanning}
                    disabled={selectedAppIds.size === 0}
                    className={`px-4 py-2 rounded-md font-medium flex items-center space-x-2 ${
                      selectedAppIds.size === 0
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-500 text-white hover:bg-blue-600'
                    }`}
                  >
                    <Package className="h-4 w-4" />
                    <span>Initialize Planning Flow</span>
                  </button>
                </div>
                <div className="flex justify-between items-center">
                  <button
                    onClick={handleToggleAllFiltered}
                    disabled={filteredApplications.length === 0}
                    className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400 flex items-center space-x-1"
                  >
                    {filteredApplications.length > 0 &&
                    filteredApplications.every((app) => selectedAppIds.has(app.id)) ? (
                      <>
                        <CheckSquare className="h-4 w-4" />
                        <span>Deselect All</span>
                      </>
                    ) : (
                      <>
                        <Square className="h-4 w-4" />
                        <span>Select All</span>
                      </>
                    )}
                  </button>
                  <div className="flex space-x-4">
                    <select
                      value={filterDept}
                      onChange={(e) => setFilterDept(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="All">All Departments</option>
                      {departments.map(dept => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                    <select
                      value={filterCriticality}
                      onChange={(e) => setFilterCriticality(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-2"
                    >
                      <option value="All">All Criticality</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                    <button
                      onClick={() => refetch()}
                      className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 flex items-center space-x-2"
                    >
                      <RefreshCw className="h-4 w-4" />
                      <span>Refresh</span>
                    </button>
                    <button
                      onClick={exportToCSV}
                      className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 flex items-center space-x-2"
                    >
                      <Download className="h-4 w-4" />
                      <span>Export CSV</span>
                    </button>
                  </div>
                </div>
              </div>

              {isLoading ? (
                <div className="p-8 text-center">
                  <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
                  <p className="text-gray-600">Loading applications...</p>
                </div>
              ) : error ? (
                <div className="p-8">
                  <div className="flex items-center justify-center text-red-600 mb-4">
                    <AlertCircle className="h-8 w-8 mr-2" />
                    <p className="text-lg font-semibold">Error loading applications</p>
                  </div>
                  <p className="text-gray-600 text-center">Please check your connection and try again.</p>
                </div>
              ) : filteredApplications.length === 0 ? (
                <div className="p-8 text-center">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No applications found for analysis</h3>
                  <p className="text-gray-600 mb-4">
                    {applications.length === 0
                      ? "Start by discovering applications in your environment using the Discovery workflow."
                      : "Adjust your filters to see available applications."}
                  </p>
                  {applications.length === 0 && (
                    <a
                      href="/discovery"
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Start Discovery
                    </a>
                  )}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                          Select
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Application
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tech Stack
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Criticality
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Department
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          6R Treatment
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Complexity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Cloud Readiness
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredApplications.map((app) => (
                        <tr key={app.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <button
                              onClick={() => handleToggleSelection(app.id)}
                              className="text-blue-600 hover:text-blue-800 focus:outline-none"
                            >
                              {selectedAppIds.has(app.id) ? (
                                <CheckSquare className="h-5 w-5" />
                              ) : (
                                <Square className="h-5 w-5" />
                              )}
                            </button>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{app.name}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-600">{app.techStack}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getCriticalityColor(app.criticality)}`}>
                              {app.criticality}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {app.department}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTreatmentColor(app.sixRTreatment || 'Not Assigned')}`}>
                              {app.sixRTreatment || 'Not Assigned'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getCriticalityColor(app.complexity)}`}>
                              {app.complexity}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${app.cloudReadiness || 0}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-600">{app.cloudReadiness || 0}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Summary Statistics */}
            {filteredApplications.length > 0 && (
              <div className="mt-6 bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Applications</p>
                    <p className="text-2xl font-bold text-gray-900">{filteredApplications.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Average Cloud Readiness</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Math.round(filteredApplications.reduce((acc, app) => acc + (app.cloudReadiness || 0), 0) / filteredApplications.length)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">High Complexity Apps</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {filteredApplications.filter(app => app.complexity === 'High').length}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Planning Initialization Wizard */}
      <PlanningInitializationWizard
        open={isWizardOpen}
        onOpenChange={setIsWizardOpen}
        engagement_id={engagement_id}
        preSelectedApplicationIds={Array.from(selectedAppIds)}
        preSelectedApplications={selectedApplications}
      />
    </div>
  );
};

export default SixRAnalysis;
