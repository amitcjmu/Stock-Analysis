import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import { 
  AlertTriangle, Bug, Shield, Clock, TrendingUp,
  Code, Database, Globe, Timeline, BarChart3, Settings,
  CheckCircle, X, Info, GraduationCap, RotateCcw
} from 'lucide-react';
import { apiCall, API_CONFIG } from '../../config/api';

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
    fetchTechDebtAnalysis();
    fetchSupportTimelines();
  }, []);

  // Trigger initial agent panel refresh on component mount
  useEffect(() => {
    const timer = setTimeout(() => {
      setAgentRefreshTrigger(prev => prev + 1);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  const fetchTechDebtAnalysis = async () => {
    try {
      setIsLoading(true);
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/tech-debt-analysis`);
      
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
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/support-timelines`);
      
      // Filter out timelines with unknown/invalid data
      const validTimelines = (response.timelines || []).filter((timeline: SupportTimeline) => {
        const hasValidTechnology = timeline.technology && 
          timeline.technology !== 'unknown' && 
          timeline.technology !== 'Unknown' &&
          !timeline.technology.toLowerCase().includes('unknown');
          
        const hasValidVersion = timeline.currentVersion && 
          timeline.currentVersion !== 'unknown' && 
          timeline.currentVersion !== 'Unknown' &&
          !timeline.currentVersion.toLowerCase().includes('unknown');
          
        const hasValidSupportEnd = timeline.supportEnd && 
          timeline.supportEnd !== 'unknown' && 
          !isNaN(Date.parse(timeline.supportEnd));
          
        return hasValidTechnology && hasValidVersion && hasValidSupportEnd;
      });
      
      setSupportTimelines(validTimelines);
    } catch (error) {
      console.error('Failed to fetch support timelines:', error);
      // Set demo data with valid timelines only
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

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <div className="flex h-full">
          {/* Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            <main className="p-8">
              <div className="max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Technical Debt Analysis</h1>
              <p className="text-lg text-gray-600">
                Comprehensive analysis of technology stack support status and modernization opportunities
              </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{summary.totalItems}</h3>
                    <p className="text-xs text-gray-600">Total Items</p>
                  </div>
                  <BarChart3 className="h-6 w-6 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-red-600">{summary.critical}</h3>
                    <p className="text-xs text-gray-600">Critical Risk</p>
                  </div>
                  <X className="h-6 w-6 text-red-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-orange-600">{summary.high}</h3>
                    <p className="text-xs text-gray-600">High Risk</p>
                  </div>
                  <AlertTriangle className="h-6 w-6 text-orange-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-yellow-600">{summary.medium}</h3>
                    <p className="text-xs text-gray-600">Medium Risk</p>
                  </div>
                  <Info className="h-6 w-6 text-yellow-500" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-red-800">{summary.endOfLife}</h3>
                    <p className="text-xs text-gray-600">End of Life</p>
                  </div>
                  <Clock className="h-6 w-6 text-red-800" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-orange-800">{summary.deprecated}</h3>
                    <p className="text-xs text-gray-600">Deprecated</p>
                  </div>
                  <Bug className="h-6 w-6 text-orange-800" />
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <div className="flex space-x-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Component Type</label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Components</option>
                    <option value="web">Web Tier</option>
                    <option value="app">Application Tier</option>
                    <option value="database">Database Tier</option>
                    <option value="os">Operating System</option>
                    <option value="framework">Frameworks</option>
                  </select>
                </div>
                
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Risk Level</label>
                  <select
                    value={selectedRisk}
                    onChange={(e) => setSelectedRisk(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Support Timeline */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Support Timeline</h2>
              <div className="space-y-4">
                {supportTimelines.map((timeline, index) => {
                  const daysUntilEOL = calculateDaysUntilEOL(timeline.supportEnd);
                  const isUrgent = daysUntilEOL < 365;
                  
                  return (
                    <div key={index} className={`border rounded-lg p-4 ${isUrgent ? 'border-red-300 bg-red-50' : 'border-gray-300'}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{timeline.technology}</h3>
                          <p className="text-sm text-gray-600">Version {timeline.currentVersion}</p>
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-medium ${isUrgent ? 'text-red-600' : 'text-gray-600'}`}>
                            {daysUntilEOL > 0 ? `${daysUntilEOL} days until EOL` : 'Already EOL'}
                          </div>
                          <div className="text-xs text-gray-500">{timeline.supportEnd}</div>
                        </div>
                      </div>
                      
                      {timeline.replacementOptions.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-700">Replacement Options:</p>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {timeline.replacementOptions.map((option, idx) => (
                              <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                                {option}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tech Debt Items */}
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Technical Debt Items</h2>
                
                {filteredItems.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Technical Debt Found</h3>
                    <p className="text-gray-600">Your technology stack is up to date!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredItems.map((item) => (
                      <div key={item.id} className="border border-gray-200 rounded-lg p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-lg bg-gray-100">
                              {getComponentIcon(item.component)}
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-900">{item.assetName}</h3>
                              <p className="text-sm text-gray-600">{item.technology} {item.currentVersion}</p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <div className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${getSupportStatusColor(item.supportStatus)}`}>
                              <span>{item.supportStatus.replace('_', ' ')}</span>
                            </div>
                            <div className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${getRiskColor(item.securityRisk)}`}>
                              {getRiskIcon(item.securityRisk)}
                              <span>{item.securityRisk} risk</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div>
                            <label className="text-sm font-medium text-gray-700">Current Version</label>
                            <div className="mt-1 p-2 bg-gray-50 border border-gray-200 rounded">
                              <span className="text-gray-800">{item.currentVersion}</span>
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium text-gray-700">Latest Version</label>
                            <div className="mt-1 p-2 bg-green-50 border border-green-200 rounded">
                              <span className="text-green-800">{item.latestVersion}</span>
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium text-gray-700">Migration Effort</label>
                            <div className="mt-1 p-2 bg-blue-50 border border-blue-200 rounded">
                              <span className="text-blue-800">{item.migrationEffort}</span>
                            </div>
                          </div>
                        </div>
                        
                        {item.endOfLifeDate && (
                          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <Clock className="h-4 w-4 text-red-600" />
                              <span className="text-sm font-medium text-red-800">
                                End of Life: {item.endOfLifeDate} ({calculateDaysUntilEOL(item.endOfLifeDate)} days)
                              </span>
                            </div>
                          </div>
                        )}
                        
                        <div className="mb-4">
                          <label className="text-sm font-medium text-gray-700">Recommended Action</label>
                          <div className="mt-1 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-sm text-blue-800">{item.recommendedAction}</p>
                          </div>
                        </div>
                        
                        {item.dependencies.length > 0 && (
                          <div>
                            <label className="text-sm font-medium text-gray-700">Dependencies</label>
                            <div className="mt-1 flex flex-wrap gap-2">
                              {item.dependencies.map((dep, idx) => (
                                <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                  {dep}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
              </div>
            </main>
          </div>

          {/* Agent Interaction Sidebar */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Agent Clarification Panel */}
              <AgentClarificationPanel 
                pageContext="tech-debt"
                refreshTrigger={agentRefreshTrigger}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Tech debt question answered:', questionId, response);
                  // Refresh tech debt analysis after agent learning
                  fetchTechDebtAnalysis();
                }}
              />

              {/* Data Classification Display */}
              <DataClassificationDisplay 
                pageContext="tech-debt"
                refreshTrigger={agentRefreshTrigger}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Tech debt classification updated:', itemId, newClassification);
                }}
              />

              {/* Agent Insights Section */}
              <AgentInsightsSection 
                pageContext="tech-debt"
                refreshTrigger={agentRefreshTrigger}
                onInsightAction={(insightId, action) => {
                  console.log('Tech debt insight action:', insightId, action);
                  if (action === 'apply_insight') {
                    // Apply tech debt recommendations
                    console.log('Applying tech debt insights');
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TechDebtAnalysis; 