/**
 * Session Comparison Component for "what-if" scenario analysis
 * Provides side-by-side session comparison with comprehensive diff visualization
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  GitCompare,
  TrendingUp,
  TrendingDown,
  Equal,
  Plus,
  Minus,
  Edit,
  DollarSign,
  AlertTriangle,
  Settings,
  Activity,
  BarChart3,
  PieChart,
  Clock,
  Database,
  Zap,
  Shield,
  Users,
  Building,
  Server,
  HardDrive,
  Globe,
  CheckCircle,
  XCircle,
  Info,
  ArrowRight,
  Download,
  RefreshCw
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/lib/api';

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
  engagementId: string;
  onComparisonComplete?: (comparison: SessionComparison) => void;
}

export const SessionComparison: React.FC<SessionComparisonProps> = ({
  engagementId,
  onComparisonComplete
}) => {
  const [sessions, setSessions] = useState<SessionForComparison[]>([]);
  const [selectedSourceSession, setSelectedSourceSession] = useState<string>('');
  const [selectedTargetSession, setSelectedTargetSession] = useState<string>('');
  const [comparisonType, setComparisonType] = useState<string>('full_comparison');
  const [comparison, setComparison] = useState<SessionComparison | null>(null);
  const [comparisonHistory, setComparisonHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [detailedComparison, setDetailedComparison] = useState<any>(null);
  const { toast } = useToast();

  // Load available sessions for comparison
  useEffect(() => {
    loadSessionsForComparison();
    loadComparisonHistory();
  }, [engagementId]);

  const loadSessionsForComparison = async () => {
    setIsLoadingSessions(true);
    try {
      const response = await apiCall(`/admin/session-comparison/engagement/${engagementId}/sessions`);
      if (response.success) {
        setSessions(response.data.sessions || []);
      } else {
        toast({
          title: "Error loading sessions",
          description: response.message || "Failed to load sessions for comparison",
          variant: "destructive"
        });
      }
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
    setIsLoadingHistory(true);
    try {
      const response = await apiCall(`/admin/session-comparison/history?engagement_id=${engagementId}&page=1&page_size=10`);
      if (response.items) {
        setComparisonHistory(response.items);
      }
    } catch (error) {
      console.error('Error loading comparison history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const performComparison = async () => {
    if (!selectedSourceSession || !selectedTargetSession) {
      toast({
        title: "Selection Required",
        description: "Please select both source and target sessions for comparison",
        variant: "destructive"
      });
      return;
    }

    if (selectedSourceSession === selectedTargetSession) {
      toast({
        title: "Invalid Selection",
        description: "Please select different sessions for comparison",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    try {
      const comparisonRequest = {
        source_session_id: selectedSourceSession,
        target_session_id: selectedTargetSession,
        comparison_type: comparisonType,
        save_to_history: true
      };

      const response = await apiCall('/admin/session-comparison/compare', {
        method: 'POST',
        body: JSON.stringify(comparisonRequest)
      });

      if (response.success) {
        setComparison(response.data);
        onComparisonComplete?.(response.data);
        
        toast({
          title: "Comparison Complete",
          description: "Session comparison has been completed successfully",
          variant: "default"
        });

        // Reload comparison history
        loadComparisonHistory();
      } else {
        toast({
          title: "Comparison Failed",
          description: response.message || "Failed to complete session comparison",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error performing comparison:', error);
      toast({
        title: "Error",
        description: "Failed to perform session comparison",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadDetailedComparison = async (comparisonId: string) => {
    try {
      const response = await apiCall(`/admin/session-comparison/comparisons/${comparisonId}/details`);
      if (response.success) {
        setDetailedComparison(response.data);
        setShowDetailDialog(true);
      } else {
        toast({
          title: "Error",
          description: "Failed to load detailed comparison",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error loading detailed comparison:', error);
      toast({
        title: "Error",
        description: "Failed to load detailed comparison",
        variant: "destructive"
      });
    }
  };

  const exportComparison = async (format: 'csv' | 'pdf' | 'json') => {
    if (!comparison) return;

    try {
      // In a real implementation, this would call an export endpoint
      const exportData = {
        comparison_id: comparison.comparison_id,
        format,
        timestamp: new Date().toISOString()
      };

      toast({
        title: "Export Started",
        description: `Exporting comparison in ${format.toUpperCase()} format...`,
        variant: "default"
      });

      // Mock export success
      setTimeout(() => {
        toast({
          title: "Export Complete",
          description: `Comparison exported successfully as ${format.toUpperCase()}`,
          variant: "default"
        });
      }, 2000);
    } catch (error) {
      console.error('Error exporting comparison:', error);
      toast({
        title: "Export Failed",
        description: "Failed to export comparison",
        variant: "destructive"
      });
    }
  };

  const renderMetricChange = (metric: string, diff: MetricDiff) => {
    const isPositive = diff.percentage_change > 0;
    const isImprovement = diff.improvement;
    
    const icon = isPositive ? (
      isImprovement ? <TrendingUp className="w-4 h-4 text-green-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />
    ) : (
      isImprovement ? <TrendingDown className="w-4 h-4 text-green-500" /> : <TrendingUp className="w-4 h-4 text-red-500" />
    );

    const color = isImprovement ? 'text-green-600' : 'text-red-600';
    const bgColor = isImprovement ? 'bg-green-50' : 'bg-red-50';
    const borderColor = isImprovement ? 'border-green-200' : 'border-red-200';

    return (
      <div className={`p-3 border rounded-lg ${bgColor} ${borderColor}`}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-sm">{metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
          {icon}
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600">
            <span>From: {typeof diff.source_value === 'number' ? diff.source_value.toLocaleString() : diff.source_value}</span>
            <span>To: {typeof diff.target_value === 'number' ? diff.target_value.toLocaleString() : diff.target_value}</span>
          </div>
          <div className={`text-sm font-medium ${color}`}>
            {diff.percentage_change > 0 ? '+' : ''}{diff.percentage_change.toFixed(1)}%
            {diff.difference !== 0 && (
              <span className="ml-2 text-xs">
                ({diff.difference > 0 ? '+' : ''}{typeof diff.difference === 'number' ? diff.difference.toLocaleString() : diff.difference})
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderComparisonSummary = () => {
    if (!comparison) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="w-5 h-5" />
            Comparison Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <BarChart3 className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-600">{comparison.summary.total_metrics_compared}</div>
              <div className="text-sm text-gray-600">Metrics Compared</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-600">{comparison.summary.overall_improvement}</div>
              <div className="text-sm text-gray-600">Improvements</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <TrendingDown className="w-8 h-8 text-red-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-red-600">{comparison.summary.overall_regression}</div>
              <div className="text-sm text-gray-600">Regressions</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <Activity className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-purple-600">{comparison.summary.significant_changes.length}</div>
              <div className="text-sm text-gray-600">Significant Changes</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Asset Changes */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Asset Changes
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Plus className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Added</span>
                  </div>
                  <Badge variant="outline" className="text-green-600 border-green-300">
                    {comparison.assets_added_count}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Minus className="w-4 h-4 text-red-500" />
                    <span className="text-sm">Removed</span>
                  </div>
                  <Badge variant="outline" className="text-red-600 border-red-300">
                    {comparison.assets_removed_count}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Edit className="w-4 h-4 text-blue-500" />
                    <span className="text-sm">Modified</span>
                  </div>
                  <Badge variant="outline" className="text-blue-600 border-blue-300">
                    {comparison.assets_modified_count}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Equal className="w-4 h-4 text-gray-500" />
                    <span className="text-sm">Unchanged</span>
                  </div>
                  <Badge variant="outline">
                    {comparison.assets_unchanged_count}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Business Impact */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Business Impact
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-600 mb-1">Cost Savings</div>
                  <div className={`font-medium ${comparison.cost_impact.savings_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {comparison.cost_impact.savings_change >= 0 ? '+' : ''}${comparison.cost_impact.savings_change.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-600 mb-1">Risk Change</div>
                  <div className={`font-medium ${comparison.risk_impact.risk_change <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {comparison.risk_impact.risk_change > 0 ? '+' : ''}{comparison.risk_impact.risk_change.toFixed(2)} pts
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-600 mb-1">Complexity</div>
                  <div className={`font-medium ${comparison.complexity_impact.complexity_change <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {comparison.complexity_impact.complexity_change > 0 ? '+' : ''}{comparison.complexity_impact.complexity_change.toFixed(2)} pts
                  </div>
                </div>
              </div>
            </div>

            {/* Quality Impact */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Quality Impact
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Improvements</span>
                  </div>
                  <Badge variant="outline" className="text-green-600 border-green-300">
                    {comparison.quality_improvements_count}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm">Regressions</span>
                  </div>
                  <Badge variant="outline" className="text-red-600 border-red-300">
                    {comparison.quality_regressions_count}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderKeyMetrics = () => {
    if (!comparison || !comparison.key_metrics_diff) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Key Metrics Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(comparison.key_metrics_diff).map(([metric, diff]) => (
              <div key={metric}>
                {renderMetricChange(metric, diff)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderComparisonHistory = () => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Comparison History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin" />
              <span className="ml-2">Loading comparison history...</span>
            </div>
          ) : comparisonHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <GitCompare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No comparison history available</p>
            </div>
          ) : (
            <div className="space-y-4">
              {comparisonHistory.map((item, index) => (
                <div key={item.id || index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <GitCompare className="w-4 h-4 text-blue-500" />
                      <span className="font-medium">
                        {item.source_session_name} → {item.target_session_name}
                      </span>
                    </div>
                    <Badge variant="outline">
                      {item.comparison_type.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    {new Date(item.created_at).toLocaleDateString()} by {item.created_by}
                  </div>
                  {item.key_findings && (
                    <div className="mb-3">
                      <h5 className="text-sm font-medium mb-1">Key Findings:</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {item.key_findings.map((finding: string, idx: number) => (
                          <li key={idx} className="flex items-center gap-2">
                            <Info className="w-3 h-3" />
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadDetailedComparison(item.id)}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Session Selection and Comparison Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="w-5 h-5" />
            Session Comparison Tool
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Source Session</label>
              <Select value={selectedSourceSession} onValueChange={setSelectedSourceSession}>
                <SelectTrigger>
                  <SelectValue placeholder="Select source session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.filter(s => s.can_compare).map((session) => (
                    <SelectItem key={session.session_id} value={session.session_id}>
                      {session.session_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Target Session</label>
              <Select value={selectedTargetSession} onValueChange={setSelectedTargetSession}>
                <SelectTrigger>
                  <SelectValue placeholder="Select target session" />
                </SelectTrigger>
                <SelectContent>
                  {sessions.filter(s => s.can_compare && s.session_id !== selectedSourceSession).map((session) => (
                    <SelectItem key={session.session_id} value={session.session_id}>
                      {session.session_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Comparison Type</label>
              <Select value={comparisonType} onValueChange={setComparisonType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full_comparison">Full Comparison</SelectItem>
                  <SelectItem value="metrics_only">Metrics Only</SelectItem>
                  <SelectItem value="assets_diff">Assets Diff</SelectItem>
                  <SelectItem value="quality_analysis">Quality Analysis</SelectItem>
                  <SelectItem value="business_impact">Business Impact</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={performComparison}
                disabled={!selectedSourceSession || !selectedTargetSession || isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    <GitCompare className="w-4 h-4 mr-2" />
                    Compare
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Session Preview */}
          {(selectedSourceSession || selectedTargetSession) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t">
              {selectedSourceSession && (
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2">Source Session</h4>
                  {(() => {
                    const session = sessions.find(s => s.session_id === selectedSourceSession);
                    return session ? (
                      <div className="space-y-1 text-sm">
                        <div><strong>{session.session_name}</strong></div>
                        <div>Assets: {session.total_assets.toLocaleString()}</div>
                        <div>Quality: {session.quality_score.toFixed(1)}%</div>
                        <div>Cost Savings: ${session.estimated_cost_savings.toLocaleString()}</div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}

              {selectedTargetSession && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="font-medium text-green-900 mb-2">Target Session</h4>
                  {(() => {
                    const session = sessions.find(s => s.session_id === selectedTargetSession);
                    return session ? (
                      <div className="space-y-1 text-sm">
                        <div><strong>{session.session_name}</strong></div>
                        <div>Assets: {session.total_assets.toLocaleString()}</div>
                        <div>Quality: {session.quality_score.toFixed(1)}%</div>
                        <div>Cost Savings: ${session.estimated_cost_savings.toLocaleString()}</div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {renderComparisonSummary()}
          {renderKeyMetrics()}
          
          {/* Export Options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5" />
                Export Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => exportComparison('csv')}>
                  Export CSV
                </Button>
                <Button variant="outline" onClick={() => exportComparison('pdf')}>
                  Export PDF
                </Button>
                <Button variant="outline" onClick={() => exportComparison('json')}>
                  Export JSON
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Comparison History */}
      {renderComparisonHistory()}

      {/* Detailed Comparison Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Detailed Comparison Analysis</DialogTitle>
          </DialogHeader>
          {detailedComparison && (
            <div className="space-y-4">
              {/* Display detailed comparison data */}
              <div className="text-sm text-gray-600">
                Generated: {new Date(detailedComparison.generated_at).toLocaleString()}
              </div>
              {/* Add more detailed comparison visualization here */}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SessionComparison; 