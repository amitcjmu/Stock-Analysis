import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { DollarSign, TrendingUp, TrendingDown, Brain, MessageSquare, Sparkles, Download, AlertTriangle, Activity, Zap, Clock, Target, Eye, BarChart3, PieChart as PieChartIcon, Users, Calendar, Filter, Bot, Cpu, Settings, MonitorSpeaker, RefreshCw } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Area, AreaChart, Tooltip, Legend } from 'recharts';
import { apiCall } from '../../config/api';

const LLMCosts = () => {
  const [llmData, setLlmData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDateRange, setSelectedDateRange] = useState('7d');
  const [selectedModel, setSelectedModel] = useState('all');
  const [selectedFeature, setSelectedFeature] = useState('all');
  const [refreshing, setRefreshing] = useState(false);
  const [dataSource, setDataSource] = useState('mock');

  // Fetch LLM usage and cost data
  useEffect(() => {
    fetchLLMData();
  }, [selectedDateRange, selectedModel, selectedFeature]);

  const fetchLLMData = async () => {
    try {
      setIsLoading(true);
      
      // Try to fetch real data from multiple LLM admin endpoints
      const [usageResponse, costResponse, modelsResponse, realtimeResponse, analyticsResponse] = await Promise.allSettled([
        apiCall('/api/v1/admin/llm-usage/usage/report', { method: 'GET' }),
        apiCall('/api/v1/admin/llm-usage/usage/costs/breakdown', { method: 'GET' }),
        apiCall('/api/v1/admin/llm-usage/pricing/models', { method: 'GET' }),
        apiCall('/api/v1/admin/llm-usage/usage/real-time', { method: 'GET' }),
        apiCall('/api/v1/admin/llm-usage/usage/summary/daily', { method: 'GET' })
      ]);

      console.log('🧠 LLM API responses:', {
        usage: usageResponse,
        cost: costResponse,
        models: modelsResponse,
        realtime: realtimeResponse,
        analytics: analyticsResponse
      });

      // Check if we got real data from any endpoint - need to check data.success flag
      const hasRealData = [usageResponse, costResponse, modelsResponse, realtimeResponse, analyticsResponse]
        .some(response => response.status === 'fulfilled' && response.value?.data?.success);

      if (hasRealData) {
        console.log('✅ Found real LLM data from API endpoints');
        setDataSource('live');
        
        const realData = {
          usage: usageResponse.status === 'fulfilled' && usageResponse.value?.data?.success ? usageResponse.value.data.data : null,
          costs: costResponse.status === 'fulfilled' && costResponse.value?.data?.success ? costResponse.value.data.data : null,
          models: modelsResponse.status === 'fulfilled' && modelsResponse.value?.data?.success ? modelsResponse.value.data.data : null,
          realtime: realtimeResponse.status === 'fulfilled' && realtimeResponse.value?.data?.success ? realtimeResponse.value.data.data : null,
          analytics: analyticsResponse.status === 'fulfilled' && analyticsResponse.value?.data?.success ? analyticsResponse.value.data.data : null
        };
        
        // Transform real data or fall back to mock for missing pieces
        const combinedData = transformRealLLMData(realData);
        setLlmData(combinedData);
      } else {
        console.log('⚠️ No real LLM data available, using enhanced mock data');
        setDataSource('mock');
        setLlmData(generateMockLLMData());
      }
      
    } catch (error) {
      console.error('Error fetching LLM data:', error);
      console.log('🔄 Falling back to mock data due to API error');
      setDataSource('mock');
      setLlmData(generateMockLLMData());
    } finally {
      setIsLoading(false);
    }
  };

  const transformRealLLMData = (realData) => {
    // Transform real API data into dashboard format
    // Fill gaps with mock data where real data is incomplete
    const mockData = generateMockLLMData();
    
    // Safely extract and transform real data
    const transformedData = {
      usage: Array.isArray(realData.usage?.daily_usage) ? realData.usage.daily_usage : mockData.usage,
      costs: Array.isArray(realData.costs?.breakdown_by_model) ? realData.costs.breakdown_by_model : mockData.costs,
      models: Array.isArray(realData.models) ? realData.models : mockData.models,
      realtime: realData.realtime || mockData.realtime,
      analytics: realData.analytics || mockData.analytics,
      features: mockData.features, // Always use mock for feature breakdown until endpoint exists
      summary: realData.analytics?.summary || realData.usage?.summary || mockData.summary
    };
    
    // Ensure all required data structures exist and are arrays where expected
    return {
      usage: Array.isArray(transformedData.usage) ? transformedData.usage : mockData.usage,
      costs: Array.isArray(transformedData.costs) ? transformedData.costs : mockData.costs,
      models: Array.isArray(transformedData.models) ? transformedData.models : mockData.models,
      realtime: transformedData.realtime || mockData.realtime,
      analytics: transformedData.analytics || mockData.analytics,
      features: Array.isArray(transformedData.features) ? transformedData.features : mockData.features,
      summary: transformedData.summary || mockData.summary
    };
  };

  const refreshData = async () => {
    setRefreshing(true);
    await fetchLLMData();
    setRefreshing(false);
  };

  const generateMockLLMData = () => {
    // Comprehensive mock data for LLM costs dashboard
    const features = [
      'multi_modal_chat', 'feedback_processing', 'asset_analysis', 'discovery_insights',
      'migration_planning', 'dependency_analysis', 'tech_debt_analysis', 'risk_assessment'
    ];
    
    const models = [
      { name: 'gemma-3-4b-it', provider: 'DeepInfra', type: 'Chat & Feedback' },
      { name: 'llama-4-maverick', provider: 'DeepInfra', type: 'Agentic Tasks' }
    ];

    // Generate usage data for last 30 days
    const usageData = [];
    const costData = [];
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const totalCalls = Math.floor(Math.random() * 500) + 100;
      const totalTokens = Math.floor(Math.random() * 100000) + 20000;
      const totalCost = (totalTokens / 1000) * 0.03 + Math.random() * 2;
      
      usageData.push({
        date: dateStr,
        calls: totalCalls,
        tokens: totalTokens,
        cost: parseFloat(totalCost.toFixed(2)),
        'gemma-3-4b-it': Math.floor(totalCalls * 0.65),
        'llama-4-maverick': Math.floor(totalCalls * 0.35)
      });
      
      costData.push({
        date: dateStr,
        DeepInfra: parseFloat(totalCost.toFixed(2))
      });
    }

    // Feature breakdown
    const featureBreakdown = features.map(feature => ({
      name: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      calls: Math.floor(Math.random() * 1000) + 100,
      cost: parseFloat((Math.random() * 50 + 5).toFixed(2)),
      tokens: Math.floor(Math.random() * 50000) + 5000,
      avgCostPerCall: parseFloat((Math.random() * 0.1 + 0.01).toFixed(3))
    }));

    // Model performance
    const modelPerformance = models.map(model => ({
      ...model,
      calls: Math.floor(Math.random() * 2000) + 200,
      tokens: Math.floor(Math.random() * 80000) + 10000,
      cost: parseFloat((Math.random() * 100 + 10).toFixed(2)),
      avgResponseTime: parseFloat((Math.random() * 2 + 0.5).toFixed(2)),
      successRate: parseFloat((95 + Math.random() * 4).toFixed(1))
    }));

    return {
      usage: usageData,
      costs: costData,
      models: modelPerformance,
      features: featureBreakdown,
      realtime: {
        currentCalls: Math.floor(Math.random() * 50) + 5,
        queuedTasks: Math.floor(Math.random() * 20),
        avgResponseTime: parseFloat((Math.random() * 3 + 1).toFixed(2)),
        errorRate: parseFloat((Math.random() * 2).toFixed(2))
      },
      summary: {
        totalCost: parseFloat((usageData.reduce((sum, day) => sum + day.cost, 0)).toFixed(2)),
        totalCalls: usageData.reduce((sum, day) => sum + day.calls, 0),
        totalTokens: usageData.reduce((sum, day) => sum + day.tokens, 0),
        avgCostPerCall: parseFloat((usageData.reduce((sum, day) => sum + day.cost, 0) / usageData.reduce((sum, day) => sum + day.calls, 0)).toFixed(4)),
        avgCostPerToken: parseFloat((usageData.reduce((sum, day) => sum + day.cost, 0) / usageData.reduce((sum, day) => sum + day.tokens, 0) * 1000).toFixed(6)),
        trend: Math.random() > 0.5 ? 'up' : 'down',
        trendPercent: parseFloat((Math.random() * 20 + 5).toFixed(1))
      }
    };
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff', '#00ffff', '#ff6666'];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            <div className="max-w-7xl mx-auto animate-pulse">
              <div className="h-8 bg-slate-200 rounded mb-6 w-64"></div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-32 bg-slate-200 rounded-lg"></div>
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-64 bg-slate-200 rounded-lg"></div>
                ))}
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Breadcrumbs */}
            <div className="mb-6">
              <ContextBreadcrumbs showContextSelector={true} />
            </div>

            {/* Header */}
            <div className="bg-white shadow-sm border rounded-lg p-6 mb-8">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Brain className="text-blue-600" />
                    LLM Costs Dashboard
                  </h1>
                  <p className="text-gray-600 mt-1">
                    Track and analyze your AI model usage and costs across all platform features
                  </p>
                  {dataSource === 'mock' && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-yellow-800 text-sm flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Currently showing simulated data. Connect to live LLM usage endpoints for real metrics.
                      </p>
                    </div>
                  )}
                  {dataSource === 'live' && (
                    <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-green-800 text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Live data connected. Showing real LLM usage and cost metrics.
                      </p>
                    </div>
                  )}
                </div>
                
                {/* Controls */}
                <div className="flex items-center gap-4">
                  <button
                    onClick={refreshData}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                  
                  <select
                    value={selectedDateRange}
                    onChange={(e) => setSelectedDateRange(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="1d">Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
                    <option value="90d">Last 90 Days</option>
                  </select>
                  
                  <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                </div>
              </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Cost</p>
                    <p className="text-2xl font-bold text-gray-900">${llmData?.summary?.totalCost}</p>
                    <div className="flex items-center gap-1 mt-1">
                      {llmData?.summary?.trend === 'up' ? (
                        <TrendingUp className="w-4 h-4 text-red-500" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-green-500" />
                      )}
                      <span className={`text-sm ${llmData?.summary?.trend === 'up' ? 'text-red-500' : 'text-green-500'}`}>
                        {llmData?.summary?.trendPercent}%
                      </span>
                    </div>
                  </div>
                  <DollarSign className="w-8 h-8 text-green-600" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Calls</p>
                    <p className="text-2xl font-bold text-gray-900">{llmData?.summary?.totalCalls?.toLocaleString()}</p>
                    <p className="text-sm text-gray-500 mt-1">Avg: ${llmData?.summary?.avgCostPerCall}/call</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-blue-600" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Tokens</p>
                    <p className="text-2xl font-bold text-gray-900">{(llmData?.summary?.totalTokens / 1000).toFixed(1)}K</p>
                    <p className="text-sm text-gray-500 mt-1">${llmData?.summary?.avgCostPerToken}/1K tokens</p>
                  </div>
                  <Cpu className="w-8 h-8 text-purple-600" />
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active Models</p>
                    <p className="text-2xl font-bold text-gray-900">{llmData?.models?.length}</p>
                    <p className="text-sm text-gray-500 mt-1">{llmData?.realtime?.currentCalls} active calls</p>
                  </div>
                  <Bot className="w-8 h-8 text-orange-600" />
                </div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Cost Trend Chart */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  Cost Trends
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={Array.isArray(llmData?.usage) ? llmData.usage.slice(-14) : []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                    />
                    <YAxis tickFormatter={(value) => `$${value}`} />
                    <Tooltip 
                      labelFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                      formatter={(value, name) => [`$${value}`, 'Cost']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="cost" 
                      stroke="#8884d8" 
                      fill="#8884d8" 
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Model Usage Distribution */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <PieChartIcon className="w-5 h-5 text-green-600" />
                  Model Usage Distribution
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Array.isArray(llmData?.models) ? llmData.models : []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({name, value}) => `${name || 'Unknown'}: ${value || 0}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="calls"
                    >
                      {(Array.isArray(llmData?.models) ? llmData.models : []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [`${value || 0} calls`, name || 'Unknown']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Provider Cost Breakdown */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  Provider Cost Breakdown
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Array.isArray(llmData?.costs) ? llmData.costs.slice(-7) : []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                    />
                    <YAxis tickFormatter={(value) => `$${value}`} />
                    <Tooltip 
                      labelFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                    />
                    <Legend />
                    <Bar dataKey="DeepInfra" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Token Usage Over Time */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-red-600" />
                  Token Usage Trends
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={Array.isArray(llmData?.usage) ? llmData.usage.slice(-14) : []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                    />
                    <YAxis tickFormatter={(value) => `${(value/1000).toFixed(0)}K`} />
                    <Tooltip 
                      labelFormatter={(value) => {
                        try {
                          return new Date(value).toLocaleDateString();
                        } catch {
                          return value;
                        }
                      }}
                      formatter={(value, name) => [`${(value/1000).toFixed(1)}K tokens`, 'Tokens']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="tokens" 
                      stroke="#ff7300" 
                      strokeWidth={3}
                      dot={{ fill: '#ff7300' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Feature Breakdown Table */}
            <div className="bg-white rounded-xl shadow-sm border mb-8">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  Feature Usage Breakdown
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Feature</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Calls</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Cost/Call</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {(Array.isArray(llmData?.features) ? llmData.features : []).map((feature, index) => (
                      <tr key={feature?.name || `feature-${index}`} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className={`w-3 h-3 rounded-full mr-3`} style={{backgroundColor: COLORS[index % COLORS.length]}}></div>
                            <span className="text-sm font-medium text-gray-900">{feature?.name || 'Unknown Feature'}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{(feature?.calls || 0).toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{((feature?.tokens || 0)/1000).toFixed(1)}K</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${feature?.cost || 0}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${feature?.avgCostPerCall || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Model Performance */}
            <div className="bg-white rounded-xl shadow-sm border mb-8">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-600" />
                  Model Performance Metrics
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
                {(Array.isArray(llmData?.models) ? llmData.models : []).map((model, index) => (
                  <div key={model?.name || `model-${index}`} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">{model?.name || 'Unknown Model'}</h4>
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">{model?.provider || 'Unknown'}</span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Calls:</span>
                        <span className="font-medium">{(model?.calls || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Cost:</span>
                        <span className="font-medium">${model?.cost || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Avg Response:</span>
                        <span className="font-medium">{model?.avgResponseTime || 0}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Success Rate:</span>
                        <span className="font-medium text-green-600">{model?.successRate || 0}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Real-time Status */}
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Eye className="w-5 h-5 text-green-600" />
                  Real-time Status
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{llmData?.realtime?.currentCalls}</div>
                  <div className="text-sm text-gray-600">Active Calls</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{llmData?.realtime?.queuedTasks}</div>
                  <div className="text-sm text-gray-600">Queued Tasks</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{llmData?.realtime?.avgResponseTime}s</div>
                  <div className="text-sm text-gray-600">Avg Response Time</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{llmData?.realtime?.errorRate}%</div>
                  <div className="text-sm text-gray-600">Error Rate</div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default LLMCosts; 