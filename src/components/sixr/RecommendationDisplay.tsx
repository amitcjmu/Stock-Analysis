import React from 'react'
import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { ChevronDown, ChevronUp, Info } from 'lucide-react'
import { CheckCircle, AlertTriangle, TrendingUp, Clock, DollarSign, Shield, Zap, Star, Target, ArrowRight } from 'lucide-react'

export interface SixRStrategyScore {
  strategy: string;
  score: number;
  confidence: number;
  rationale: string[];
  risk_factors: string[];
  benefits: string[];
}

export interface SixRRecommendation {
  recommended_strategy: string;
  confidence_score: number;
  strategy_scores: SixRStrategyScore[];
  key_factors: string[];
  assumptions: string[];
  next_steps: string[];
  estimated_effort?: string;
  estimated_timeline?: string;
  estimated_cost_impact?: string;
}

interface RecommendationDisplayProps {
  recommendation: SixRRecommendation;
  previousRecommendation?: SixRRecommendation;
  iterationNumber?: number;
  onAccept?: () => void;
  onReject?: () => void;
  onIterate?: () => void;
  showComparison?: boolean;
  className?: string;
}

const strategyConfig = {
  rehost: {
    label: 'Rehost',
    description: 'Lift and shift with minimal changes',
    icon: '🚀',
    color: 'bg-blue-500',
    modernization: 'Minimal'
  },
  replatform: {
    label: 'Replatform', 
    description: 'Lift, tinker, and shift with basic optimizations',
    icon: '⚡',
    color: 'bg-green-500',
    modernization: 'Minimal'
  },
  refactor: {
    label: 'Refactor',
    description: 'Re-architect with significant code changes',
    icon: '🔧',
    color: 'bg-yellow-500',
    modernization: 'High'
  },
  rearchitect: {
    label: 'Rearchitect',
    description: 'Rebuild with new cloud-native architecture',
    icon: '🏗️',
    color: 'bg-purple-500',
    modernization: 'High'
  },
  rewrite: {
    label: 'Rewrite',
    description: 'Complete rebuild with cloud-native services',
    icon: '✨',
    color: 'bg-indigo-500',
    modernization: 'High'
  },
  replace: {
    label: 'Replace',
    description: 'Replace with alternative solution',
    icon: '🔄',
    color: 'bg-orange-500',
    modernization: 'Variable'
  },
  retire: {
    label: 'Retire',
    description: 'Decommission the application',
    icon: '🗑️',
    color: 'bg-red-500',
    modernization: 'N/A'
  }
};

const getConfidenceLevel = (score: number): { level: string; color: string; icon: React.ReactNode } => {
  if (score >= 0.8) return { 
    level: 'High', 
    color: 'text-green-600 bg-green-50 border-green-200', 
    icon: <CheckCircle className="h-4 w-4" />
  };
  if (score >= 0.6) return { 
    level: 'Medium', 
    color: 'text-yellow-600 bg-yellow-50 border-yellow-200', 
    icon: <Star className="h-4 w-4" />
  };
  if (score >= 0.4) return { 
    level: 'Low', 
    color: 'text-orange-600 bg-orange-50 border-orange-200', 
    icon: <AlertTriangle className="h-4 w-4" />
  };
  return { 
    level: 'Very Low', 
    color: 'text-red-600 bg-red-50 border-red-200', 
    icon: <AlertTriangle className="h-4 w-4" />
  };
};

const getEffortIcon = (effort: string) => {
  switch (effort?.toLowerCase()) {
    case 'low': return <Zap className="h-4 w-4 text-green-500" />;
    case 'medium': return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'high': return <TrendingUp className="h-4 w-4 text-orange-500" />;
    case 'very_high': return <Target className="h-4 w-4 text-red-500" />;
    default: return <Clock className="h-4 w-4 text-gray-500" />;
  }
};

export const RecommendationDisplay: React.FC<RecommendationDisplayProps> = ({
  recommendation,
  previousRecommendation,
  iterationNumber,
  onAccept,
  onReject,
  onIterate,
  showComparison = false,
  className = ''
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [selectedTab, setSelectedTab] = useState('recommendation');

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const recommendedStrategy = strategyConfig[recommendation.recommended_strategy as keyof typeof strategyConfig];
  const confidence = getConfidenceLevel(recommendation.confidence_score);

  // Sort strategy scores by score
  const sortedStrategies = [...recommendation.strategy_scores].sort((a, b) => b.score - a.score);

  const renderStrategyCard = (strategyScore: SixRStrategyScore, isRecommended: boolean = false) => {
    const config = strategyConfig[strategyScore.strategy as keyof typeof strategyConfig];
    if (!config) return null;

    return (
      <div 
        key={strategyScore.strategy}
        className={`
          p-4 border rounded-lg transition-all
          ${isRecommended ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300'}
        `}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{config.icon}</span>
            <div>
              <h4 className={`font-semibold ${isRecommended ? 'text-blue-900' : 'text-gray-900'}`}>
                {config.label}
                {isRecommended && <Badge className="ml-2 bg-blue-500">Recommended</Badge>}
              </h4>
              <p className="text-sm text-gray-600">{config.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">{strategyScore.score}</div>
            <div className="text-xs text-gray-500">Score</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Confidence:</span>
            <span className="font-medium">{Math.round(strategyScore.confidence * 100)}%</span>
          </div>
          <Progress value={strategyScore.score} className="h-2" />
          
          <div className="grid grid-cols-2 gap-4 mt-3 text-xs">
            <div>
              <span className="font-medium text-green-700">Benefits:</span>
              <ul className="mt-1 space-y-1">
                {strategyScore.benefits.slice(0, 2).map((benefit, idx) => (
                  <li key={idx} className="text-green-600">• {benefit}</li>
                ))}
              </ul>
            </div>
            <div>
              <span className="font-medium text-red-700">Risks:</span>
              <ul className="mt-1 space-y-1">
                {strategyScore.risk_factors.slice(0, 2).map((risk, idx) => (
                  <li key={idx} className="text-red-600">• {risk}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderComparisonView = () => {
    if (!previousRecommendation) return null;

    const prevStrategy = strategyConfig[previousRecommendation.recommended_strategy as keyof typeof strategyConfig];
    const currentStrategy = strategyConfig[recommendation.recommended_strategy as keyof typeof strategyConfig];
    const confidenceChange = recommendation.confidence_score - previousRecommendation.confidence_score;

    return (
      <Card className="border-orange-200 bg-orange-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center space-x-2">
            <ArrowRight className="h-5 w-5 text-orange-600" />
            <span>Iteration Comparison</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-white rounded border">
              <div className="text-sm text-gray-600 mb-1">Previous</div>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-xl">{prevStrategy?.icon}</span>
                <span className="font-semibold">{prevStrategy?.label}</span>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Confidence: {Math.round(previousRecommendation.confidence_score * 100)}%
              </div>
            </div>
            <div className="text-center p-3 bg-white rounded border border-blue-200">
              <div className="text-sm text-gray-600 mb-1">Current</div>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-xl">{currentStrategy?.icon}</span>
                <span className="font-semibold">{currentStrategy?.label}</span>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Confidence: {Math.round(recommendation.confidence_score * 100)}%
                <span className={`ml-1 ${confidenceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ({confidenceChange >= 0 ? '+' : ''}{Math.round(confidenceChange * 100)}%)
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main Recommendation Card */}
      <Card className="border-blue-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-4xl">{recommendedStrategy?.icon}</span>
              <div>
                <CardTitle className="text-2xl text-blue-900">
                  {recommendedStrategy?.label}
                </CardTitle>
                <CardDescription className="text-blue-700">
                  {recommendedStrategy?.description}
                </CardDescription>
                {iterationNumber && (
                  <Badge variant="outline" className="mt-2">
                    Iteration {iterationNumber}
                  </Badge>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className={`inline-flex items-center space-x-2 px-3 py-2 rounded-lg border ${confidence.color}`}>
                {confidence.icon}
                <span className="font-semibold">{confidence.level} Confidence</span>
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {Math.round(recommendation.confidence_score * 100)}% confidence score
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {recommendation.estimated_effort && (
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                {getEffortIcon(recommendation.estimated_effort)}
                <div>
                  <div className="text-sm font-medium">Effort Level</div>
                  <div className="text-xs text-gray-600 capitalize">{recommendation.estimated_effort}</div>
                </div>
              </div>
            )}
            {recommendation.estimated_timeline && (
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                <Clock className="h-4 w-4 text-blue-500" />
                <div>
                  <div className="text-sm font-medium">Timeline</div>
                  <div className="text-xs text-gray-600">{recommendation.estimated_timeline}</div>
                </div>
              </div>
            )}
            {recommendation.estimated_cost_impact && (
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                <DollarSign className="h-4 w-4 text-green-500" />
                <div>
                  <div className="text-sm font-medium">Cost Impact</div>
                  <div className="text-xs text-gray-600 capitalize">{recommendation.estimated_cost_impact}</div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              {onAccept && (
                <Button onClick={onAccept} className="bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Accept Recommendation
                </Button>
              )}
              {onIterate && (
                <Button variant="outline" onClick={onIterate}>
                  <Target className="h-4 w-4 mr-2" />
                  Refine Analysis
                </Button>
              )}
            </div>
            {onReject && (
              <Button variant="destructive" onClick={onReject}>
                <AlertTriangle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Comparison View */}
      {showComparison && renderComparisonView()}

      {/* Detailed Analysis Tabs */}
      <Card className="border-blue-100 bg-blue-50/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Info className="h-5 w-5 text-blue-600" />
            <span>Detailed AI Agent Analysis</span>
          </CardTitle>
          <CardDescription>
            Comprehensive reasoning, alternative strategies, and implementation guidance from AI agents
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="recommendation">All Strategies</TabsTrigger>
              <TabsTrigger value="rationale">Rationale</TabsTrigger>
              <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
              <TabsTrigger value="next-steps">Next Steps</TabsTrigger>
            </TabsList>

        <TabsContent value="recommendation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Comparison</CardTitle>
              <CardDescription>
                All 6R strategies ranked by suitability for your application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {sortedStrategies.map((strategy, index) => 
                renderStrategyCard(strategy, strategy.strategy === recommendation.recommended_strategy)
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rationale" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Decision Rationale</CardTitle>
              <CardDescription>
                Key factors that influenced the recommendation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2 flex items-center">
                  <Info className="h-4 w-4 mr-2 text-blue-500" />
                  Key Decision Factors
                </h4>
                <ul className="space-y-1">
                  {recommendation.key_factors.map((factor, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-blue-500 mt-1">•</span>
                      <span className="text-sm">{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Detailed Rationale</h4>
                <div className="space-y-2">
                  {sortedStrategies[0]?.rationale.map((reason, index) => (
                    <div key={index} className="p-3 bg-blue-50 rounded border-l-4 border-blue-500">
                      <p className="text-sm">{reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assumptions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Assumptions</CardTitle>
              <CardDescription>
                Assumptions made during the analysis process
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recommendation.assumptions.map((assumption, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded border-l-4 border-yellow-400">
                    <Shield className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm">{assumption}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="next-steps" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recommended Next Steps</CardTitle>
              <CardDescription>
                Action items to proceed with the recommended strategy
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recommendation.next_steps.map((step, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded border-l-4 border-green-400">
                    <div className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm">{step}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default RecommendationDisplay; 