/**
 * Demo Data Generator
 *
 * Generates demo agent plans for different page contexts.
 */

import type { AgentPlan } from './types';

export const generateDemoPlan = (context: string): AgentPlan => {
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
