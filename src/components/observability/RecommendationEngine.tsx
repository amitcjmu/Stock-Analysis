/**
 * Recommendation Engine Component
 * AI-powered fine-tuning suggestions based on performance data
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

import React from 'react'
import type { useState } from 'react'
import { useMemo } from 'react'
import { Lightbulb, Brain, RefreshCw, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import type { TabsContent } from '../ui/tabs'
import { Tabs, TabsList, TabsTrigger } from '../ui/tabs'
import { useRecommendations } from './hooks/useRecommendations';
import { RecommendationCard } from './recommendations/RecommendationCard';
import type { Recommendation } from './recommendations/RecommendationCard';

// Types moved to recommendations/RecommendationCard.tsx

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

// RecommendationCard component moved to recommendations/RecommendationCard.tsx

const RecommendationEngine: React.FC<RecommendationEngineProps> = ({
  agentName,
  showAllAgents = false,
  maxRecommendations = 10,
  enableFeedback = true,
  onRecommendationApply,
  className = ''
}) => {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [activePriority, setActivePriority] = useState<string>('all');

  // Use the custom hook for recommendations
  const { recommendations, loading, error, refresh, updateFeedback } = useRecommendations({
    agentName,
    showAllAgents,
    maxRecommendations
  });

  const handleRecommendationApply = async (recommendation: Recommendation) => {
    console.log('Applying recommendation:', recommendation.id);
    
    if (onRecommendationApply) {
      onRecommendationApply(recommendation);
    }

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const handleRecommendationFeedback = (recommendationId: string, helpful: boolean) => {
    updateFeedback(recommendationId, helpful);
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
        
        <Button onClick={refresh} variant="outline" disabled={loading}>
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