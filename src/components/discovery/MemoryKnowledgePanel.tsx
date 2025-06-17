import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Brain,
  Database,
  Lightbulb,
  TrendingUp,
  Network,
  Search,
  RefreshCw,
  BarChart3,
  Activity,
  Zap,
  Users,
  Target,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

interface MemoryMetrics {
  total_size_mb: number;
  used_size_mb: number;
  utilization_percentage: number;
  active_insights: number;
  cross_crew_insights: number;
  learning_patterns: number;
  last_cleanup: string;
  performance_score: number;
}

interface KnowledgeBaseMetrics {
  domain: string;
  sources_loaded: number;
  total_documents: number;
  utilization_score: number;
  last_updated: string;
  effectiveness_rating: number;
  crew_usage: string[];
}

interface LearningEffectiveness {
  field_mapping_accuracy: number;
  asset_classification_accuracy: number;
  dependency_detection_accuracy: number;
  user_feedback_integration: number;
  improvement_trend: number;
  confidence_threshold: number;
}

interface CrossCrewInsight {
  source_crew: string;
  target_crew: string;
  insight_type: string;
  confidence_score: number;
  usage_count: number;
  created_at: string;
  effectiveness_score: number;
}

interface MemoryKnowledgePanelProps {
  flowId: string;
  refreshInterval?: number;
  onOptimize?: () => void;
}

const MemoryKnowledgePanel: React.FC<MemoryKnowledgePanelProps> = ({
  flowId,
  refreshInterval = 10000,
  onOptimize
}) => {
  const [activeTab, setActiveTab] = useState('memory');
  const [memoryMetrics, setMemoryMetrics] = useState<MemoryMetrics | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseMetrics[]>([]);
  const [learningEffectiveness, setLearningEffectiveness] = useState<LearningEffectiveness | null>(null);
  const [crossCrewInsights, setCrossCrewInsights] = useState<CrossCrewInsight[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch memory and knowledge data
  const fetchData = async () => {
    if (!flowId || isLoading) return;
    
    setIsLoading(true);
    try {
      // Fetch memory analytics
      const memoryResponse = await fetch(`/api/v1/discovery/flow/memory/analytics/${flowId}?report_type=detailed`);
      if (memoryResponse.ok) {
        const memoryData = await memoryResponse.json();
        if (memoryData.report) {
          setMemoryMetrics({
            total_size_mb: memoryData.report.memory_usage?.total_size_mb || 0,
            used_size_mb: memoryData.report.memory_usage?.used_size_mb || 0,
            utilization_percentage: memoryData.report.memory_usage?.utilization_percentage || 0,
            active_insights: memoryData.report.active_insights || 0,
            cross_crew_insights: memoryData.report.cross_domain_insights?.count || 0,
            learning_patterns: memoryData.report.learning_patterns?.count || 0,
            last_cleanup: memoryData.report.last_cleanup || new Date().toISOString(),
            performance_score: memoryData.report.performance_score || 0
          });

          if (memoryData.report.cross_domain_insights?.insights) {
            setCrossCrewInsights(memoryData.report.cross_domain_insights.insights.map((insight: any) => ({
              source_crew: insight.source || 'Unknown',
              target_crew: insight.target || 'Unknown',
              insight_type: insight.type || 'general',
              confidence_score: insight.confidence || 0,
              usage_count: insight.usage_count || 0,
              created_at: insight.timestamp || new Date().toISOString(),
              effectiveness_score: insight.effectiveness || 0
            })));
          }

          if (memoryData.report.learning_effectiveness) {
            setLearningEffectiveness({
              field_mapping_accuracy: memoryData.report.learning_effectiveness.field_mapping || 0,
              asset_classification_accuracy: memoryData.report.learning_effectiveness.asset_classification || 0,
              dependency_detection_accuracy: memoryData.report.learning_effectiveness.dependency_detection || 0,
              user_feedback_integration: memoryData.report.learning_effectiveness.user_feedback || 0,
              improvement_trend: memoryData.report.learning_effectiveness.trend || 0,
              confidence_threshold: memoryData.report.learning_effectiveness.threshold || 0.8
            });
          }
        }
      }

      // Fetch knowledge base status
      const knowledgeResponse = await fetch(`/api/v1/discovery/flow/knowledge/status/${flowId}`);
      if (knowledgeResponse.ok) {
        const knowledgeData = await knowledgeResponse.json();
        if (knowledgeData.knowledge_bases) {
          const kbMetrics = Object.entries(knowledgeData.knowledge_bases).map(([domain, data]: [string, any]) => ({
            domain,
            sources_loaded: data.sources_loaded || 0,
            total_documents: data.total_documents || 0,
            utilization_score: data.utilization_score || 0,
            last_updated: data.last_updated || new Date().toISOString(),
            effectiveness_rating: data.effectiveness_rating || 0,
            crew_usage: data.crew_usage || []
          }));
          setKnowledgeBases(kbMetrics);
        }
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch memory/knowledge data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [flowId, refreshInterval]);

  const handleOptimize = async () => {
    if (onOptimize) {
      onOptimize();
    } else {
      // Default optimization call
      try {
        await fetch(`/api/v1/discovery/flow/memory/optimize/${flowId}`, { method: 'POST' });
        fetchData(); // Refresh after optimization
      } catch (error) {
        console.error('Failed to optimize memory:', error);
      }
    }
  };

  const formatSize = (sizeInMB: number): string => {
    if (sizeInMB < 1) return `${(sizeInMB * 1024).toFixed(1)} KB`;
    if (sizeInMB < 1024) return `${sizeInMB.toFixed(1)} MB`;
    return `${(sizeInMB / 1024).toFixed(1)} GB`;
  };

  const getUtilizationColor = (percentage: number): string => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getEffectivenessIcon = (score: number) => {
    if (score >= 8) return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (score >= 6) return <Activity className="h-4 w-4 text-yellow-500" />;
    return <AlertTriangle className="h-4 w-4 text-red-500" />;
  };

  const MemoryOverview = () => (
    <div className="space-y-6">
      {/* Memory Usage Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Database className="h-4 w-4" />
              Memory Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatSize(memoryMetrics?.used_size_mb || 0)}</div>
            <p className="text-xs text-gray-600">of {formatSize(memoryMetrics?.total_size_mb || 0)}</p>
            <Progress 
              value={memoryMetrics?.utilization_percentage || 0} 
              className="h-2 mt-2" 
            />
            <p className={`text-xs mt-1 ${getUtilizationColor(memoryMetrics?.utilization_percentage || 0)}`}>
              {(memoryMetrics?.utilization_percentage || 0).toFixed(1)}% used
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Active Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{memoryMetrics?.active_insights || 0}</div>
            <p className="text-xs text-gray-600">total insights stored</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Network className="h-4 w-4" />
              Cross-Crew Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{memoryMetrics?.cross_crew_insights || 0}</div>
            <p className="text-xs text-gray-600">shared between crews</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Performance Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(memoryMetrics?.performance_score || 0).toFixed(1)}/10</div>
            <Progress 
              value={(memoryMetrics?.performance_score || 0) * 10} 
              className="h-2 mt-2" 
            />
          </CardContent>
        </Card>
      </div>

      {/* Memory Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Memory Management
            </CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={fetchData} disabled={isLoading}>
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleOptimize}>
                <Zap className="h-4 w-4" />
                Optimize
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium mb-2">Learning Patterns</div>
              <div className="text-2xl font-bold">{memoryMetrics?.learning_patterns || 0}</div>
              <p className="text-gray-600">patterns identified</p>
            </div>
            <div>
              <div className="font-medium mb-2">Last Cleanup</div>
              <div className="text-lg">
                {memoryMetrics?.last_cleanup ? 
                  new Date(memoryMetrics.last_cleanup).toLocaleDateString() : 'Never'
                }
              </div>
              <p className="text-gray-600">optimization run</p>
            </div>
            <div>
              <div className="font-medium mb-2">Memory Health</div>
              <div className="flex items-center gap-2">
                {getEffectivenessIcon(memoryMetrics?.performance_score || 0)}
                <span className="text-lg">
                  {memoryMetrics?.performance_score && memoryMetrics.performance_score >= 8 ? 'Excellent' :
                   memoryMetrics?.performance_score && memoryMetrics.performance_score >= 6 ? 'Good' : 'Needs Attention'}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const KnowledgeBasesOverview = () => (
    <div className="space-y-4">
      {knowledgeBases.map((kb, index) => (
        <Card key={index}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg capitalize flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                {kb.domain.replace('_', ' ')} Knowledge Base
              </CardTitle>
              <div className="flex items-center gap-2">
                {getEffectivenessIcon(kb.effectiveness_rating)}
                <Badge variant="outline">
                  {kb.effectiveness_rating.toFixed(1)}/10
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="font-medium mb-1">Sources Loaded</div>
                <div className="text-xl font-bold">{kb.sources_loaded}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Total Documents</div>
                <div className="text-xl font-bold">{kb.total_documents}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Utilization Score</div>
                <div className="text-xl font-bold">{kb.utilization_score.toFixed(1)}/10</div>
                <Progress value={kb.utilization_score * 10} className="h-1 mt-1" />
              </div>
              <div>
                <div className="font-medium mb-1">Last Updated</div>
                <div className="text-sm">{new Date(kb.last_updated).toLocaleDateString()}</div>
              </div>
            </div>
            
            {kb.crew_usage.length > 0 && (
              <div className="mt-4">
                <div className="font-medium text-sm mb-2">Used by Crews:</div>
                <div className="flex flex-wrap gap-2">
                  {kb.crew_usage.map((crew, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {crew}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const LearningEffectivenessOverview = () => (
    <div className="space-y-6">
      {learningEffectiveness && (
        <>
          {/* Learning Accuracy Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Field Mapping</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(learningEffectiveness.field_mapping_accuracy * 100).toFixed(1)}%
                </div>
                <Progress value={learningEffectiveness.field_mapping_accuracy * 100} className="h-2 mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Asset Classification</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(learningEffectiveness.asset_classification_accuracy * 100).toFixed(1)}%
                </div>
                <Progress value={learningEffectiveness.asset_classification_accuracy * 100} className="h-2 mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Dependency Detection</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(learningEffectiveness.dependency_detection_accuracy * 100).toFixed(1)}%
                </div>
                <Progress value={learningEffectiveness.dependency_detection_accuracy * 100} className="h-2 mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">User Feedback</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(learningEffectiveness.user_feedback_integration * 100).toFixed(1)}%
                </div>
                <Progress value={learningEffectiveness.user_feedback_integration * 100} className="h-2 mt-2" />
              </CardContent>
            </Card>
          </div>

          {/* Learning Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Learning Improvement Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="text-3xl font-bold">
                  {learningEffectiveness.improvement_trend > 0 ? '+' : ''}
                  {(learningEffectiveness.improvement_trend * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  improvement over last 10 interactions
                </div>
                <Badge variant={learningEffectiveness.improvement_trend > 0 ? 'default' : 'secondary'}>
                  {learningEffectiveness.improvement_trend > 0 ? 'Improving' : 'Stable'}
                </Badge>
              </div>
              <div className="mt-4">
                <div className="text-sm font-medium mb-2">
                  Confidence Threshold: {(learningEffectiveness.confidence_threshold * 100).toFixed(0)}%
                </div>
                <Progress value={learningEffectiveness.confidence_threshold * 100} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const CrossCrewInsightsOverview = () => (
    <div className="space-y-4">
      {crossCrewInsights.length > 0 ? (
        <div className="grid gap-4">
          {crossCrewInsights.map((insight, index) => (
            <Card key={index}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">
                    {insight.source_crew} → {insight.target_crew}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {insight.insight_type}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      Used {insight.usage_count}x
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="font-medium mb-1">Confidence Score</div>
                    <div className="text-lg font-bold">{(insight.confidence_score * 100).toFixed(1)}%</div>
                    <Progress value={insight.confidence_score * 100} className="h-1 mt-1" />
                  </div>
                  <div>
                    <div className="font-medium mb-1">Effectiveness</div>
                    <div className="text-lg font-bold">{insight.effectiveness_score.toFixed(1)}/10</div>
                    <Progress value={insight.effectiveness_score * 10} className="h-1 mt-1" />
                  </div>
                  <div>
                    <div className="font-medium mb-1">Created</div>
                    <div className="text-sm">{new Date(insight.created_at).toLocaleDateString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-8">
            <Network className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No cross-crew insights available yet</p>
            <p className="text-sm text-gray-400">Insights will appear as crews collaborate and share knowledge</p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Memory & Knowledge Analytics
              </CardTitle>
              <CardDescription>
                Real-time monitoring of memory usage, knowledge utilization, and learning effectiveness
              </CardDescription>
            </div>
            <div className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="memory">Memory</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge Bases</TabsTrigger>
          <TabsTrigger value="learning">Learning</TabsTrigger>
          <TabsTrigger value="insights">Cross-Crew Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="memory" className="space-y-4">
          <MemoryOverview />
        </TabsContent>

        <TabsContent value="knowledge" className="space-y-4">
          <KnowledgeBasesOverview />
        </TabsContent>

        <TabsContent value="learning" className="space-y-4">
          <LearningEffectivenessOverview />
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <CrossCrewInsightsOverview />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MemoryKnowledgePanel; 