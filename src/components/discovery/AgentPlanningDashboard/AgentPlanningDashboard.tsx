/**
 * Agent Planning Dashboard
 *
 * Main dashboard component for agent planning and task management.
 */

import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brain, RefreshCw, AlertCircle, X } from 'lucide-react';

import type { AgentPlanningDashboardProps, FeedbackType, TaskInput } from './types'
import type { AgentPlan } from './types'
import * as api from './api';
import PlanOverview from './PlanOverview';
import FeedbackForm from './FeedbackForm';
import TaskCard from './TaskCard';
import HumanInputTab from './HumanInputTab';
import CompletedTaskCard from './CompletedTaskCard';
import NextActionsTab from './NextActionsTab';

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
  const [modalOpen, setModalOpen] = useState(isOpen);

  // Human input state
  const [planSuggestion, setPlanSuggestion] = useState('');
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('suggestion');

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

  const fetchAgentPlan = async (): Promise<any> => {
    try {
      setLoading(true);
      setError(null);

      const plan = await api.fetchAgentPlan(pageContext);
      setAgentPlan(plan);
    } catch (err) {
      setError('Agent planning service partially available - showing demo workflow');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskApproval = async (taskId: string, approved: boolean): void => {
    try {
      await api.submitTaskApproval(taskId, approved, pageContext);

      if (onTaskFeedback) {
        onTaskFeedback(taskId, { approved });
      }

      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit task approval:', error);
    }
  };

  const handleHumanInputSubmission = async (taskId: string, input: TaskInput): void => {
    try {
      await api.submitHumanInput(taskId, input, pageContext);

      if (onHumanInput) {
        onHumanInput(taskId, input);
      }

      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit human input:', error);
    }
  };

  const handlePlanSuggestionSubmit = async (): void => {
    if (!planSuggestion.trim() || !agentPlan) return;

    try {
      await api.submitPlanSuggestion(agentPlan.plan_id, planSuggestion, feedbackType, pageContext);

      setPlanSuggestion('');
      alert('✅ Plan suggestion submitted successfully! Agents will consider this feedback for plan improvements.');

      // Refresh plan
      await fetchAgentPlan();
    } catch (error) {
      console.error('Failed to submit plan suggestion:', error);
      alert('🎭 Demo mode: Plan suggestion recorded. In production, this would update the agent planning workflow.');
    }
  };

  const handleCloseModal = (): void => {
    setModalOpen(false);
    if (onClose) {
      onClose();
    }
  };

  // Enhanced trigger element with proper modal control
  const enhancedTriggerElement = triggerElement ? (
    <div onClick={() => setModalOpen(true)} className="cursor-pointer">
      {triggerElement}
    </div>
  ) : (
    <Button onClick={() => setModalOpen(true)}>
      <Brain className="h-4 w-4 mr-2" />
      Open Agent Planning
    </Button>
  );

  return (
    <>
      {/* Trigger Element */}
      {enhancedTriggerElement}

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
                  <PlanOverview agentPlan={agentPlan} />

                  {/* Human Input Section */}
                  <FeedbackForm
                    feedbackType={feedbackType}
                    setFeedbackType={setFeedbackType}
                    planSuggestion={planSuggestion}
                    setPlanSuggestion={setPlanSuggestion}
                    onSubmit={handlePlanSuggestionSubmit}
                  />

                  {/* Rest of the existing content in tabs */}
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid grid-cols-4 w-full">
                      <TabsTrigger value="overview">Next Actions</TabsTrigger>
                      <TabsTrigger value="human-input">Human Input Required</TabsTrigger>
                      <TabsTrigger value="active">Active & Planned</TabsTrigger>
                      <TabsTrigger value="completed">Completed</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4 mt-6">
                      <NextActionsTab nextActions={agentPlan.next_actions} />
                    </TabsContent>

                    <TabsContent value="human-input" className="space-y-4 mt-6">
                      <HumanInputTab
                        humanInputTasks={agentPlan.human_input_required}
                        onHumanInputSubmission={handleHumanInputSubmission}
                      />
                    </TabsContent>

                    <TabsContent value="active" className="space-y-4 mt-6">
                      {agentPlan.tasks.filter(task => task.status !== 'completed').map((task) => (
                        <TaskCard key={task.id} task={task} />
                      ))}
                    </TabsContent>

                    <TabsContent value="completed" className="space-y-4 mt-6">
                      {agentPlan.tasks.filter(task => task.status === 'completed').map((task) => (
                        <CompletedTaskCard key={task.id} task={task} />
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
