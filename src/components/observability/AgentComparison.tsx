/**
 * Agent Comparison Component
 * Side-by-side agent performance analysis and comparison tools
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Search, X, Download, RefreshCw, ArrowUpDown, Trophy, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';
import { AgentStatusIndicator } from './AgentStatusIndicator';

// Types for comparison data
interface AgentComparisonData {
  agentName: string;
  metrics: {
    successRate: number;
    totalTasks: number;
    avgDuration: number;
    avgConfidence: number;
    memoryUsage: number;
    llmCalls: number;
    errorRate: number;
    throughput: number; // tasks per hour
  };
  trends: {
    successRateHistory: number[];
    durationHistory: number[];
    confidenceHistory: number[];
    timestamps: string[];
  };
  ranking: {
    overall: number;
    successRate: number;
    performance: number;
    reliability: number;
  };
}

interface ComparisonMetric {
  key: keyof AgentComparisonData['metrics'];
  label: string;
  unit: string;
  higherIsBetter: boolean;
  format: (value: number) => string;
}

interface AgentComparisonProps {
  /** Pre-selected agents to compare */
  initialAgents?: string[];
  /** Maximum number of agents to compare */
  maxAgents?: number;
  /** Default comparison period in days */
  defaultPeriod?: number;
  /** Show ranking information */
  showRanking?: boolean;
  /** Enable export functionality */
  enableExport?: boolean;
  /** Callback when comparison changes */
  onComparisonChange?: (agents: string[]) => void;
  /** CSS class name */
  className?: string;
}

const COMPARISON_METRICS: ComparisonMetric[] = [
  {
    key: 'successRate',
    label: 'Success Rate',
    unit: '%',
    higherIsBetter: true,
    format: (value) => `${(value * 100).toFixed(1)}%`
  },
  {
    key: 'avgDuration',
    label: 'Avg Duration',
    unit: 's',
    higherIsBetter: false,
    format: (value) => `${value.toFixed(1)}s`
  },
  {
    key: 'avgConfidence',
    label: 'Avg Confidence',
    unit: '%',
    higherIsBetter: true,
    format: (value) => `${(value * 100).toFixed(1)}%`
  },
  {
    key: 'totalTasks',
    label: 'Total Tasks',
    unit: '',
    higherIsBetter: true,
    format: (value) => value.toString()
  },
  {
    key: 'throughput',
    label: 'Throughput',
    unit: 'tasks/hr',
    higherIsBetter: true,
    format: (value) => `${value.toFixed(1)}/hr`
  },
  {
    key: 'memoryUsage',
    label: 'Memory Usage',
    unit: 'MB',
    higherIsBetter: false,
    format: (value) => `${value.toFixed(1)} MB`
  },
  {
    key: 'errorRate',
    label: 'Error Rate',
    unit: '%',
    higherIsBetter: false,
    format: (value) => `${(value * 100).toFixed(1)}%`
  }
];

const MetricCard: React.FC<{
  metric: ComparisonMetric;
  agents: AgentComparisonData[];
  selectedAgents: string[];
}> = ({ metric, agents, selectedAgents }) => {
  const values = agents
    .filter(agent => selectedAgents.includes(agent.agentName))
    .map(agent => ({
      name: agent.agentName,
      value: agent.metrics[metric.key],
      ranking: agent.ranking.overall
    }))
    .sort((a, b) => metric.higherIsBetter ? b.value - a.value : a.value - b.value);

  const best = values[0];
  const worst = values[values.length - 1];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-gray-600">
          {metric.label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {values.map((item, index) => {
            const isBest = item === best;
            const isWorst = item === worst && values.length > 1;
            
            return (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    isBest ? 'bg-green-500' : 
                    isWorst ? 'bg-red-500' : 
                    'bg-gray-400'
                  }`} />
                  <span className="text-sm font-medium text-gray-900 truncate max-w-32">
                    {item.name.replace('Agent', '')}
                  </span>
                  {isBest && <Trophy className="w-4 h-4 text-yellow-500" />}
                </div>
                <div className="flex items-center gap-1">
                  <span className={`text-sm font-bold ${
                    isBest ? 'text-green-600' : 
                    isWorst ? 'text-red-600' : 
                    'text-gray-900'
                  }`}>
                    {metric.format(item.value)}
                  </span>
                  {index === 0 && values.length > 1 && (
                    <TrendingUp className="w-3 h-3 text-green-500" />
                  )}
                  {index === values.length - 1 && values.length > 1 && (
                    <TrendingDown className="w-3 h-3 text-red-500" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

const AgentSelector: React.FC<{
  availableAgents: string[];
  selectedAgents: string[];
  onSelectionChange: (agents: string[]) => void;
  maxAgents: number;
}> = ({ availableAgents, selectedAgents, onSelectionChange, maxAgents }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredAgents = availableAgents.filter(agent =>
    agent.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedAgents.includes(agent)
  );

  const handleAddAgent = (agent: string) => {
    if (selectedAgents.length < maxAgents) {
      onSelectionChange([...selectedAgents, agent]);
    }
  };

  const handleRemoveAgent = (agent: string) => {
    onSelectionChange(selectedAgents.filter(a => a !== agent));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Select Agents to Compare</CardTitle>
        <p className="text-sm text-gray-600">
          Select up to {maxAgents} agents for performance comparison
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Selected agents */}
          {selectedAgents.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Selected Agents ({selectedAgents.length}/{maxAgents})</h4>
              <div className="flex flex-wrap gap-2">
                {selectedAgents.map(agent => (
                  <Badge key={agent} variant="default" className="flex items-center gap-1">
                    {agent.replace('Agent', '')}
                    <X 
                      className="w-3 h-3 cursor-pointer hover:text-red-500" 
                      onClick={() => handleRemoveAgent(agent)}
                    />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Agent search and selection */}
          {selectedAgents.length < maxAgents && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Available Agents</h4>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search agents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {filteredAgents.map(agent => (
                  <div
                    key={agent}
                    className="flex items-center justify-between p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleAddAgent(agent)}
                  >
                    <span className="text-sm">{agent}</span>
                    <Button variant="ghost" size="sm">
                      Add
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const AgentComparison: React.FC<AgentComparisonProps> = ({
  initialAgents = [],
  maxAgents = 4,
  defaultPeriod = 7,
  showRanking = true,
  enableExport = true,
  onComparisonChange,
  className = ''
}) => {
  const [selectedAgents, setSelectedAgents] = useState<string[]>(initialAgents);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<AgentComparisonData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState(defaultPeriod);
  const [activeTab, setActiveTab] = useState('overview');

  // Load available agents
  useEffect(() => {
    loadAvailableAgents();
  }, []);

  // Load comparison data when selection changes
  useEffect(() => {
    if (selectedAgents.length > 0) {
      loadComparisonData();
    }
    
    if (onComparisonChange) {
      onComparisonChange(selectedAgents);
    }
  }, [selectedAgents, period]);

  const loadAvailableAgents = async () => {
    try {
      const agents = await agentObservabilityService.getAgentNames();
      setAvailableAgents(agents);
    } catch (err) {
      console.error('Failed to load available agents:', err);
      setError('Failed to load available agents');
    }
  };

  const loadComparisonData = async () => {
    if (selectedAgents.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      // Load data for each selected agent
      const agentDataPromises = selectedAgents.map(async (agentName) => {
        const [performance, analytics] = await Promise.all([
          agentObservabilityService.getAgentPerformance(agentName, period),
          agentObservabilityService.getAgentAnalytics(agentName, period)
        ]);

        if (!performance.success || !analytics.success) {
          throw new Error(`Failed to load data for ${agentName}`);
        }

        const perfData = performance.data;
        const analyticsData = analytics.data;

        // Calculate derived metrics
        const errorRate = perfData.summary.total_tasks > 0 ? 
          perfData.summary.failed_tasks / perfData.summary.total_tasks : 0;
        
        const throughput = perfData.summary.total_tasks / (period * 24); // tasks per hour

        return {
          agentName,
          metrics: {
            successRate: perfData.summary.success_rate,
            totalTasks: perfData.summary.total_tasks,
            avgDuration: perfData.summary.avg_duration_seconds,
            avgConfidence: perfData.summary.avg_confidence_score,
            memoryUsage: analyticsData.analytics.resource_usage.avg_memory_usage_mb,
            llmCalls: perfData.summary.total_llm_calls,
            errorRate,
            throughput
          },
          trends: {
            successRateHistory: perfData.trends.success_rates,
            durationHistory: perfData.trends.avg_durations,
            confidenceHistory: perfData.trends.confidence_scores || Array.from({ length: perfData.trends.success_rates.length }, () => 0),
            timestamps: perfData.trends.dates
          },
          ranking: {
            overall: 0, // Will be calculated after loading all data
            successRate: 0,
            performance: 0,
            reliability: 0
          }
        } as AgentComparisonData;
      });

      const agentData = await Promise.all(agentDataPromises);

      // Calculate rankings
      const dataWithRankings = calculateRankings(agentData);
      
      setComparisonData(dataWithRankings);
    } catch (err) {
      console.error('Failed to load comparison data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  };

  const calculateRankings = (data: AgentComparisonData[]): AgentComparisonData[] => {
    // Calculate overall ranking based on multiple factors
    const scoredData = data.map(agent => {
      const performanceScore = 
        (agent.metrics.successRate * 0.3) +
        ((1 - agent.metrics.errorRate) * 0.2) +
        (agent.metrics.avgConfidence * 0.2) +
        (Math.min(agent.metrics.throughput / 10, 1) * 0.15) +
        (Math.max(0, 1 - agent.metrics.avgDuration / 60) * 0.15);

      return { ...agent, performanceScore };
    });

    // Sort by performance score and assign rankings
    scoredData.sort((a, b) => b.performanceScore - a.performanceScore);
    
    return scoredData.map((agent, index) => ({
      ...agent,
      ranking: {
        overall: index + 1,
        successRate: getRankByMetric(data, 'successRate', agent.agentName, true),
        performance: getRankByMetric(data, 'avgDuration', agent.agentName, false),
        reliability: getRankByMetric(data, 'errorRate', agent.agentName, false)
      }
    }));
  };

  const getRankByMetric = (data: AgentComparisonData[], metric: keyof AgentComparisonData['metrics'], agentName: string, higherIsBetter: boolean): number => {
    const sorted = [...data].sort((a, b) => 
      higherIsBetter ? b.metrics[metric] - a.metrics[metric] : a.metrics[metric] - b.metrics[metric]
    );
    return sorted.findIndex(agent => agent.agentName === agentName) + 1;
  };

  const handleSelectionChange = (agents: string[]) => {
    setSelectedAgents(agents);
  };

  const handleExportData = () => {
    if (comparisonData.length === 0) return;

    const exportData = {
      timestamp: new Date().toISOString(),
      period: `${period} days`,
      agents: comparisonData.map(agent => ({
        name: agent.agentName,
        metrics: agent.metrics,
        ranking: agent.ranking
      }))
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `agent-comparison-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Prepare chart data
  const chartData = useMemo(() => {
    if (comparisonData.length === 0) return [];

    const maxLength = Math.max(...comparisonData.map(agent => agent.trends.timestamps.length));
    
    return Array.from({ length: maxLength }, (_, index) => {
      const dataPoint: any = { index };
      
      comparisonData.forEach(agent => {
        if (agent.trends.timestamps[index]) {
          dataPoint[`${agent.agentName}_success`] = agent.trends.successRateHistory[index] * 100;
          dataPoint[`${agent.agentName}_duration`] = agent.trends.durationHistory[index];
          dataPoint.timestamp = agent.trends.timestamps[index];
        }
      });
      
      return dataPoint;
    });
  }, [comparisonData]);

  // Prepare radar chart data
  const radarData = useMemo(() => {
    return COMPARISON_METRICS.slice(0, 6).map(metric => {
      const dataPoint: any = { metric: metric.label };
      
      comparisonData.forEach(agent => {
        const value = agent.metrics[metric.key];
        // Normalize values to 0-100 scale for radar chart
        let normalizedValue;
        if (metric.key === 'successRate' || metric.key === 'avgConfidence') {
          normalizedValue = value * 100;
        } else if (metric.key === 'avgDuration') {
          normalizedValue = Math.max(0, 100 - (value / 10) * 100); // Invert duration (lower is better)
        } else if (metric.key === 'errorRate') {
          normalizedValue = Math.max(0, 100 - (value * 100)); // Invert error rate
        } else {
          normalizedValue = Math.min(100, (value / 100) * 100); // Scale other metrics
        }
        
        dataPoint[agent.agentName] = normalizedValue;
      });
      
      return dataPoint;
    });
  }, [comparisonData]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Agent Performance Comparison</h2>
          <p className="text-gray-600">
            Compare performance metrics across multiple agents
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={period.toString()} onValueChange={(value) => setPeriod(parseInt(value))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last day</SelectItem>
              <SelectItem value="7">Last week</SelectItem>
              <SelectItem value="30">Last month</SelectItem>
              <SelectItem value="90">Last 3 months</SelectItem>
            </SelectContent>
          </Select>
          
          <Button onClick={loadComparisonData} variant="outline" disabled={loading || selectedAgents.length === 0}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          {enableExport && (
            <Button onClick={handleExportData} variant="outline" disabled={comparisonData.length === 0}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Agent Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AgentSelector
            availableAgents={availableAgents}
            selectedAgents={selectedAgents}
            onSelectionChange={handleSelectionChange}
            maxAgents={maxAgents}
          />
        </div>

        {selectedAgents.length > 0 && (
          <div className="lg:col-span-2">
            {error && (
              <Alert className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {loading ? (
              <Card>
                <CardContent className="p-8">
                  <div className="text-center">
                    <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-2 animate-spin" />
                    <p className="text-gray-500">Loading comparison data...</p>
                  </div>
                </CardContent>
              </Card>
            ) : comparisonData.length > 0 ? (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="trends">Trends</TabsTrigger>
                  <TabsTrigger value="detailed">Detailed</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4 mt-4">
                  {/* Rankings Overview */}
                  {showRanking && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Overall Rankings</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {comparisonData
                            .sort((a, b) => a.ranking.overall - b.ranking.overall)
                            .map((agent, index) => (
                              <div key={agent.agentName} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                                <div className="flex items-center gap-3">
                                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                                    index === 0 ? 'bg-yellow-500' :
                                    index === 1 ? 'bg-gray-400' :
                                    index === 2 ? 'bg-orange-500' :
                                    'bg-gray-300'
                                  }`}>
                                    {index + 1}
                                  </div>
                                  <span className="font-medium">{agent.agentName}</span>
                                  <AgentStatusIndicator status="active" variant="dot" size="sm" />
                                </div>
                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                  <span>Success: #{agent.ranking.successRate}</span>
                                  <span>Speed: #{agent.ranking.performance}</span>
                                  <span>Reliability: #{agent.ranking.reliability}</span>
                                </div>
                              </div>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {COMPARISON_METRICS.slice(0, 4).map(metric => (
                      <MetricCard
                        key={metric.key}
                        metric={metric}
                        agents={comparisonData}
                        selectedAgents={selectedAgents}
                      />
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="trends" className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Success Rate Trends */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Success Rate Trends</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="index" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {comparisonData.map((agent, index) => (
                              <Line
                                key={agent.agentName}
                                type="monotone"
                                dataKey={`${agent.agentName}_success`}
                                stroke={`hsl(${index * 120}, 70%, 50%)`}
                                strokeWidth={2}
                                name={agent.agentName}
                              />
                            ))}
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Performance Radar */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Performance Radar</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <RadarChart data={radarData}>
                            <PolarGrid />
                            <PolarAngleAxis dataKey="metric" />
                            <PolarRadiusAxis angle={90} domain={[0, 100]} />
                            {comparisonData.map((agent, index) => (
                              <Radar
                                key={agent.agentName}
                                name={agent.agentName}
                                dataKey={agent.agentName}
                                stroke={`hsl(${index * 120}, 70%, 50%)`}
                                fill={`hsl(${index * 120}, 70%, 50%)`}
                                fillOpacity={0.2}
                              />
                            ))}
                            <Legend />
                          </RadarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="detailed" className="space-y-4 mt-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                    {COMPARISON_METRICS.map(metric => (
                      <MetricCard
                        key={metric.key}
                        metric={metric}
                        agents={comparisonData}
                        selectedAgents={selectedAgents}
                      />
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentComparison;
export type { AgentComparisonProps, AgentComparisonData };