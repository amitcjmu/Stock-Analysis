import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { 
  AlertTriangle, Bug, Shield, Clock, TrendingUp,
  Code, Database, Globe, BarChart3, Settings,
  CheckCircle, X, Info, GraduationCap, RotateCcw
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';
import { useAppContext } from '../../hooks/useContext';

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
  const { client_account_id, engagement_id } = useAppContext();
  const [techDebtItems, setTechDebtItems] = useState<TechDebtItem[]>([]);
  const [supportTimelines, setSupportTimelines] = useState<SupportTimeline[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState({
    totalItems: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    endOfLife: 0,
    deprecated: 0
  });
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);

  useEffect(() => {
    if (client_account_id && engagement_id) {
      fetchTechDebtAnalysis();
      fetchSupportTimelines();
    }
  }, [client_account_id, engagement_id]);

  // Trigger initial agent panel refresh on component mount
  useEffect(() => {
    const timer = setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  const fetchTechDebtAnalysis = async () => {
    if (!client_account_id || !engagement_id) {
      console.warn("Client or engagement not selected, skipping tech debt analysis fetch.");
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.TECH_DEBT_ANALYSIS, {
        method: 'POST',
        body: JSON.stringify({
          client_account_id: client_account_id,
          engagement_id: engagement_id,
        })
      });
      
      // Filter out items with unknown/invalid data
      const validItems = (response.items || []).filter((item: TechDebtItem) => {
        // Only include items with valid technology names and versions
        const hasValidTechnology = item.technology && 
          item.technology !== 'unknown' && 
          item.technology !== 'Unknown' &&
          !item.technology.toLowerCase().includes('unknown');
          
        const hasValidVersion = item.currentVersion && 
          item.currentVersion !== 'unknown' && 
          item.currentVersion !== 'Unknown' &&
          !item.currentVersion.toLowerCase().includes('unknown');
          
        const hasValidEOLDate = !item.endOfLifeDate || 
          (item.endOfLifeDate && 
           item.endOfLifeDate !== 'unknown' && 
           !isNaN(Date.parse(item.endOfLifeDate)));
           
        return hasValidTechnology && hasValidVersion && hasValidEOLDate;
      });
      
      setTechDebtItems(validItems);
      
      // Update summary to reflect filtered items
      const filteredSummary = {
        totalItems: validItems.length,
        critical: validItems.filter(item => item.securityRisk === 'critical').length,
        high: validItems.filter(item => item.securityRisk === 'high').length,
        medium: validItems.filter(item => item.securityRisk === 'medium').length,
        low: validItems.filter(item => item.securityRisk === 'low').length,
        endOfLife: validItems.filter(item => item.supportStatus === 'end_of_life').length,
        deprecated: validItems.filter(item => item.supportStatus === 'deprecated').length
      };
      
      setSummary(filteredSummary);
      
      // Trigger agent analysis for tech debt context
      if (validItems.length > 0) {
        await triggerAgentAnalysis(validItems);
      }
    } catch (error) {
      console.error('Failed to fetch tech debt analysis:', error);
      // Set demo data with valid items only
      const demoItems: TechDebtItem[] = [
        {
          id: 'tech-debt-1',
          assetId: 'asset-001',
          assetName: 'web-server-01',
          component: 'os',
          technology: 'Windows Server',
          currentVersion: '2016',
          latestVersion: '2022',
          supportStatus: 'deprecated',
          endOfLifeDate: '2025-12-31',
          securityRisk: 'high',
          migrationEffort: 'medium',
          businessImpact: 'high',
          recommendedAction: 'Upgrade to Windows Server 2022 before end of support',
          dependencies: ['IIS', 'SQL Server']
        },
        {
          id: 'tech-debt-2',
          assetId: 'asset-002',
          assetName: 'app-server-01',
          component: 'framework',
          technology: 'Node.js',
          currentVersion: '14.x',
          latestVersion: '20.x',
          supportStatus: 'deprecated',
          endOfLifeDate: '2025-04-30',
          securityRisk: 'medium',
          migrationEffort: 'low',
          businessImpact: 'medium',
          recommendedAction: 'Upgrade to Node.js 20.x for continued security updates',
          dependencies: ['Express.js', 'MongoDB']
        }
      ];
      
      setTechDebtItems(demoItems);
      setSummary({
        totalItems: 2,
        critical: 0,
        high: 1,
        medium: 1,
        low: 0,
        endOfLife: 0,
        deprecated: 2
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger agent analysis for tech debt context
  const triggerAgentAnalysis = async (techDebtData: TechDebtItem[]) => {
    try {
      console.log('Triggering agent analysis for tech-debt context');
      
      // Prepare data for agent analysis
      const agentAnalysisRequest = {
        data_source: {
          file_data: techDebtData.slice(0, 20), // Send sample of tech debt items
          columns: techDebtData.length > 0 ? Object.keys(techDebtData[0]) : [],
          sample_data: techDebtData.slice(0, 10),
          metadata: {
            source: "tech-debt-analysis-page",
            file_name: "tech_debt_analysis.csv",
            total_records: techDebtData.length,
            context: "tech_debt_analysis",
            mapping_context: "tech-debt"
          }
        },
        analysis_type: "data_source_analysis",
        page_context: "tech-debt"
      };

      // Trigger agent analysis
      const agentResponse = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS, {
        method: 'POST',
        body: JSON.stringify(agentAnalysisRequest)
      });

      if (agentResponse) {
        console.log('✅ Agent analysis completed for tech-debt context');
        setAgentRefreshTrigger(prev => prev + 1);
      }
      
    } catch (error) {
      console.error('Failed to trigger agent analysis for tech debt:', error);
    }
  };

  const fetchSupportTimelines = async () => {
    try {
      // For now, use demo data since support-timelines endpoint doesn't exist yet
      const demoTimelines: SupportTimeline[] = [
        {
          technology: 'Windows Server 2016',
          currentVersion: '2016',
          supportEnd: '2025-12-31',
          extendedSupportEnd: '2027-12-31',
          replacementOptions: ['Windows Server 2022', 'Azure Virtual Machines']
        },
        {
          technology: 'Node.js 14.x',
          currentVersion: '14.21.3',
          supportEnd: '2025-04-30',
          replacementOptions: ['Node.js 20.x', 'Node.js 18.x']
        }
      ];
      
      setSupportTimelines(demoTimelines);
    } catch (error) {
      console.error('Failed to fetch support timelines:', error);
      setSupportTimelines([]);
    }
  };

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

  const filteredItems = techDebtItems.filter(item => {
    const categoryMatch = selectedCategory === 'all' || item.component === selectedCategory;
    const riskMatch = selectedRisk === 'all' || item.securityRisk === selectedRisk;
    return categoryMatch && riskMatch;
  });

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
                    {filteredItems.map(item => {
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