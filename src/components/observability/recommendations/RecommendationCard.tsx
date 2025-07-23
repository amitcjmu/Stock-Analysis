/**
 * RecommendationCard component extracted from RecommendationEngine
 * Displays a single recommendation with expandable details
 */

import React from 'react'
import type { useState } from 'react'
import { 
  TrendingUp, CheckCircle, Zap, Target, Brain, 
  ArrowRight, X, RefreshCw, ThumbsUp, ThumbsDown, AlertTriangle 
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Progress } from '../../ui/progress';
import type { IMPACT_CONFIG, RECOMMENDATION_CATEGORIES } from '../utils/constants'
import { PRIORITY_CONFIG, EFFORT_CONFIG } from '../utils/constants'

export interface Recommendation {
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
  confidence: number;
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

export interface RecommendationCardProps {
  recommendation: Recommendation;
  onApply?: (recommendation: Recommendation) => void;
  onFeedback?: (recommendationId: string, helpful: boolean) => void;
  enableFeedback?: boolean;
}

const categoryIcons = {
  performance: <TrendingUp className="w-5 h-5 text-blue-500" />,
  reliability: <CheckCircle className="w-5 h-5 text-green-500" />,
  efficiency: <Zap className="w-5 h-5 text-purple-500" />,
  resource: <Target className="w-5 h-5 text-orange-500" />,
  configuration: <Brain className="w-5 h-5 text-indigo-500" />
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onApply,
  onFeedback,
  enableFeedback = false
}) => {
  const [expanded, setExpanded] = useState(false);
  const [applying, setApplying] = useState(false);

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
    ((recommendation.estimatedImprovement.projected - recommendation.estimatedImprovement.current) / 
     recommendation.estimatedImprovement.current * 100) : 0;

  return (
    <Card className={`border-l-4 transition-all duration-200 ${PRIORITY_CONFIG[recommendation.priority].color}`}>
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
                <Badge variant="outline" className={`text-xs ${IMPACT_CONFIG[recommendation.impact].color}`}>
                  {recommendation.impact} impact
                </Badge>
                <Badge variant="outline" className={`text-xs ${EFFORT_CONFIG[recommendation.effort].color}`}>
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
            value={Math.min(100, (recommendation.estimatedImprovement.projected / 
                  (recommendation.estimatedImprovement.current * 2)) * 100)} 
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