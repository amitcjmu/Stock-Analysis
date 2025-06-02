import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, 
  TrendingUp, 
  Target, 
  Database, 
  CheckCircle, 
  AlertCircle,
  RefreshCw,
  Lightbulb
} from 'lucide-react';
import { useAppContext } from '@/hooks/useContext';
import { apiCall, API_CONFIG } from '@/config/api';

interface LearningStatistics {
  total_contexts: number;
  total_patterns: number;
  total_learning_events: number;
  field_mapping_patterns: number;
  data_source_patterns: number;
  quality_assessment_patterns: number;
  agents_tracked: number;
  last_updated: string;
}

interface SystemHealth {
  patterns_learned: boolean;
  agents_tracked: boolean;
  learning_active: boolean;
}

interface LearningData {
  learning_statistics: LearningStatistics;
  system_health: SystemHealth;
}

interface FieldMappingSuggestion {
  field_name: string;
  suggestion: {
    suggested_mapping: string;
    confidence: number;
    pattern_source: string;
    usage_count: number;
  };
  learning_available: boolean;
  context: string;
}

const AgentLearningInsights: React.FC = () => {
  const { context, getContextHeaders } = useAppContext();
  const [learningData, setLearningData] = useState<LearningData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testField, setTestField] = useState('server_name');
  const [fieldSuggestion, setFieldSuggestion] = useState<FieldMappingSuggestion | null>(null);

  const fetchLearningData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const headers = getContextHeaders();
      const response = await apiCall(
        API_CONFIG.ENDPOINTS.AGENT_LEARNING.LEARNING_STATISTICS,
        {
          method: 'GET',
          headers
        }
      );
      
      setLearningData(response);
    } catch (err) {
      console.error('Error fetching learning data:', err);
      setError('Failed to load learning insights');
    } finally {
      setIsLoading(false);
    }
  };

  const testFieldMapping = async () => {
    if (!testField.trim()) return;
    
    try {
      const headers = getContextHeaders();
      const response = await apiCall(
        `${API_CONFIG.ENDPOINTS.AGENT_LEARNING.FIELD_MAPPING_SUGGEST}/${encodeURIComponent(testField)}`,
        {
          method: 'GET',
          headers
        }
      );
      
      setFieldSuggestion(response);
    } catch (err) {
      console.error('Error testing field mapping:', err);
      setFieldSuggestion(null);
    }
  };

  const learnFieldMapping = async () => {
    try {
      const headers = getContextHeaders();
      await apiCall(
        API_CONFIG.ENDPOINTS.AGENT_LEARNING.FIELD_MAPPING_LEARN,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({
            original_field: 'application_name',
            mapped_field: 'app_name',
            field_type: 'application_identifier',
            confidence: 0.85
          })
        }
      );
      
      // Refresh data after learning
      await fetchLearningData();
    } catch (err) {
      console.error('Error learning field mapping:', err);
    }
  };

  useEffect(() => {
    fetchLearningData();
  }, [context]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Agent Learning Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading learning insights...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Agent Learning Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button onClick={fetchLearningData} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!learningData) {
    return null;
  }

  const { learning_statistics, system_health } = learningData;

  const getHealthColor = (isHealthy: boolean) => isHealthy ? 'text-green-600' : 'text-gray-400';
  const getHealthIcon = (isHealthy: boolean) => isHealthy ? CheckCircle : AlertCircle;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Agent Learning Insights
          <Badge variant={system_health.learning_active ? "default" : "secondary"}>
            {system_health.learning_active ? "Active" : "Inactive"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="patterns">Patterns</TabsTrigger>
            <TabsTrigger value="test">Test Learning</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {learning_statistics.total_contexts}
                </div>
                <div className="text-sm text-gray-600">Active Contexts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {learning_statistics.total_patterns}
                </div>
                <div className="text-sm text-gray-600">Learned Patterns</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {learning_statistics.total_learning_events}
                </div>
                <div className="text-sm text-gray-600">Learning Events</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {learning_statistics.agents_tracked}
                </div>
                <div className="text-sm text-gray-600">Agents Tracked</div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Target className="h-4 w-4" />
                System Health
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex items-center gap-2">
                  {React.createElement(getHealthIcon(system_health.patterns_learned), {
                    className: `h-4 w-4 ${getHealthColor(system_health.patterns_learned)}`
                  })}
                  <span className="text-sm">Patterns Learned</span>
                </div>
                <div className="flex items-center gap-2">
                  {React.createElement(getHealthIcon(system_health.agents_tracked), {
                    className: `h-4 w-4 ${getHealthColor(system_health.agents_tracked)}`
                  })}
                  <span className="text-sm">Agents Tracked</span>
                </div>
                <div className="flex items-center gap-2">
                  {React.createElement(getHealthIcon(system_health.learning_active), {
                    className: `h-4 w-4 ${getHealthColor(system_health.learning_active)}`
                  })}
                  <span className="text-sm">Learning Active</span>
                </div>
              </div>
            </div>

            <div className="text-xs text-gray-500">
              Last updated: {new Date(learning_statistics.last_updated).toLocaleString()}
            </div>
          </TabsContent>

          <TabsContent value="patterns" className="space-y-4">
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <Database className="h-4 w-4" />
                Pattern Distribution
              </h4>
              
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Field Mapping Patterns</span>
                    <span>{learning_statistics.field_mapping_patterns}</span>
                  </div>
                  <Progress 
                    value={(learning_statistics.field_mapping_patterns / Math.max(learning_statistics.total_patterns, 1)) * 100} 
                    className="h-2"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Data Source Patterns</span>
                    <span>{learning_statistics.data_source_patterns}</span>
                  </div>
                  <Progress 
                    value={(learning_statistics.data_source_patterns / Math.max(learning_statistics.total_patterns, 1)) * 100} 
                    className="h-2"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Quality Assessment Patterns</span>
                    <span>{learning_statistics.quality_assessment_patterns}</span>
                  </div>
                  <Progress 
                    value={(learning_statistics.quality_assessment_patterns / Math.max(learning_statistics.total_patterns, 1)) * 100} 
                    className="h-2"
                  />
                </div>
              </div>

              {learning_statistics.total_patterns === 0 && (
                <div className="text-center py-6 text-gray-500">
                  <Lightbulb className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No patterns learned yet</p>
                  <p className="text-sm">Agents will learn patterns as you use the system</p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="test" className="space-y-4">
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Test Field Mapping Learning</h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={testField}
                    onChange={(e) => setTestField(e.target.value)}
                    placeholder="Enter field name to test"
                    className="flex-1 px-3 py-2 border rounded-md"
                  />
                  <Button onClick={testFieldMapping}>
                    Test Mapping
                  </Button>
                </div>
              </div>

              {fieldSuggestion && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h5 className="font-medium mb-2">Mapping Suggestion</h5>
                  <div className="space-y-2 text-sm">
                    <div><strong>Field:</strong> {fieldSuggestion.field_name}</div>
                    <div><strong>Suggested Mapping:</strong> {fieldSuggestion.suggestion.suggested_mapping || 'None'}</div>
                    <div><strong>Confidence:</strong> {(fieldSuggestion.suggestion.confidence * 100).toFixed(1)}%</div>
                    <div><strong>Source:</strong> {fieldSuggestion.suggestion.pattern_source}</div>
                    <div><strong>Usage Count:</strong> {fieldSuggestion.suggestion.usage_count}</div>
                    <div><strong>Context:</strong> {fieldSuggestion.context}</div>
                  </div>
                </div>
              )}

              <div>
                <h4 className="font-semibold mb-2">Learn New Pattern</h4>
                <Button onClick={learnFieldMapping} className="w-full">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Learn Sample Field Mapping
                </Button>
                <p className="text-xs text-gray-500 mt-1">
                  This will teach the system that "application_name" maps to "app_name"
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <div className="mt-4 pt-4 border-t">
          <Button onClick={fetchLearningData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default AgentLearningInsights; 