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
  Settings,
  X,
  Edit3,
  Send
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
  isOpen?: boolean;
  onClose?: () => void;
  triggerElement?: React.ReactNode;
}

const AgentPlanningDashboard: React.FC<AgentPlanningDashboardProps> = ({
  pageContext,
  onPlanApproval,
  onTaskFeedback,
  onHumanInput,
  isOpen = false,
  onClose,
  triggerElement
}) => {
  const [agentPlan, setAgentPlan] = useState<AgentPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);
  const [humanInputDialog, setHumanInputDialog] = useState(false);
  const [planApprovalDialog, setPlanApprovalDialog] = useState(false);
  const [modalOpen, setModalOpen] = useState(isOpen);
  
  // Human input state
  const [humanInputText, setHumanInputText] = useState('');
  const [planSuggestion, setPlanSuggestion] = useState('');
  const [feedbackType, setFeedbackType] = useState<'suggestion' | 'concern' | 'approval' | 'correction'>('suggestion');

  useEffect(() => {
    setModalOpen(isOpen);
  }, [isOpen]);

  useEffect(() => {
    if (modalOpen) {
      fetchAgentPlan();
      // Poll for updates every 30 seconds when modal is open
      const interval = setInterval(fetchAgentPlan, 30000);
      return () => clearInterval(interval);
    }
  }, [pageContext, modalOpen]);

  const fetchAgentPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🤖 Fetching agent plan for context:', pageContext);
      
      // Get current agent plan for the page context
      const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS}/plan`, {
        method: 'POST',
        body: JSON.stringify({
          page_context: pageContext,
          analysis_type: 'planning_workflow',
          include_human_feedback_opportunities: true
        })
      });
      
      console.log('🤖 Agent plan response:', response);
      
      if (response.agent_plan) {
        setAgentPlan(response.agent_plan);
      } else {
        // Generate a demo plan based on page context
        console.log('🎭 No agent plan in response, generating demo plan');
        setAgentPlan(generateDemoPlan(pageContext));
      }
    } catch (err) {
      console.error('Failed to fetch agent plan:', err);
      
      // Always provide demo plan for development - don't show error state
      const demoPlan = generateDemoPlan(pageContext);
      setAgentPlan(demoPlan);
      
      // Only set error if it's not a 404 (which just means the endpoint isn't implemented yet)
      if (err.message && !err.message.includes('404')) {
        setError('Agent planning service partially available - showing demo workflow');
      } else {
        console.log('🎭 Agent planning endpoint not available, using demo plan');
      }
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
      setHumanInputText('');
      
      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit human input:', error);
    }
  };

  const handlePlanSuggestionSubmit = async () => {
    if (!planSuggestion.trim()) return;
    
    try {
      await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
        method: 'POST',
        body: JSON.stringify({
          plan_id: agentPlan?.plan_id,
          suggestion: planSuggestion,
          feedback_type: feedbackType,
          page_context: pageContext,
          learning_type: 'plan_modification_feedback'
        })
      });
      
      setPlanSuggestion('');
      alert('✅ Plan suggestion submitted successfully! Agents will consider this feedback for plan improvements.');
      
      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit plan suggestion:', error);
      alert('🎭 Demo mode: Plan suggestion recorded. In production, this would update the agent planning workflow.');
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    if (onClose) {
      onClose();
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

  // Trigger button (if no custom trigger provided)
  const defaultTrigger = (
    <Button 
      onClick={() => setModalOpen(true)}
      variant="outline" 
      className="w-full"
    >
      <Brain className="h-4 w-4 mr-2" />
      Agent Planning Dashboard
    </Button>
  );

  return (
    <>
      {/* Trigger Element */}
      {triggerElement || defaultTrigger}

      {/* Modal Overlay */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-[90%] h-[90%] max-w-7xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Brain className="h-6 w-6" />
                <h2 className="text-2xl font-bold text-gray-900">
                  {agentPlan?.plan_name || 'Agent Planning Dashboard'}
                </h2>
                {agentPlan && (
                  <Badge variant={agentPlan.status === 'active' ? 'default' : 'secondary'}>
                    {agentPlan.status}
                  </Badge>
                )}
              </div>
              <Button onClick={handleCloseModal} variant="ghost" size="sm">
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading agent plan...</span>
                </div>
              ) : error || !agentPlan ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
                  <p className="text-red-600 mb-4">{error || 'No agent plan available'}</p>
                  <Button onClick={fetchAgentPlan} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Plan Overview */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <p className="text-gray-600 mb-4">{agentPlan.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">{agentPlan.overall_progress}%</div>
                        <div className="text-sm text-gray-600">Overall Progress</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600">{agentPlan.completed_tasks}</div>
                        <div className="text-sm text-gray-600">Completed Tasks</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-orange-600">{agentPlan.human_input_required.length}</div>
                        <div className="text-sm text-gray-600">Need Your Input</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600">{agentPlan.blocking_issues.length}</div>
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
                      <Progress value={agentPlan.overall_progress} className="h-3" />
                    </div>
                  </div>

                  {/* Human Input Section */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
                      <Edit3 className="h-5 w-5" />
                      Provide Plan Feedback
                    </h3>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Feedback Type
                        </label>
                        <select
                          value={feedbackType}
                          onChange={(e) => setFeedbackType(e.target.value as any)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="suggestion">Suggestion for improvement</option>
                          <option value="concern">Concern about current plan</option>
                          <option value="approval">Approval with comments</option>
                          <option value="correction">Correction needed</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Your Input
                        </label>
                        <textarea
                          value={planSuggestion}
                          onChange={(e) => setPlanSuggestion(e.target.value)}
                          placeholder="Share your suggestions, concerns, or corrections for the agent plan..."
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <Button 
                        onClick={handlePlanSuggestionSubmit}
                        disabled={!planSuggestion.trim()}
                        className="w-full"
                      >
                        <Send className="h-4 w-4 mr-2" />
                        Submit Feedback to Agents
                      </Button>
                    </div>
                  </div>

                  {/* Rest of the existing content in tabs */}
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid grid-cols-4 w-full">
                      <TabsTrigger value="overview">Next Actions</TabsTrigger>
                      <TabsTrigger value="human-input">Human Input Required</TabsTrigger>
                      <TabsTrigger value="active">Active & Planned</TabsTrigger>
                      <TabsTrigger value="completed">Completed</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4 mt-6">
                      {agentPlan.next_actions.length > 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                            <Target className="h-4 w-4" />
                            Next Actions for You
                          </h4>
                          <ul className="space-y-1">
                            {agentPlan.next_actions.map((action, index) => (
                              <li key={index} className="text-sm text-green-800 flex items-center gap-2">
                                <ArrowRight className="h-3 w-3" />
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="human-input" className="space-y-4 mt-6">
                      {agentPlan.human_input_required.length > 0 ? (
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
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p>No human input required at this time</p>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="active" className="space-y-4 mt-6">
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
                          </div>
                        </div>
                      ))}
                    </TabsContent>

                    <TabsContent value="completed" className="space-y-4 mt-6">
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
                  </Tabs>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="border-t border-gray-200 p-6 flex justify-between items-center">
              <Button onClick={fetchAgentPlan} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Plan
              </Button>
              
              <div className="flex gap-3">
                <Button onClick={handleCloseModal} variant="outline">
                  Close Dashboard
                </Button>
                {agentPlan && (
                  <Button onClick={() => {
                    if (onPlanApproval) {
                      onPlanApproval(agentPlan.plan_id, true);
                    }
                    alert('✅ Plan approved! Agents will proceed with execution.');
                  }}>
                    Approve Plan
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AgentPlanningDashboard; 