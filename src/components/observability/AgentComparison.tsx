/**
 * Agent Comparison Component
 * Side-by-side agent performance analysis and comparison tools
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Download, RefreshCw, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';
import { useAgentComparison } from './hooks/useAgentComparison';
import { COMPARISON_METRICS, PERIOD_OPTIONS } from './utils/constants';
import { exportToJSON } from './utils/formatters';
import { AgentSelector } from './comparison/AgentSelector';
import { MetricCard } from './comparison/MetricCard';
import { RankingsOverview } from './comparison/RankingsOverview';
import { SuccessRateTrendChart, PerformanceRadarChart } from './comparison/ComparisonCharts';

// Types moved to hooks/useAgentComparison.ts
import type { AgentComparisonData } from './hooks/useAgentComparison';

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

// Constants moved to utils/constants.ts

// MetricCard component moved to comparison/MetricCard.tsx

// AgentSelector component moved to comparison/AgentSelector.tsx

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
  const [period, setPeriod] = useState(defaultPeriod);
  const [activeTab, setActiveTab] = useState('overview');

  // Use the custom hook for comparison data
  const { comparisonData, loading, error, refresh } = useAgentComparison({
    selectedAgents,
    period,
    autoRefresh: false
  });

  // Load available agents
  useEffect(() => {
    loadAvailableAgents();
  }, []);

  // Notify parent when selection changes
  useEffect(() => {
    if (onComparisonChange) {
      onComparisonChange(selectedAgents);
    }
  }, [selectedAgents, onComparisonChange]);

  const loadAvailableAgents = async (): Promise<any> => {
    try {
      const agents = await agentObservabilityService.getAgentNames();
      setAvailableAgents(agents);
    } catch (err) {
      console.error('Failed to load available agents:', err);
    }
  };

  const handleSelectionChange = (agents: string[]): void => {
    setSelectedAgents(agents);
  };

  const handleExportData = (): void => {
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

    exportToJSON(exportData, 'agent-comparison');
  };

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
              {PERIOD_OPTIONS.map(option => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={refresh} variant="outline" disabled={loading || selectedAgents.length === 0}>
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
                  {showRanking && <RankingsOverview comparisonData={comparisonData} />}

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
                    <SuccessRateTrendChart comparisonData={comparisonData} />
                    <PerformanceRadarChart comparisonData={comparisonData} />
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
