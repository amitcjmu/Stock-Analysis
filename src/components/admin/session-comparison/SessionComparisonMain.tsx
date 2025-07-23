/**
 * Session Comparison Component for "what-if" scenario analysis
 * Provides side-by-side session comparison with comprehensive diff visualization
 */

import React from 'react'
import type { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import type { TrendingUp, TrendingDown, Equal, Plus, Minus, Edit, DollarSign, AlertTriangle, Settings, Activity, BarChart3, PieChart, Clock, Database, Zap, Shield, Users, Building, Server, HardDrive, Globe, CheckCircle, XCircle, Info, ArrowRight } from 'lucide-react'
import { GitCompare, Download, RefreshCw } from 'lucide-react'
import { useToast } from '@/hooks/use-toast';

// Types for session comparison
interface SessionSnapshot {
  session_id: string;
  session_name: string;
  created_at: string;
  status: string;
  total_assets: number;
  unique_assets: number;
  duplicate_assets: number;
  quality_score: number;
  completeness_score: number;
  assets_by_type: Record<string, number>;
  assets_by_department: Record<string, number>;
  assets_by_status: Record<string, number>;
  validation_errors: number;
  missing_critical_fields: number;
  data_consistency_score: number;
  estimated_cost_savings: number;
  migration_complexity_score: number;
  risk_score: number;
  technologies_detected: string[];
  dependencies_mapped: number;
  integration_complexity: number;
  modernization_potential: number;
  agent_confidence_score: number;
  classification_accuracy: number;
  recommendations_count: number;
  processing_time_seconds: number;
  data_source_count: number;
  import_method: string;
  errors_encountered: number;
}

interface ComparisonHistoryItem {
  comparison_id: string;
  source_session: string;
  target_session: string;
  generated_at: string;
  overall_improvement: number;
  comparison_type?: string;
  performed_by?: string;
  notes?: string;
}

interface MetricDiff {
  source_value: number;
  target_value: number;
  difference: number;
  percentage_change: number;
  improvement: boolean;
}

interface SessionComparison {
  comparison_id: string;
  source_session_id: string;
  target_session_id: string;
  comparison_type: string;
  generated_at: string;
  summary: {
    total_metrics_compared: number;
    significant_changes: Array<{
      metric: string;
      change: number;
      direction: 'improvement' | 'regression';
    }>;
    overall_improvement: number;
    overall_regression: number;
    source_session: string;
    target_session: string;
  };
  key_metrics_diff: Record<string, MetricDiff>;
  assets_added_count: number;
  assets_removed_count: number;
  assets_modified_count: number;
  assets_unchanged_count: number;
  quality_improvements_count: number;
  quality_regressions_count: number;
  cost_impact: {
    savings_change: number;
    description: string;
  };
  risk_impact: {
    risk_change: number;
    description: string;
  };
  complexity_impact: {
    complexity_change: number;
    description: string;
  };
}

interface SessionForComparison {
  session_id: string;
  session_name: string;
  created_at: string;
  status: string;
  total_assets: number;
  quality_score: number;
  estimated_cost_savings: number;
  processing_time_hours: number;
  can_compare: boolean;
}

interface SessionComparisonProps {
  engagementId?: string;
  onComparisonComplete?: (comparison: SessionComparison) => void;
}

export const SessionComparisonMain: React.FC<SessionComparisonProps> = ({
  engagementId,
  onComparisonComplete
}) => {
  const [sessions, setSessions] = useState<SessionForComparison[]>([]);
  const [selectedSourceSession, setSelectedSourceSession] = useState<string>('');
  const [selectedTargetSession, setSelectedTargetSession] = useState<string>('');
  const [comparisonType, setComparisonType] = useState<string>('full_comparison');
  const [comparison, setComparison] = useState<SessionComparison | null>(null);
  const [comparisonHistory, setComparisonHistory] = useState<ComparisonHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const { toast } = useToast();

  // Load available sessions for comparison
  useEffect(() => {
    loadSessionsForComparison();
    loadComparisonHistory();
  }, [engagementId]);

  const loadSessionsForComparison = async () => {
    setIsLoadingSessions(true);
    try {
      // Demo data for sessions
      const demoSessions: SessionForComparison[] = [
        {
          session_id: '1',
          session_name: 'Initial Discovery Session',
          created_at: '2025-01-10T10:30:00Z',
          status: 'completed',
          total_assets: 1250,
          quality_score: 78.5,
          estimated_cost_savings: 2500000,
          processing_time_hours: 2.5,
          can_compare: true
        },
        {
          session_id: '2',
          session_name: 'Enhanced Data Import',
          created_at: '2025-01-15T14:20:00Z',
          status: 'completed',
          total_assets: 1380,
          quality_score: 85.2,
          estimated_cost_savings: 2750000,
          processing_time_hours: 3.1,
          can_compare: true
        }
      ];

      setSessions(demoSessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
      toast({
        title: "Error",
        description: "Failed to load sessions for comparison",
        variant: "destructive"
      });
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const loadComparisonHistory = async () => {
    try {
      // Demo comparison history
      setComparisonHistory([
        {
          comparison_id: '1',
          source_session: 'Initial Discovery Session',
          target_session: 'Enhanced Data Import',
          generated_at: '2025-01-16T09:00:00Z',
          overall_improvement: 8.5
        }
      ]);
    } catch (error) {
      console.error('Error loading comparison history:', error);
    }
  };

  const performComparison = async () => {
    if (!selectedSourceSession || !selectedTargetSession) {
      toast({
        title: "Selection Required",
        description: "Please select both source and target sessions",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    try {
      const demoComparison: SessionComparison = {
        comparison_id: Date.now().toString(),
        source_session_id: selectedSourceSession,
        target_session_id: selectedTargetSession,
        comparison_type: comparisonType,
        generated_at: new Date().toISOString(),
        summary: {
          total_metrics_compared: 15,
          significant_changes: [
            { metric: 'Quality Score', change: 6.7, direction: 'improvement' },
            { metric: 'Total Assets', change: 130, direction: 'improvement' },
            { metric: 'Cost Savings', change: 250000, direction: 'improvement' }
          ],
          overall_improvement: 8.5,
          overall_regression: 1.2,
          source_session: sessions.find(s => s.session_id === selectedSourceSession)?.session_name || '',
          target_session: sessions.find(s => s.session_id === selectedTargetSession)?.session_name || ''
        },
        key_metrics_diff: {
          quality_score: {
            source_value: 78.5,
            target_value: 85.2,
            difference: 6.7,
            percentage_change: 8.5,
            improvement: true
          },
          total_assets: {
            source_value: 1250,
            target_value: 1380,
            difference: 130,
            percentage_change: 10.4,
            improvement: true
          }
        },
        assets_added_count: 130,
        assets_removed_count: 0,
        assets_modified_count: 45,
        assets_unchanged_count: 1205
      };

      setComparison(demoComparison);
      
      if (onComparisonComplete) {
        onComparisonComplete(demoComparison);
      }

      toast({
        title: "Comparison Complete",
        description: "Session comparison generated successfully"
      });
    } catch (error) {
      console.error('Error performing comparison:', error);
      toast({
        title: "Comparison Failed",
        description: "Failed to generate session comparison",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderMetricChange = (metric: string, diff: MetricDiff) => {
    const isImprovement = diff.improvement;
    const Icon = isImprovement ? TrendingUp : TrendingDown;
    const colorClass = isImprovement ? 'text-green-600' : 'text-red-600';
    const bgClass = isImprovement ? 'bg-green-50' : 'bg-red-50';

    return (
      <div className={`p-3 rounded-lg ${bgClass}`}>
        <div className="flex items-center justify-between">
          <span className="font-medium">{metric}</span>
          <Icon className={`w-4 h-4 ${colorClass}`} />
        </div>
        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-sm">
            <span>Source:</span>
            <span>{diff.source_value.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Target:</span>
            <span>{diff.target_value.toLocaleString()}</span>
          </div>
          <div className={`flex justify-between text-sm font-medium ${colorClass}`}>
            <span>Change:</span>
            <span>
              {diff.difference > 0 ? '+' : ''}{diff.difference.toLocaleString()} 
              ({diff.percentage_change > 0 ? '+' : ''}{diff.percentage_change.toFixed(1)}%)
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderComparisonSummary = () => {
    if (!comparison) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="w-5 h-5" />
            Comparison Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Sessions Compared</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Source</Badge>
                  <span className="text-sm">{comparison.summary.source_session}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Target</Badge>
                  <span className="text-sm">{comparison.summary.target_session}</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-3">Overall Impact</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Improvements:</span>
                  <span className="text-sm font-medium text-green-600">
                    {comparison.summary.overall_improvement.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Regressions:</span>
                  <span className="text-sm font-medium text-red-600">
                    {comparison.summary.overall_regression.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <Separator className="my-4" />

          <div>
            <h4 className="font-medium mb-3">Asset Changes</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{comparison.assets_added_count}</div>
                <div className="text-sm text-muted-foreground">Added</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{comparison.assets_modified_count}</div>
                <div className="text-sm text-muted-foreground">Modified</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">{comparison.assets_unchanged_count}</div>
                <div className="text-sm text-muted-foreground">Unchanged</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{comparison.assets_removed_count}</div>
                <div className="text-sm text-muted-foreground">Removed</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderKeyMetrics = () => {
    if (!comparison) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Key Metrics Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(comparison.key_metrics_diff).map(([metric, diff]) => (
              <div key={metric}>
                {renderMetricChange(metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()), diff)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Session Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="w-5 h-5" />
            Session Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Source Session</label>
              <Select value={selectedSourceSession} onValueChange={setSelectedSourceSession}>
                <SelectTrigger>
                  <SelectValue placeholder="Select source session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.filter(s => s.can_compare).map(session => (
                    <SelectItem key={session.session_id} value={session.session_id}>
                      {session.session_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Target Session</label>
              <Select value={selectedTargetSession} onValueChange={setSelectedTargetSession}>
                <SelectTrigger>
                  <SelectValue placeholder="Select target session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.filter(s => s.can_compare && s.session_id !== selectedSourceSession).map(session => (
                    <SelectItem key={session.session_id} value={session.session_id}>
                      {session.session_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <Button 
              onClick={performComparison}
              disabled={!selectedSourceSession || !selectedTargetSession || isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Comparing...
                </>
              ) : (
                <>
                  <GitCompare className="w-4 h-4 mr-2" />
                  Compare Sessions
                </>
              )}
            </Button>
            
            {comparison && (
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export Results
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {comparison && (
        <Tabs defaultValue="summary" className="space-y-4">
          <TabsList>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="metrics">Key Metrics</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="summary">
            {renderComparisonSummary()}
          </TabsContent>

          <TabsContent value="metrics">
            {renderKeyMetrics()}
          </TabsContent>

          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Comparison History</CardTitle>
              </CardHeader>
              <CardContent>
                {comparisonHistory.length > 0 ? (
                  <div className="space-y-2">
                    {comparisonHistory.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">{item.source_session} vs {item.target_session}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(item.generated_at).toLocaleDateString()}
                          </div>
                        </div>
                        <Badge variant="outline">
                          {item.overall_improvement > 0 ? '+' : ''}{item.overall_improvement}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No comparison history available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default SessionComparisonMain; 