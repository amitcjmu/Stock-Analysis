import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Brain, 
  Users, 
  Target,
  ArrowRight,
  PlayCircle,
  PauseCircle,
  RefreshCw,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  HelpCircle,
  Zap,
  TrendingUp,
  Settings
} from 'lucide-react';
import { apiCall, API_CONFIG } from '@/config/api';

interface AgentTask {
  id: string;
  agent_name: string;
  task_description: string;
  status: 'planned' | 'in_progress' | 'completed' | 'blocked' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  dependencies: string[];
  estimated_duration: number;
  progress: number;
  started_at?: string;
  completed_at?: string;
  requires_human_input?: boolean;
  human_feedback?: any;
}

interface AgentPlan {
  plan_id: string;
  plan_name: string;
  description: string;
  total_tasks: number;
  completed_tasks: number;
  overall_progress: number;
  estimated_completion: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  tasks: AgentTask[];
  next_actions: string[];
  blocking_issues: string[];
  human_input_required: AgentTask[];
}

interface AgentPlanningDashboardProps {
  pageContext: string;
  onPlanApproval?: (planId: string, approved: boolean) => void;
  onTaskFeedback?: (taskId: string, feedback: any) => void;
  onHumanInput?: (taskId: string, input: any) => void;
}

const AgentPlanningDashboard: React.FC<AgentPlanningDashboardProps> = ({
  pageContext,
  onPlanApproval,
  onTaskFeedback,
  onHumanInput
}) => {
  const [agentPlan, setAgentPlan] = useState<AgentPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [humanInputDialog, setHumanInputDialog] = useState(false);
  const [planApprovalDialog, setPlanApprovalDialog] = useState(false);

  useEffect(() => {
    fetchAgentPlan();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchAgentPlan, 30000);
    return () => clearInterval(interval);
  }, [pageContext]);

  const fetchAgentPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get current agent plan for the page context
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS}/plan`, {
        method: 'POST',
        body: JSON.stringify({
          page_context: pageContext,
          analysis_type: 'planning_workflow',
          include_human_feedback_opportunities: true
        })
      });
      
      if (response.agent_plan) {
        setAgentPlan(response.agent_plan);
      } else {
        // Generate a demo plan based on page context
        setAgentPlan(generateDemoPlan(pageContext));
      }
    } catch (err) {
      console.error('Failed to fetch agent plan:', err);
      setError('Failed to load agent planning data');
      // Set demo plan as fallback
      setAgentPlan(generateDemoPlan(pageContext));
    } finally {
      setLoading(false);
    }
  };

  const generateDemoPlan = (context: string): AgentPlan => {
    const baseId = `plan_${context}_${Date.now()}`;
    
    const contextPlans = {
      'asset-inventory': {
        name: 'Asset Inventory Intelligence Plan',
        description: 'AI-driven asset classification, quality improvement, and migration readiness assessment',
        tasks: [
          {
            id: 'task_1',
            agent_name: 'Asset Intelligence Agent',
            task_description: 'Analyze asset data quality and classify asset types using learned patterns',
            status: 'completed' as const,
            priority: 'high' as const,
            dependencies: [],
            estimated_duration: 15,
            progress: 100,
            completed_at: new Date(Date.now() - 300000).toISOString(),
            requires_human_input: false
          },
          {
            id: 'task_2', 
            agent_name: 'Field Mapping Intelligence',
            task_description: 'Suggest field mappings based on organizational patterns and validate data completeness',
            status: 'in_progress' as const,
            priority: 'high' as const,
            dependencies: ['task_1'],
            estimated_duration: 20,
            progress: 75,
            started_at: new Date(Date.now() - 180000).toISOString(),
            requires_human_input: true,
            human_feedback: {
              question: 'Should we map "Owner" field to "Business Owner" or "Technical Owner"?',
              options: ['Business Owner', 'Technical Owner', 'Both (create separate fields)'],
              context: 'Found ambiguous owner references in asset data'
            }
          },
          {
            id: 'task_3',
            agent_name: 'Migration Readiness Agent',
            task_description: 'Assess migration readiness and identify critical missing attributes',
            status: 'planned' as const,
            priority: 'medium' as const,
            dependencies: ['task_2'],
            estimated_duration: 10,
            progress: 0,
            requires_human_input: false
          }
        ]
      },
      'data-cleansing': {
        name: 'Data Quality Orchestration Plan',
        description: 'Intelligent data quality analysis and automated cleansing recommendations',
        tasks: [
          {
            id: 'task_1',
            agent_name: 'Data Quality Agent',
            task_description: 'Analyze data quality patterns and identify cleansing opportunities',
            status: 'completed' as const,
            priority: 'critical' as const,
            dependencies: [],
            estimated_duration: 25,
            progress: 100,
            completed_at: new Date(Date.now() - 600000).toISOString(),
            requires_human_input: false
          },
          {
            id: 'task_2',
            agent_name: 'Pattern Learning Agent',
            task_description: 'Learn from previous cleansing decisions to improve automation',
            status: 'in_progress' as const,
            priority: 'high' as const,
            dependencies: ['task_1'],
            estimated_duration: 15,
            progress: 60,
            started_at: new Date(Date.now() - 360000).toISOString(),
            requires_human_input: true,
            human_feedback: {
              question: 'Should we automatically standardize environment names (prod->Production, dev->Development)?',
              options: ['Yes, auto-standardize', 'No, flag for review', 'Ask each time'],
              context: 'Found 15 variations of environment names that could be standardized'
            }
          }
        ]
      },
      'tech-debt': {
        name: 'Technical Debt Assessment Plan',
        description: 'Comprehensive technology stack analysis and modernization roadmap',
        tasks: [
          {
            id: 'task_1',
            agent_name: 'Tech Debt Analyzer',
            task_description: 'Scan technology stack for end-of-life and deprecated components',
            status: 'completed' as const,
            priority: 'high' as const,
            dependencies: [],
            estimated_duration: 20,
            progress: 100,
            completed_at: new Date(Date.now() - 480000).toISOString(),
            requires_human_input: false
          },
          {
            id: 'task_2',
            agent_name: 'Modernization Planner',
            task_description: 'Generate modernization recommendations with timeline and effort estimates',
            status: 'blocked' as const,
            priority: 'medium' as const,
            dependencies: ['task_1'],
            estimated_duration: 30,
            progress: 0,
            requires_human_input: true,
            human_feedback: {
              question: 'What is your organization\'s preferred cloud platform for modernization?',
              options: ['AWS', 'Azure', 'Google Cloud', 'Multi-cloud', 'On-premises only'],
              context: 'Need to align modernization recommendations with your cloud strategy'
            }
          }
        ]
      }
    };

    const planData = contextPlans[context] || contextPlans['asset-inventory'];
    const completed = planData.tasks.filter(t => t.status === 'completed').length;
    const total = planData.tasks.length;
    
    return {
      plan_id: baseId,
      plan_name: planData.name,
      description: planData.description,
      total_tasks: total,
      completed_tasks: completed,
      overall_progress: Math.round((completed / total) * 100),
      estimated_completion: new Date(Date.now() + 1800000).toISOString(),
      status: completed === total ? 'completed' : 'active',
      tasks: planData.tasks,
      next_actions: [
        'Review human feedback requests',
        'Approve automated recommendations',
        'Validate learned patterns'
      ],
      blocking_issues: planData.tasks.filter(t => t.status === 'blocked').map(t => t.task_description),
      human_input_required: planData.tasks.filter(t => t.requires_human_input)
    };
  };

  const handleTaskApproval = async (taskId: string, approved: boolean) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
        method: 'POST',
        body: JSON.stringify({
          task_id: taskId,
          approval: approved,
          page_context: pageContext,
          learning_type: 'task_approval_feedback'
        })
      });
      
      if (onTaskFeedback) {
        onTaskFeedback(taskId, { approved });
      }
      
      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit task approval:', error);
    }
  };

  const handleHumanInputSubmission = async (taskId: string, input: any) => {
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
        method: 'POST',
        body: JSON.stringify({
          task_id: taskId,
          human_input: input,
          page_context: pageContext,
          learning_type: 'human_input_feedback'
        })
      });
      
      if (onHumanInput) {
        onHumanInput(taskId, input);
      }
      
      setHumanInputDialog(false);
      setSelectedTask(null);
      
      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit human input:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'planned': return 'text-gray-600 bg-gray-100';
      case 'blocked': return 'text-red-600 bg-red-100';
      case 'failed': return 'text-red-600 bg-red-200';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'in_progress': return <PlayCircle className="h-4 w-4" />;
      case 'planned': return <Clock className="h-4 w-4" />;
      case 'blocked': return <AlertCircle className="h-4 w-4" />;
      case 'failed': return <AlertCircle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Agent Planning Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            <span>Loading agent plan...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !agentPlan) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            Agent Planning Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600 mb-4">{error || 'No agent plan available'}</p>
          <Button onClick={fetchAgentPlan} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Plan Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              {agentPlan.plan_name}
            </span>
            <div className="flex items-center gap-2">
              <Badge variant={agentPlan.status === 'active' ? 'default' : 'secondary'}>
                {agentPlan.status}
              </Badge>
              <Button onClick={fetchAgentPlan} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">{agentPlan.description}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{agentPlan.overall_progress}%</div>
              <div className="text-sm text-gray-600">Overall Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{agentPlan.completed_tasks}</div>
              <div className="text-sm text-gray-600">Completed Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{agentPlan.human_input_required.length}</div>
              <div className="text-sm text-gray-600">Need Your Input</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{agentPlan.blocking_issues.length}</div>
              <div className="text-sm text-gray-600">Blocking Issues</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Plan Progress</span>
              <span className="text-sm text-gray-600">
                {agentPlan.completed_tasks} of {agentPlan.total_tasks} tasks completed
              </span>
            </div>
            <Progress value={agentPlan.overall_progress} className="h-2" />
          </div>

          {agentPlan.next_actions.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Next Actions for You
              </h4>
              <ul className="space-y-1">
                {agentPlan.next_actions.map((action, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Human Input Required */}
      {agentPlan.human_input_required.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-600">
              <MessageSquare className="h-5 w-5" />
              Human Input Required ({agentPlan.human_input_required.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {agentPlan.human_input_required.map((task) => (
                <div key={task.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
                      <p className="text-sm text-gray-600">{task.task_description}</p>
                    </div>
                    <Badge className={getPriorityColor(task.priority)}>
                      {task.priority}
                    </Badge>
                  </div>
                  
                  {task.human_feedback && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-orange-900 mb-2">
                        {task.human_feedback.question}
                      </p>
                      <p className="text-xs text-orange-700 mb-3">
                        Context: {task.human_feedback.context}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {task.human_feedback.options.map((option, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            onClick={() => handleHumanInputSubmission(task.id, { selected_option: option })}
                          >
                            {option}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Details */}
      <Card>
        <CardHeader>
          <CardTitle>Task Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-3 w-full">
              <TabsTrigger value="active">Active & Planned</TabsTrigger>
              <TabsTrigger value="completed">Completed</TabsTrigger>
              <TabsTrigger value="all">All Tasks</TabsTrigger>
            </TabsList>

            <TabsContent value="active" className="space-y-4 mt-4">
              {agentPlan.tasks.filter(task => task.status !== 'completed').map((task) => (
                <div key={task.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusIcon(task.status)}
                        <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
                        <Badge className={getStatusColor(task.status)}>
                          {task.status.replace('_', ' ')}
                        </Badge>
                        <Badge className={getPriorityColor(task.priority)}>
                          {task.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{task.task_description}</p>
                      {task.progress > 0 && (
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                      )}
                      <div className="text-xs text-gray-500">
                        Estimated duration: {task.estimated_duration} minutes
                        {task.dependencies.length > 0 && (
                          <span className="ml-2">
                            • Depends on: {task.dependencies.join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {task.requires_human_input && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedTask(task);
                            setHumanInputDialog(true);
                          }}
                        >
                          <MessageSquare className="h-4 w-4 mr-1" />
                          Provide Input
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="completed" className="space-y-4 mt-4">
              {agentPlan.tasks.filter(task => task.status === 'completed').map((task) => (
                <div key={task.id} className="border rounded-lg p-4 bg-green-50">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
                    <Badge className="text-green-600 bg-green-100">completed</Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{task.task_description}</p>
                  <div className="text-xs text-gray-500">
                    Completed: {task.completed_at ? new Date(task.completed_at).toLocaleString() : 'Unknown'}
                    • Duration: {task.estimated_duration} minutes
                  </div>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="all" className="space-y-4 mt-4">
              {agentPlan.tasks.map((task) => (
                <div key={task.id} className={`border rounded-lg p-4 ${task.status === 'completed' ? 'bg-green-50' : ''}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusIcon(task.status)}
                        <h4 className="font-medium text-gray-900">{task.agent_name}</h4>
                        <Badge className={getStatusColor(task.status)}>
                          {task.status.replace('_', ' ')}
                        </Badge>
                        <Badge className={getPriorityColor(task.priority)}>
                          {task.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{task.task_description}</p>
                      {task.progress > 0 && task.status !== 'completed' && (
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                      )}
                      <div className="text-xs text-gray-500">
                        {task.status === 'completed' && task.completed_at ? (
                          `Completed: ${new Date(task.completed_at).toLocaleString()}`
                        ) : task.status === 'in_progress' && task.started_at ? (
                          `Started: ${new Date(task.started_at).toLocaleString()}`
                        ) : (
                          `Estimated duration: ${task.estimated_duration} minutes`
                        )}
                        {task.dependencies.length > 0 && (
                          <span className="ml-2">
                            • Depends on: {task.dependencies.join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default AgentPlanningDashboard; 