/**
 * Hook for generating and managing recommendations
 * Extracted from RecommendationEngine component
 */

import { useState, useEffect, useCallback } from 'react';
import { agentObservabilityService } from '../../../services/api/agentObservabilityService';
import type { Recommendation } from '../recommendations/RecommendationCard';

export interface UseRecommendationsOptions {
  agentName?: string;
  showAllAgents?: boolean;
  maxRecommendations?: number;
  period?: number;
}

export const useRecommendations = (options: UseRecommendationsOptions) => {
  const { agentName, showAllAgents = false, maxRecommendations = 10, period = 7 } = options;
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const realRecommendations = await generateRealDataRecommendations(
        agentName,
        showAllAgents,
        period,
        maxRecommendations
      );
      setRecommendations(realRecommendations);
    } catch (err) {
      console.error('Failed to generate recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  }, [agentName, showAllAgents, period, maxRecommendations]);

  useEffect(() => {
    generateRecommendations();
  }, [generateRecommendations]);

  const updateRecommendationFeedback = useCallback((recommendationId: string, helpful: boolean) => {
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
  }, []);

  return {
    recommendations,
    loading,
    error,
    refresh: generateRecommendations,
    updateFeedback: updateRecommendationFeedback
  };
};

async function generateRealDataRecommendations(
  agentName: string | undefined,
  showAllAgents: boolean,
  period: number,
  maxRecommendations: number
): Promise<Recommendation[]> {
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
        agentObservabilityService.getAgentPerformance(agent, period),
        agentObservabilityService.getAgentAnalytics(agent, period)
      ]);

      if (performance.success && analytics.success) {
        const perfData = performance.data;
        const analyticsData = analytics.data;

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
}

function generateAgentRecommendations(agentName: string, perfData: any, analyticsData: any): Recommendation[] {
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
}