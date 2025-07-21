/**
 * Recommendation Engine Component
 * AI-powered fine-tuning suggestions based on performance data
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Brain, Zap, Clock, Target, ArrowRight, RefreshCw, X, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

// Types for recommendations
interface Recommendation {
  id: string;
  agentName: string;
  category: 'performance' | 'reliability' | 'efficiency' | 'resource' | 'configuration';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  effort: 'low' | 'medium' | 'high';
  estimatedImprovement: {
    metric: string;
    current: number;
    projected: number;
    unit: string;
  };
  rationale: string[];
  steps: string[];
  prerequisites?: string[];
  tags: string[];
  confidence: number; // 0-1
  basedOnData: {
    period: string;
    sampleSize: number;
    keyMetrics: Record<string, number>;
  };
  feedback?: {
    helpful: number;
    notHelpful: number;
    userFeedback: 'helpful' | 'not_helpful' | null;
  };
}

interface RecommendationEngineProps {
  /** Agent to generate recommendations for */
  agentName?: string;
  /** Show recommendations for all agents */
  showAllAgents?: boolean;
  /** Maximum number of recommendations to show */
  maxRecommendations?: number;
  /** Enable user feedback on recommendations */
  enableFeedback?: boolean;
  /** Callback when recommendation is applied */
  onRecommendationApply?: (recommendation: Recommendation) => void;
  /** CSS class name */
  className?: string;
}

const RecommendationCard: React.FC<{
  recommendation: Recommendation;
  onApply?: (recommendation: Recommendation) => void;
  onFeedback?: (recommendationId: string, helpful: boolean) => void;
  enableFeedback?: boolean;
}> = ({ recommendation, onApply, onFeedback, enableFeedback = false }) => {
  const [expanded, setExpanded] = useState(false);
  const [applying, setApplying] = useState(false);

  const priorityColors = {
    high: 'border-l-red-500 bg-red-50',
    medium: 'border-l-yellow-500 bg-yellow-50',
    low: 'border-l-blue-500 bg-blue-50'
  };

  const categoryIcons = {
    performance: <TrendingUp className="w-5 h-5 text-blue-500" />,
    reliability: <CheckCircle className="w-5 h-5 text-green-500" />,
    efficiency: <Zap className="w-5 h-5 text-purple-500" />,
    resource: <Target className="w-5 h-5 text-orange-500" />,
    configuration: <Brain className="w-5 h-5 text-indigo-500" />
  };

  const impactColors = {
    high: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    low: 'text-blue-600 bg-blue-100'
  };

  const effortColors = {
    low: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100'
  };

  const handleApply = async () => {
    if (!onApply) return;
    
    setApplying(true);
    try {
      await onApply(recommendation);
    } finally {
      setApplying(false);
    }
  };

  const handleFeedback = (helpful: boolean) => {
    if (onFeedback) {
      onFeedback(recommendation.id, helpful);
    }
  };

  const improvementPercent = recommendation.estimatedImprovement.current > 0 ? 
    ((recommendation.estimatedImprovement.projected - recommendation.estimatedImprovement.current) / recommendation.estimatedImprovement.current * 100) : 0;

  return (
    <Card className={`border-l-4 transition-all duration-200 ${priorityColors[recommendation.priority]}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {categoryIcons[recommendation.category]}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-gray-900 text-sm">{recommendation.title}</h3>
                <Badge variant="secondary" className="text-xs">
                  {recommendation.category}
                </Badge>
                <Badge variant="outline" className={`text-xs ${impactColors[recommendation.impact]}`}>
                  {recommendation.impact} impact
                </Badge>
                <Badge variant="outline" className={`text-xs ${effortColors[recommendation.effort]}`}>
                  {recommendation.effort} effort
                </Badge>
              </div>
              <p className="text-sm text-gray-600">{recommendation.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-right">
              <div className="text-xs text-gray-500">Confidence</div>
              <div className="text-sm font-medium">{(recommendation.confidence * 100).toFixed(0)}%</div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <X className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Impact Preview */}
        <div className="mt-3 p-3 bg-white rounded-md border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {recommendation.estimatedImprovement.metric}
            </span>
            <span className={`text-sm font-bold ${improvementPercent > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {improvementPercent > 0 ? '+' : ''}{improvementPercent.toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>
              {recommendation.estimatedImprovement.current.toFixed(1)} {recommendation.estimatedImprovement.unit}
            </span>
            <ArrowRight className="w-3 h-3" />
            <span className="font-medium">
              {recommendation.estimatedImprovement.projected.toFixed(1)} {recommendation.estimatedImprovement.unit}
            </span>
          </div>
          <Progress 
            value={Math.min(100, (recommendation.estimatedImprovement.projected / (recommendation.estimatedImprovement.current * 2)) * 100)} 
            className="mt-2 h-1" 
          />
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            {/* Rationale */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Why this recommendation?</h4>
              <ul className="space-y-1">
                {recommendation.rationale.map((reason, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                    <div className="w-1 h-1 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Implementation Steps */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Implementation Steps</h4>
              <ol className="space-y-2">
                {recommendation.steps.map((step, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start gap-3">
                    <div className="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            {/* Prerequisites */}
            {recommendation.prerequisites && recommendation.prerequisites.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Prerequisites</h4>
                <ul className="space-y-1">
                  {recommendation.prerequisites.map((prereq, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                      <AlertTriangle className="w-3 h-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                      {prereq}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Data Source */}
            <div className="bg-gray-50 p-3 rounded-md">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Based on Data</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Period: {recommendation.basedOnData.period}</div>
                <div>Sample Size: {recommendation.basedOnData.sampleSize} tasks</div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(recommendation.basedOnData.keyMetrics).map(([metric, value]) => (
                    <Badge key={metric} variant="outline" className="text-xs">
                      {metric}: {typeof value === 'number' ? value.toFixed(2) : value}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2 border-t">
              <div className="flex items-center gap-2">
                {recommendation.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              <div className="flex items-center gap-2">
                {enableFeedback && (
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleFeedback(true)}
                      className={`${recommendation.feedback?.userFeedback === 'helpful' ? 'bg-green-100 text-green-600' : ''}`}
                    >
                      <ThumbsUp className="w-3 h-3" />
                      {recommendation.feedback?.helpful || 0}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleFeedback(false)}
                      className={`${recommendation.feedback?.userFeedback === 'not_helpful' ? 'bg-red-100 text-red-600' : ''}`}
                    >
                      <ThumbsDown className="w-3 h-3" />
                      {recommendation.feedback?.notHelpful || 0}
                    </Button>
                  </div>
                )}

                <Button
                  onClick={handleApply}
                  size="sm"
                  disabled={applying}
                >
                  {applying && <RefreshCw className="w-3 h-3 mr-1 animate-spin" />}
                  Apply Recommendation
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

const RecommendationEngine: React.FC<RecommendationEngineProps> = ({
  agentName,
  showAllAgents = false,
  maxRecommendations = 10,
  enableFeedback = true,
  onRecommendationApply,
  className = ''
}) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [activePriority, setActivePriority] = useState<string>('all');

  useEffect(() => {
    generateRecommendations();
  }, [agentName, showAllAgents]);

  const generateRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      // Since we don't have a real recommendation API yet, we'll generate mock recommendations
      // Generate recommendations based on actual agent performance data
      const realRecommendations = await generateRealDataRecommendations();
      setRecommendations(realRecommendations);
    } catch (err) {
      console.error('Failed to generate recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  const generateRealDataRecommendations = async (): Promise<Recommendation[]> => {
    // Generate recommendations using real agent performance data from APIs
    let agents: string[] = [];
    
    try {
      const agentsResponse = await agentObservabilityService.getAllAgentsSummary();
      if (agentsResponse.success) {
        const agentCards = agentObservabilityService.transformToAgentCardData(agentsResponse);
        agents = agentName ? [agentName] : agentCards.map(agent => agent.name);
      }
    } catch (error) {
      console.error('Failed to fetch real agents:', error);
      agents = agentName ? [agentName] : [];
    }
    const recommendations: Recommendation[] = [];

    for (const agent of agents.slice(0, showAllAgents ? undefined : 1)) {
      try {
        const [performance, analytics] = await Promise.all([
          agentObservabilityService.getAgentPerformance(agent, 7),
          agentObservabilityService.getAgentAnalytics(agent, 7)
        ]);

        if (performance.success && analytics.success) {
          const perfData = performance.data;
          const analyticsData = analytics.data;

          // Generate recommendations based on performance patterns
          const agentRecommendations = generateAgentRecommendations(agent, perfData, analyticsData);
          recommendations.push(...agentRecommendations);
        }
      } catch (err) {
        console.error(`Failed to get data for agent ${agent}:`, err);
      }
    }

    // Sort by priority and confidence
    return recommendations
      .sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
        if (priorityDiff !== 0) return priorityDiff;
        return b.confidence - a.confidence;
      })
      .slice(0, maxRecommendations);
  };

  const generateAgentRecommendations = (agentName: string, perfData: any, analyticsData: any): Recommendation[] => {
    const recommendations: Recommendation[] = [];
    const summary = perfData.summary;
    const resourceUsage = analyticsData.analytics.resource_usage;

    // Performance-based recommendations
    if (summary.success_rate < 0.9) {
      recommendations.push({
        id: `${agentName}-improve-success-rate`,
        agentName,
        category: 'reliability',
        priority: summary.success_rate < 0.8 ? 'high' : 'medium',
        title: 'Improve Task Success Rate',
        description: 'Success rate is below optimal levels. Consider implementing retry mechanisms and better error handling.',
        impact: 'high',
        effort: 'medium',
        estimatedImprovement: {
          metric: 'Success Rate',
          current: summary.success_rate * 100,
          projected: Math.min(95, summary.success_rate * 100 + 10),
          unit: '%'
        },
        rationale: [
          `Current success rate is ${(summary.success_rate * 100).toFixed(1)}%, below the recommended 90%`,
          `${summary.failed_tasks} tasks have failed in the last 7 days`,
          'Failed tasks often indicate underlying issues with data quality or processing logic'
        ],
        steps: [
          'Analyze failed task logs to identify common failure patterns',
          'Implement exponential backoff retry mechanism for transient failures',
          'Add input validation to catch data quality issues early',
          'Enhance error handling with more specific error messages',
          'Monitor and alert on failure rate thresholds'
        ],
        prerequisites: ['Access to task execution logs', 'Development environment setup'],
        tags: ['reliability', 'error-handling', 'monitoring'],
        confidence: 0.85,
        basedOnData: {
          period: 'Last 7 days',
          sampleSize: summary.total_tasks,
          keyMetrics: {
            'Success Rate': summary.success_rate,
            'Failed Tasks': summary.failed_tasks,
            'Avg Duration': summary.avg_duration_seconds
          }
        }
      });
    }

    if (summary.avg_duration_seconds > 30) {
      recommendations.push({
        id: `${agentName}-optimize-performance`,
        agentName,
        category: 'performance',
        priority: summary.avg_duration_seconds > 60 ? 'high' : 'medium',
        title: 'Optimize Task Execution Time',
        description: 'Tasks are taking longer than expected. Consider optimizing algorithms and resource usage.',
        impact: 'medium',
        effort: 'medium',
        estimatedImprovement: {
          metric: 'Avg Duration',
          current: summary.avg_duration_seconds,
          projected: summary.avg_duration_seconds * 0.7,
          unit: 'seconds'
        },
        rationale: [
          `Average task duration is ${summary.avg_duration_seconds.toFixed(1)}s, above optimal range`,
          'Longer execution times impact overall system throughput',
          'Performance optimization can reduce resource costs'
        ],
        steps: [
          'Profile code to identify performance bottlenecks',
          'Optimize database queries and data processing logic',
          'Implement caching for frequently accessed data',
          'Consider parallel processing for independent operations',
          'Review and optimize LLM call patterns'
        ],
        tags: ['performance', 'optimization', 'throughput'],
        confidence: 0.78,
        basedOnData: {
          period: 'Last 7 days',
          sampleSize: summary.total_tasks,
          keyMetrics: {
            'Avg Duration': summary.avg_duration_seconds,
            'Total Tasks': summary.total_tasks,
            'LLM Calls': summary.total_llm_calls
          }
        }
      });
    }

    if (resourceUsage.avg_memory_usage_mb > 300) {
      recommendations.push({
        id: `${agentName}-optimize-memory`,
        agentName,
        category: 'resource',
        priority: resourceUsage.avg_memory_usage_mb > 500 ? 'high' : 'medium',
        title: 'Reduce Memory Consumption',
        description: 'Memory usage is higher than expected. Optimize data structures and processing patterns.',
        impact: 'medium',
        effort: 'low',
        estimatedImprovement: {
          metric: 'Memory Usage',
          current: resourceUsage.avg_memory_usage_mb,
          projected: resourceUsage.avg_memory_usage_mb * 0.8,
          unit: 'MB'
        },
        rationale: [
          `Average memory usage is ${resourceUsage.avg_memory_usage_mb.toFixed(1)}MB, above recommended limits`,
          'High memory usage can lead to performance degradation',
          'Memory optimization improves scalability'
        ],
        steps: [
          'Profile memory usage to identify memory-intensive operations',
          'Implement streaming processing for large datasets',
          'Optimize data structures and reduce object creation',
          'Add garbage collection tuning if applicable',
          'Consider data pagination for large result sets'
        ],
        tags: ['memory', 'optimization', 'scalability'],
        confidence: 0.72,
        basedOnData: {
          period: 'Last 7 days',
          sampleSize: summary.total_tasks,
          keyMetrics: {
            'Avg Memory': resourceUsage.avg_memory_usage_mb,
            'Peak Memory': resourceUsage.peak_memory_usage_mb || resourceUsage.avg_memory_usage_mb * 1.5
          }
        }
      });
    }

    if (summary.avg_confidence_score < 0.8) {
      recommendations.push({
        id: `${agentName}-improve-confidence`,
        agentName,
        category: 'efficiency',
        priority: 'medium',
        title: 'Enhance Decision Confidence',
        description: 'Agent confidence scores suggest uncertainty in decision-making. Consider additional training or validation.',
        impact: 'medium',
        effort: 'high',
        estimatedImprovement: {
          metric: 'Avg Confidence',
          current: summary.avg_confidence_score * 100,
          projected: Math.min(90, summary.avg_confidence_score * 100 + 15),
          unit: '%'
        },
        rationale: [
          `Average confidence score is ${(summary.avg_confidence_score * 100).toFixed(1)}%, below optimal range`,
          'Low confidence indicates uncertainty in processing decisions',
          'Higher confidence correlates with better task outcomes'
        ],
        steps: [
          'Analyze tasks with low confidence scores',
          'Enhance training data quality and coverage',
          'Implement confidence calibration techniques',
          'Add human-in-the-loop validation for low-confidence decisions',
          'Consider ensemble methods for better decision-making'
        ],
        tags: ['confidence', 'training', 'decision-making'],
        confidence: 0.68,
        basedOnData: {
          period: 'Last 7 days',
          sampleSize: summary.total_tasks,
          keyMetrics: {
            'Avg Confidence': summary.avg_confidence_score,
            'Total Tasks': summary.total_tasks
          }
        }
      });
    }

    return recommendations;
  };

  const handleRecommendationApply = async (recommendation: Recommendation) => {
    // This would implement the actual recommendation application
    console.log('Applying recommendation:', recommendation.id);
    
    if (onRecommendationApply) {
      onRecommendationApply(recommendation);
    }

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const handleRecommendationFeedback = (recommendationId: string, helpful: boolean) => {
    setRecommendations(prev => prev.map(rec => {
      if (rec.id === recommendationId) {
        const feedback = rec.feedback || { helpful: 0, notHelpful: 0, userFeedback: null };
        
        // Remove previous feedback if exists
        if (feedback.userFeedback === 'helpful') feedback.helpful--;
        if (feedback.userFeedback === 'not_helpful') feedback.notHelpful--;
        
        // Add new feedback
        if (helpful) {
          feedback.helpful++;
          feedback.userFeedback = 'helpful';
        } else {
          feedback.notHelpful++;
          feedback.userFeedback = 'not_helpful';
        }
        
        return { ...rec, feedback };
      }
      return rec;
    }));
  };

  const filteredRecommendations = useMemo(() => {
    return recommendations.filter(rec => {
      if (activeCategory !== 'all' && rec.category !== activeCategory) return false;
      if (activePriority !== 'all' && rec.priority !== activePriority) return false;
      return true;
    });
  }, [recommendations, activeCategory, activePriority]);

  const categoryStats = useMemo(() => {
    const stats: Record<string, number> = {};
    recommendations.forEach(rec => {
      stats[rec.category] = (stats[rec.category] || 0) + 1;
    });
    return stats;
  }, [recommendations]);

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-8">
          <div className="text-center">
            <Brain className="w-8 h-8 text-gray-400 mx-auto mb-2 animate-pulse" />
            <p className="text-gray-500">Generating AI-powered recommendations...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Lightbulb className="w-6 h-6 text-yellow-500" />
          <div>
            <h2 className="text-xl font-bold text-gray-900">AI Recommendations</h2>
            <p className="text-gray-600">
              {filteredRecommendations.length} optimization suggestions
              {agentName && ` for ${agentName}`}
            </p>
          </div>
        </div>
        
        <Button onClick={generateRecommendations} variant="outline" disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters and Stats */}
      <div className="flex items-center justify-between">
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList>
            <TabsTrigger value="all">All ({recommendations.length})</TabsTrigger>
            <TabsTrigger value="performance">Performance ({categoryStats.performance || 0})</TabsTrigger>
            <TabsTrigger value="reliability">Reliability ({categoryStats.reliability || 0})</TabsTrigger>
            <TabsTrigger value="efficiency">Efficiency ({categoryStats.efficiency || 0})</TabsTrigger>
            <TabsTrigger value="resource">Resource ({categoryStats.resource || 0})</TabsTrigger>
          </TabsList>
        </Tabs>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Priority:</span>
          <select
            value={activePriority}
            onChange={(e) => setActivePriority(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecommendations.length === 0 ? (
          <Card>
            <CardContent className="p-8">
              <div className="text-center">
                <Lightbulb className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">No recommendations found for the selected filters.</p>
                <p className="text-gray-400 text-sm mt-1">
                  Your agents are performing well! Check back later for new suggestions.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredRecommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation.id}
              recommendation={recommendation}
              onApply={handleRecommendationApply}
              onFeedback={handleRecommendationFeedback}
              enableFeedback={enableFeedback}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RecommendationEngine;
export type { RecommendationEngineProps, Recommendation };