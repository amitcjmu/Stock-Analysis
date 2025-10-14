/**
 * Assessment Technical Debt Assessment Page
 *
 * This component provides technical debt assessment for the Assessment flow.
 * Migrated from Discovery flow per ADR-027 (v3.0.0).
 *
 * Shows:
 * - Technical debt items and severity
 * - Support status and EOL tracking
 * - Security risk assessment
 * - Migration effort and business impact
 * - Remediation recommendations
 */

import React, { useState } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { Shield, Info, AlertTriangle, Bug, Clock, TrendingUp, Code, Database, Globe, BarChart3, Settings, CheckCircle, X, RotateCcw, Play, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { useToast } from '../../components/ui/use-toast';

interface TechDebtItem {
  id: string;
  asset_id: string;
  asset_name: string;
  component: 'web' | 'app' | 'database' | 'os' | 'framework';
  technology: string;
  current_version: string;
  latest_version: string;
  support_status: 'supported' | 'extended' | 'deprecated' | 'end_of_life';
  end_of_life_date?: string;
  security_risk: 'low' | 'medium' | 'high' | 'critical';
  migration_effort: 'low' | 'medium' | 'high' | 'complex';
  business_impact: 'low' | 'medium' | 'high' | 'critical';
  recommended_action: string;
  dependencies: string[];
}

interface SupportTimeline {
  technology: string;
  current_version: string;
  support_end: string;
  extended_support_end?: string;
  replacement_options: string[];
}

const AssessmentTechDebtAssessment = (): JSX.Element => {
  const { toast } = useToast();

  // TODO: Replace with Assessment flow hooks when implemented
  // For now, this is a placeholder that matches the expected structure
  const isLoading = false;
  const error = null;
  const isTechDebtComplete = false;
  const currentPhase = 'tech_debt_assessment';

  // Local state for UI
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  // Placeholder data
  const techDebtItems: TechDebtItem[] = [];
  const supportTimelines: SupportTimeline[] = [];

  // Generate summary from tech debt items
  const summary = {
    total_items: techDebtItems.length,
    critical: techDebtItems.filter(item => item.security_risk === 'critical').length,
    high: techDebtItems.filter(item => item.security_risk === 'high').length,
    medium: techDebtItems.filter(item => item.security_risk === 'medium').length,
    low: techDebtItems.filter(item => item.security_risk === 'low').length,
    end_of_life: techDebtItems.filter(item => item.support_status === 'end_of_life').length,
    deprecated: techDebtItems.filter(item => item.support_status === 'deprecated').length
  };

  // Handle tech debt analysis execution
  const handleExecuteTechDebtAnalysis = async (): Promise<void> => {
    try {
      toast({
        title: 'Starting Analysis',
        description: 'Tech debt assessment is starting...',
      });
    } catch (err) {
      console.error('Failed to execute tech debt assessment:', err);
      toast({
        title: 'Error',
        description: 'Failed to start tech debt assessment. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Handle refresh
  const handleRefresh = async (): Promise<void> => {
    try {
      toast({
        title: 'Refreshing',
        description: 'Tech debt assessment data is being refreshed...',
      });
    } catch (err) {
      console.error('Failed to refresh tech debt data:', err);
      toast({
        title: 'Error',
        description: 'Failed to refresh data. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Filter tech debt items based on selected filters
  const filteredTechDebtItems = techDebtItems.filter(item => {
    const matchesCategory = selectedCategory === 'all' || item.component === selectedCategory;
    const matchesRisk = selectedRisk === 'all' || item.security_risk === selectedRisk;
    return matchesCategory && matchesRisk;
  });

  const getComponentIcon = (component: string): JSX.Element => {
    switch (component) {
      case 'web': return <Globe className="h-5 w-5" />;
      case 'app': return <Code className="h-5 w-5" />;
      case 'database': return <Database className="h-5 w-5" />;
      case 'os': return <Settings className="h-5 w-5" />;
      case 'framework': return <BarChart3 className="h-5 w-5" />;
      default: return <Code className="h-5 w-5" />;
    }
  };

  const getSupportStatusColor = (status: string): string => {
    switch (status) {
      case 'supported': return 'text-green-600 bg-green-100';
      case 'extended': return 'text-yellow-600 bg-yellow-100';
      case 'deprecated': return 'text-orange-600 bg-orange-100';
      case 'end_of_life': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (risk: string): string => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskIcon = (risk: string): JSX.Element => {
    switch (risk) {
      case 'low': return <CheckCircle className="h-4 w-4" />;
      case 'medium': return <Info className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      case 'critical': return <X className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const calculateDaysUntilEOL = (eolDate: string): number | null => {
    if (!eolDate) return null;
    const today = new Date();
    const eol = new Date(eolDate);
    const diffTime = eol.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (isLoading) {
    return (
      <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900">
            <div className="container mx-auto px-6 py-8 text-center">
              <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Loading Tech Debt Assessment...</h1>
              <p className="text-lg mt-2 text-gray-600 dark:text-gray-300">Please wait while our agents analyze the data.</p>
              <div className="mt-8">
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mx-auto"></div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900">
          <div className="container mx-auto px-6 py-8">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>

            <div className="flex justify-between items-center mb-6">
              <div>
                <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Technical Debt Assessment</h1>
                <Badge variant="outline" className="mt-2">
                  Assessment Flow
                </Badge>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isLoading}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                {!isTechDebtComplete && (
                  <Button
                    onClick={handleExecuteTechDebtAnalysis}
                  >
                    <Play className="mr-2 h-4 w-4" />
                    Start Assessment
                  </Button>
                )}
              </div>
            </div>

            {/* Placeholder Info */}
            <Card className="mb-6 border-blue-200 bg-blue-50">
              <CardContent className="pt-6">
                <div className="flex items-start">
                  <Info className="mr-2 h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-blue-900 font-medium">Assessment Phase Integration In Progress</p>
                    <p className="text-blue-700 text-sm mt-1">
                      This technical debt assessment page is part of the Assessment flow. Integration with
                      Assessment flow hooks and backend services is currently being completed. The page
                      structure follows the Discovery pattern and will be fully functional once the
                      Assessment flow backend services are connected.
                    </p>
                    <p className="text-blue-700 text-sm mt-2">
                      <strong>Note:</strong> Per ADR-027, tech debt assessment was migrated from Discovery
                      to Assessment flow in v3.0.0.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <Bug className="h-8 w-8 text-blue-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">Total Debt Items</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{summary.total_items}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <AlertTriangle className="h-8 w-8 text-red-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">Critical/High Risk</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{summary.critical + summary.high}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <Clock className="h-8 w-8 text-orange-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">End of Life / Deprecated</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{summary.end_of_life + summary.deprecated}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">Overall Health Score</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">
                      {summary.total_items > 0 ? (100 - ((summary.critical + summary.high) / summary.total_items) * 100).toFixed(0) : '100'}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Debt Details</h2>
                <div className="flex space-x-4">
                  <select
                    value={selectedCategory}
                    onChange={e => setSelectedCategory(e.target.value)}
                    className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-md p-2"
                  >
                    <option value="all">All Categories</option>
                    <option value="os">OS</option>
                    <option value="database">Database</option>
                    <option value="framework">Framework</option>
                    <option value="app">Application</option>
                    <option value="web">Web Server</option>
                  </select>
                  <select
                    value={selectedRisk}
                    onChange={e => setSelectedRisk(e.target.value)}
                    className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-md p-2"
                  >
                    <option value="all">All Risks</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto">
                {filteredTechDebtItems.length > 0 ? (
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Asset</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Technology</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Versions</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Support Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Security Risk</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Recommended Action</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {filteredTechDebtItems.map(item => {
                        const daysUntilEOL = calculateDaysUntilEOL(item.end_of_life_date || '');
                        return (
                          <tr key={item.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                {getComponentIcon(item.component)}
                                <span className="ml-2 font-medium text-gray-900 dark:text-white">{item.asset_name}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{item.technology}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <span className="text-gray-900 dark:text-white">{item.current_version}</span>
                              <span className="text-gray-500 dark:text-gray-400"> → {item.latest_version}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getSupportStatusColor(item.support_status)}`}>
                                {item.support_status.replace('_', ' ').toUpperCase()}
                              </span>
                              {daysUntilEOL !== null && (
                                <p className={`text-xs mt-1 ${daysUntilEOL < 30 ? 'text-red-500' : 'text-gray-500'}`}>
                                  {daysUntilEOL > 0
                                    ? `${daysUntilEOL} days left`
                                    : daysUntilEOL === 0
                                    ? 'EOL today'
                                    : `EOL ${-daysUntilEOL} days ago`}
                                </p>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                {getRiskIcon(item.security_risk)}
                                <span className={`ml-2 px-2 py-1 text-xs rounded ${getRiskColor(item.security_risk)}`}>
                                  {item.security_risk.toUpperCase()}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{item.recommended_action}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No technical debt items found. Start assessment to analyze assets.
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">Support Timelines</h2>
                <div className="space-y-4">
                  {supportTimelines.length > 0 ? (
                    supportTimelines.map((timeline, index) => (
                      <div key={index} className="border-l-4 border-blue-500 pl-4">
                        <p className="font-bold text-gray-900 dark:text-white">{timeline.technology}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Support Ends: {timeline.support_end}</p>
                        {timeline.extended_support_end && (
                          <p className="text-sm text-yellow-600 dark:text-yellow-400">Extended Support Ends: {timeline.extended_support_end}</p>
                        )}
                        <p className="text-sm text-gray-500 dark:text-gray-300">Replacements: {timeline.replacement_options.join(', ')}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500">No support timeline data available yet.</p>
                  )}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">
                  Agent Insights
                  <button
                    onClick={() => setAgentRefreshTrigger(prev => prev + 1)}
                    className="ml-4 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
                    title="Refresh Agent Analysis"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </h2>
                <AgentInsightsSection
                  context="tech_debt_assessment"
                  refreshTrigger={agentRefreshTrigger}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AssessmentTechDebtAssessment;
