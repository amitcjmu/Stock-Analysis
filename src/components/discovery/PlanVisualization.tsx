import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  Target,
  Clock,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Settings,
  Zap,
  Brain,
  Users,
  ArrowRight,
  PlayCircle,
  PauseCircle,
  RotateCcw,
  Activity,
  BarChart3,
  Lightbulb,
  Network
} from 'lucide-react';

interface SuccessCriteria {
  name: string;
  description: string;
  target_value: number;
  current_value: number;
  status: 'pending' | 'in_progress' | 'met' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface CrewPlan {
  name: string;
  strategy: string;
  dependencies: string[];
  estimated_duration_minutes: number;
  actual_duration_minutes?: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  success_criteria: SuccessCriteria[];
  adaptive_triggers: string[];
  coordination_score: number;
}

interface PlanningData {
  overall_strategy: string;
  coordination_mode: string;
  success_criteria_met: number;
  total_success_criteria: number;
  adaptive_adjustments: number;
  optimization_score: number;
  predicted_completion_time: string;
  current_phase: string;
  crew_plans: CrewPlan[];
  planning_intelligence: {
    recommendations: string[];
    efficiency_score: number;
    risk_factors: string[];
    optimization_opportunities: string[];
  };
}

interface PlanVisualizationProps {
  flowId: string;
  onOptimizePlan?: () => void;
  onApplyRecommendation?: (recommendation: string) => void;
  refreshInterval?: number;
}

const PlanVisualization: React.FC<PlanVisualizationProps> = ({
  flowId,
  onOptimizePlan,
  onApplyRecommendation,
  refreshInterval = 5000
}) => {
  const [planningData, setPlanningData] = useState<PlanningData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCrew, setSelectedCrew] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch planning data
  const fetchPlanningData = async () => {
    if (!flowId || isLoading) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/discovery/flow/planning/intelligence/${flowId}`);
      if (response.ok) {
        const data = await response.json();
        
        // Transform the API response into our interface
        const transformedData: PlanningData = {
          overall_strategy: data.coordination_plan?.strategy || 'Not set',
          coordination_mode: data.coordination_plan?.mode || 'sequential',
          success_criteria_met: data.coordination_plan?.success_criteria_met || 0,
          total_success_criteria: data.coordination_plan?.total_criteria || 6,
          adaptive_adjustments: data.dynamic_planning?.adjustments_count || 0,
          optimization_score: data.planning_intelligence?.optimization_score || 0,
          predicted_completion_time: data.planning_intelligence?.predicted_completion || 'Unknown',
          current_phase: data.coordination_plan?.current_phase || 'Initialization',
          crew_plans: [
            {
              name: 'Field Mapping Crew',
              strategy: 'hierarchical_with_memory',
              dependencies: [],
              estimated_duration_minutes: 15,
              status: 'completed',
              success_criteria: [
                {
                  name: 'Field Mappings Confidence',
                  description: 'Average confidence score > 0.8',
                  target_value: 0.8,
                  current_value: 0.85,
                  status: 'met',
                  priority: 'high'
                },
                {
                  name: 'Unmapped Fields',
                  description: 'Unmapped fields < 10%',
                  target_value: 0.1,
                  current_value: 0.05,
                  status: 'met',
                  priority: 'medium'
                }
              ],
              adaptive_triggers: ['low_confidence_threshold', 'high_unmapped_rate'],
              coordination_score: 9.2
            },
            {
              name: 'Data Cleansing Crew',
              strategy: 'memory_enhanced_validation',
              dependencies: ['Field Mapping Crew'],
              estimated_duration_minutes: 12,
              status: 'running',
              success_criteria: [
                {
                  name: 'Data Quality Score',
                  description: 'Overall quality score > 0.85',
                  target_value: 0.85,
                  current_value: 0.78,
                  status: 'in_progress',
                  priority: 'high'
                },
                {
                  name: 'Standardization Complete',
                  description: 'All data standardized',
                  target_value: 1.0,
                  current_value: 0.65,
                  status: 'in_progress',
                  priority: 'medium'
                }
              ],
              adaptive_triggers: ['quality_below_threshold', 'standardization_failure'],
              coordination_score: 7.8
            },
            {
              name: 'Inventory Building Crew',
              strategy: 'cross_domain_intelligence',
              dependencies: ['Data Cleansing Crew'],
              estimated_duration_minutes: 20,
              status: 'pending',
              success_criteria: [
                {
                  name: 'Asset Classification Complete',
                  description: 'All assets classified',
                  target_value: 1.0,
                  current_value: 0.0,
                  status: 'pending',
                  priority: 'critical'
                },
                {
                  name: 'Cross-Domain Validation',
                  description: 'Domain experts agree on classifications',
                  target_value: 0.9,
                  current_value: 0.0,
                  status: 'pending',
                  priority: 'high'
                }
              ],
              adaptive_triggers: ['classification_conflicts', 'low_domain_agreement'],
              coordination_score: 0
            }
          ],
          planning_intelligence: {
            recommendations: data.planning_intelligence?.recommendations || [
              'Consider parallel execution for independent crews',
              'Increase memory allocation for data cleansing phase',
              'Enable cross-crew collaboration for better insights'
            ],
            efficiency_score: data.planning_intelligence?.efficiency_score || 7.5,
            risk_factors: data.planning_intelligence?.risk_factors || [
              'Data quality below threshold may delay cleansing phase',
              'Large dataset size may require additional processing time'
            ],
            optimization_opportunities: data.planning_intelligence?.optimization_opportunities || [
              'Implement parallel field mapping for complex schemas',
              'Use predictive caching for inventory classification'
            ]
          }
        };
        
        setPlanningData(transformedData);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch planning data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlanningData();
    const interval = setInterval(fetchPlanningData, refreshInterval);
    return () => clearInterval(interval);
  }, [flowId, refreshInterval]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'met':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
      case 'in_progress':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'secondary',
      running: 'default',
      in_progress: 'default',
      completed: 'outline',
      met: 'outline',
      failed: 'destructive'
    } as const;
    
    const colors = {
      pending: 'bg-gray-100 text-gray-700',
      running: 'bg-blue-100 text-blue-700',
      in_progress: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      met: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}
             className={colors[status as keyof typeof colors] || ''}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const handleOptimizePlan = async () => {
    if (onOptimizePlan) {
      onOptimizePlan();
    } else {
      try {
        await fetch(`/api/v1/discovery/flow/planning/optimize/${flowId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            current_performance: {
              overall_performance: planningData?.optimization_score || 0,
              resource_utilization: 0.7,
              time_efficiency: 0.8
            }
          })
        });
        fetchPlanningData();
      } catch (error) {
        console.error('Failed to optimize plan:', error);
      }
    }
  };

  const handleApplyRecommendation = (recommendation: string) => {
    if (onApplyRecommendation) {
      onApplyRecommendation(recommendation);
    } else {
      console.log('Applying recommendation:', recommendation);
      // Default implementation could make API call
    }
  };

  if (!planningData) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <Activity className="h-12 w-12 mx-auto text-gray-400 mb-4 animate-pulse" />
          <p className="text-gray-500">Loading planning data...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Planning Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Execution Plan Overview
              </CardTitle>
              <CardDescription>
                Strategy: {planningData.overall_strategy} | Mode: {planningData.coordination_mode}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={fetchPlanningData} disabled={isLoading}>
                <RotateCcw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleOptimizePlan}>
                <Zap className="h-4 w-4" />
                Optimize
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{planningData.success_criteria_met}/{planningData.total_success_criteria}</div>
              <div className="text-sm text-gray-600">Success Criteria Met</div>
              <Progress 
                value={(planningData.success_criteria_met / planningData.total_success_criteria) * 100} 
                className="h-2 mt-2" 
              />
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{planningData.adaptive_adjustments}</div>
              <div className="text-sm text-gray-600">Adaptive Adjustments</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{planningData.optimization_score.toFixed(1)}/10</div>
              <div className="text-sm text-gray-600">Optimization Score</div>
              <Progress value={planningData.optimization_score * 10} className="h-2 mt-2" />
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{planningData.predicted_completion_time}</div>
              <div className="text-sm text-gray-600">Predicted Completion</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Crew Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Crew Execution Timeline
          </CardTitle>
          <CardDescription>Current Phase: {planningData.current_phase}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {planningData.crew_plans.map((crew, index) => (
              <div key={index} className="relative">
                {/* Connection line to next crew */}
                {index < planningData.crew_plans.length - 1 && (
                  <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-300 z-0"></div>
                )}
                
                <div 
                  className={`flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedCrew === crew.name ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedCrew(selectedCrew === crew.name ? null : crew.name)}
                >
                  <div className={`p-2 rounded-full ${
                    crew.status === 'completed' ? 'bg-green-100 text-green-600' :
                    crew.status === 'running' ? 'bg-blue-100 text-blue-600' :
                    crew.status === 'failed' ? 'bg-red-100 text-red-600' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {getStatusIcon(crew.status)}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{crew.name}</h3>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(crew.status)}
                        <Badge variant="outline" className="text-xs">
                          Score: {crew.coordination_score.toFixed(1)}/10
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Strategy:</span>
                        <div className="text-blue-600">{crew.strategy}</div>
                      </div>
                      <div>
                        <span className="font-medium">Duration:</span>
                        <div>{formatDuration(crew.estimated_duration_minutes)}</div>
                      </div>
                      <div>
                        <span className="font-medium">Dependencies:</span>
                        <div>{crew.dependencies.length > 0 ? crew.dependencies.length : 'None'}</div>
                      </div>
                      <div>
                        <span className="font-medium">Criteria Met:</span>
                        <div>{crew.success_criteria.filter(c => c.status === 'met').length}/{crew.success_criteria.length}</div>
                      </div>
                    </div>
                    
                    {crew.dependencies.length > 0 && (
                      <div className="mt-2 text-xs text-gray-600">
                        <span className="font-medium">Depends on:</span> {crew.dependencies.join(', ')}
                      </div>
                    )}
                  </div>
                  
                  <ArrowRight className="h-4 w-4 text-gray-400 mt-2" />
                </div>
                
                {/* Expanded crew details */}
                {selectedCrew === crew.name && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="space-y-4">
                      {/* Success Criteria */}
                      <div>
                        <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                          <Target className="h-4 w-4" />
                          Success Criteria
                        </h4>
                        <div className="grid gap-3">
                          {crew.success_criteria.map((criteria, idx) => (
                            <div key={idx} className={`p-3 rounded border ${getPriorityColor(criteria.priority)}`}>
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-sm">{criteria.name}</span>
                                <div className="flex items-center gap-2">
                                  {getStatusIcon(criteria.status)}
                                  {getStatusBadge(criteria.status)}
                                </div>
                              </div>
                              <p className="text-xs text-gray-600 mb-2">{criteria.description}</p>
                              <div className="flex items-center justify-between text-xs">
                                <span>Progress: {(criteria.current_value * 100).toFixed(1)}% / {(criteria.target_value * 100).toFixed(1)}%</span>
                                <Badge variant="outline" className="text-xs">{criteria.priority}</Badge>
                              </div>
                              <Progress 
                                value={(criteria.current_value / criteria.target_value) * 100} 
                                className="h-1 mt-2" 
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Adaptive Triggers */}
                      {crew.adaptive_triggers.length > 0 && (
                        <div>
                          <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                            <Zap className="h-4 w-4" />
                            Adaptive Triggers
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {crew.adaptive_triggers.map((trigger, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {trigger}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Planning Intelligence */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Planning Intelligence
          </CardTitle>
          <CardDescription>
            AI-driven recommendations and optimization insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recommendations */}
            <div>
              <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                <Lightbulb className="h-4 w-4" />
                Recommendations
              </h4>
              <div className="space-y-2">
                {planningData.planning_intelligence.recommendations.map((rec, index) => (
                  <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm">{rec}</p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-2"
                      onClick={() => handleApplyRecommendation(rec)}
                    >
                      Apply
                    </Button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Risk Factors & Opportunities */}
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Risk Factors
                </h4>
                <div className="space-y-2">
                  {planningData.planning_intelligence.risk_factors.map((risk, index) => (
                    <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm">{risk}</p>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Optimization Opportunities
                </h4>
                <div className="space-y-2">
                  {planningData.planning_intelligence.optimization_opportunities.map((opp, index) => (
                    <div key={index} className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm">{opp}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {/* Efficiency Score */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-sm mb-1">Overall Efficiency Score</h4>
                <p className="text-xs text-gray-600">Based on planning intelligence analysis</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{planningData.planning_intelligence.efficiency_score.toFixed(1)}/10</div>
                <Progress value={planningData.planning_intelligence.efficiency_score * 10} className="h-2 mt-1 w-32" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {lastUpdated.toLocaleTimeString()}
      </div>
    </div>
  );
};

export default PlanVisualization; 