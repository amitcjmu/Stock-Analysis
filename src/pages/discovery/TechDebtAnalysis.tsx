import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { 
  AlertTriangle, Bug, Shield, Clock, TrendingUp,
  Code, Database, Globe, BarChart3, Settings,
  CheckCircle, X, Info, GraduationCap, RotateCcw, Play, RefreshCw
} from 'lucide-react';
import { useDiscoveryFlowV2 } from '../../hooks/discovery/useDiscoveryFlowV2';
import { useTechDebtFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { useToast } from '../../components/ui/use-toast';

interface TechDebtItem {
  id: string;
  assetId: string;
  assetName: string;
  component: 'web' | 'app' | 'database' | 'os' | 'framework';
  technology: string;
  currentVersion: string;
  latestVersion: string;
  supportStatus: 'supported' | 'extended' | 'deprecated' | 'end_of_life';
  endOfLifeDate?: string;
  securityRisk: 'low' | 'medium' | 'high' | 'critical';
  migrationEffort: 'low' | 'medium' | 'high' | 'complex';
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  recommendedAction: string;
  dependencies: string[];
}

interface SupportTimeline {
  technology: string;
  currentVersion: string;
  supportEnd: string;
  extendedSupportEnd?: string;
  replacementOptions: string[];
}

const TechDebtAnalysis = () => {
  const { client, engagement } = useAuth();
  const { toast } = useToast();
  
  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useTechDebtFlowDetection();
  
  // V2 Discovery flow hook - pass effectiveFlowId instead of urlFlowId
  const {
    flow,
    isLoading,
    error,
    updatePhase,
    isUpdating,
    progressPercentage,
    currentPhase,
    completedPhases,
    nextPhase
  } = useDiscoveryFlowV2(effectiveFlowId);

  // Debug info for flow detection
  console.log('🔍 TechDebt flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

  // Get tech debt specific data from V2 flow - extract from flow state
  const techDebtResults = flow?.results?.tech_debt || flow?.tech_debt_analysis || flow?.results?.tech_debt_analysis || {};
  const isTechDebtComplete = completedPhases.includes('tech_debt') || completedPhases.includes('tech_debt_completed');
  
  // Local state for UI
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  // Extract tech debt data from flow results
  const techDebtItems = techDebtResults?.items || techDebtResults?.debt_items || techDebtResults?.debt_scores ? 
    Object.entries(techDebtResults.debt_scores || {}).map(([key, value]: [string, any], index) => ({
      id: `debt_${index}`,
      assetId: key,
      assetName: value?.asset_name || key,
      component: value?.component || 'app',
      technology: value?.technology || 'Unknown',
      currentVersion: value?.current_version || 'Unknown',
      latestVersion: value?.latest_version || 'Unknown',
      supportStatus: value?.support_status || 'unknown',
      endOfLifeDate: value?.end_of_life_date,
      securityRisk: value?.security_risk || 'medium',
      migrationEffort: value?.migration_effort || 'medium',
      businessImpact: value?.business_impact || 'medium',
      recommendedAction: value?.recommended_action || 'Review and assess',
      dependencies: value?.dependencies || []
    })) : [];

  const supportTimelines = techDebtResults?.support_timelines || [];
  
  // Generate summary from tech debt items
  const summary = {
    totalItems: techDebtItems.length,
    critical: techDebtItems.filter(item => item.securityRisk === 'critical').length,
    high: techDebtItems.filter(item => item.securityRisk === 'high').length,
    medium: techDebtItems.filter(item => item.securityRisk === 'medium').length,
    low: techDebtItems.filter(item => item.securityRisk === 'low').length,
    endOfLife: techDebtItems.filter(item => item.supportStatus === 'end_of_life').length,
    deprecated: techDebtItems.filter(item => item.supportStatus === 'deprecated').length
  };

  // Handle tech debt analysis execution
  const handleExecuteTechDebtAnalysis = async () => {
    try {
      await updatePhase('tech_debt', { action: 'start_analysis' });
      toast({
        title: 'Success',
        description: 'Tech debt analysis started.',
      });
    } catch (err) {
      console.error('Failed to execute tech debt analysis phase:', err);
      toast({
        title: 'Error',
        description: 'Failed to start tech debt analysis. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    try {
      // Refresh by re-fetching flow data
      await updatePhase(currentPhase, { action: 'refresh' });
      toast({
        title: 'Success',
        description: 'Tech debt analysis data refreshed.',
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

  // Trigger initial agent panel refresh on component mount
  useEffect(() => {
    const timer = setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  // Filter tech debt items based on selected filters
  const filteredTechDebtItems = techDebtItems.filter(item => {
    const matchesCategory = selectedCategory === 'all' || item.component === selectedCategory;
    const matchesRisk = selectedRisk === 'all' || item.securityRisk === selectedRisk;
    return matchesCategory && matchesRisk;
  });

  const getComponentIcon = (component: string) => {
    switch (component) {
      case 'web': return <Globe className="h-5 w-5" />;
      case 'app': return <Code className="h-5 w-5" />;
      case 'database': return <Database className="h-5 w-5" />;
      case 'os': return <Settings className="h-5 w-5" />;
      case 'framework': return <BarChart3 className="h-5 w-5" />;
      default: return <Code className="h-5 w-5" />;
    }
  };

  const getSupportStatusColor = (status: string) => {
    switch (status) {
      case 'supported': return 'text-green-600 bg-green-100';
      case 'extended': return 'text-yellow-600 bg-yellow-100';
      case 'deprecated': return 'text-orange-600 bg-orange-100';
      case 'end_of_life': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'low': return <CheckCircle className="h-4 w-4" />;
      case 'medium': return <Info className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      case 'critical': return <X className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const calculateDaysUntilEOL = (eolDate: string) => {
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
              <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Loading Tech Debt Analysis...</h1>
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
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Technical Debt Analysis</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <Bug className="h-8 w-8 text-blue-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">Total Debt Items</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{summary.totalItems}</p>
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
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{summary.endOfLife + summary.deprecated}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-lg text-gray-600 dark:text-gray-400">Overall Health Score</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">
                      {summary.totalItems > 0 ? (100 - ((summary.critical + summary.high) / summary.totalItems) * 100).toFixed(0) : '100'}%
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
                      const daysUntilEOL = calculateDaysUntilEOL(item.endOfLifeDate);
                      return (
                        <tr key={item.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getComponentIcon(item.component)}
                              <span className="ml-2 font-medium text-gray-900 dark:text-white">{item.assetName}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{item.technology}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className="text-gray-900 dark:text-white">{item.currentVersion}</span>
                            <span className="text-gray-500 dark:text-gray-400"> → {item.latestVersion}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getSupportStatusColor(item.supportStatus)}`}>
                              {item.supportStatus.replace('_', ' ').toUpperCase()}
                            </span>
                            {daysUntilEOL !== null && (
                              <p className={`text-xs mt-1 ${daysUntilEOL < 30 ? 'text-red-500' : 'text-gray-500'}`}>
                                {daysUntilEOL > 0 ? `${daysUntilEOL} days left` : `EOL ${-daysUntilEOL} days ago`}
                              </p>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getRiskIcon(item.securityRisk)}
                              <span className={`ml-2 ${getRiskColor(item.securityRisk)}`}>{item.securityRisk.toUpperCase()}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{item.recommendedAction}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">Support Timelines</h2>
                <div className="space-y-4">
                  {supportTimelines.map((timeline, index) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-4">
                      <p className="font-bold text-gray-900 dark:text-white">{timeline.technology}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Support Ends: {timeline.supportEnd}</p>
                      {timeline.extendedSupportEnd && (
                        <p className="text-sm text-yellow-600 dark:text-yellow-400">Extended Support Ends: {timeline.extendedSupportEnd}</p>
                      )}
                      <p className="text-sm text-gray-500 dark:text-gray-300">Replacements: {timeline.replacementOptions.join(', ')}</p>
                    </div>
                  ))}
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
                  context="tech_debt_analysis" 
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

export default TechDebtAnalysis; 