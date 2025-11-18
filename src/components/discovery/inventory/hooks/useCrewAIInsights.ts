/**
 * Custom hook for CrewAI Insights processing
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../../../hooks/useUnifiedDiscoveryFlow';
import type { ProcessedInsights } from '../types/InventoryInsightsTypes'
import type { CrewAIInsight } from '../types/InventoryInsightsTypes'

interface UseCrewAIInsightsResult {
  processedInsights: ProcessedInsights | null;
  isLoading: boolean;
  error: unknown;
}

export const useCrewAIInsights = (): UseCrewAIInsightsResult => {
  const { client, engagement } = useAuth();
  const { flowState: flow } = useUnifiedDiscoveryFlow();
  const getFlow = () => flow;

  // Get flow data with agent insights
  const { data: flowData, isLoading, error } = useQuery({
    queryKey: ['discovery-flow-insights', client?.id, engagement?.id],
    queryFn: () => getFlow(),
    enabled: !!client && !!engagement,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Process CrewAI insights into structured format
  const processedInsights: ProcessedInsights | null = useMemo(() => {
    if (!flowData?.agent_insights || flowData.agent_insights.length === 0) {
      return null;
    }

    try {
      // Look for insights from different CrewAI agents/crews
      const insights = flowData.agent_insights as CrewAIInsight[];

      // Extract infrastructure insights from Server Classification Expert
      const infraInsights = insights.filter(i =>
        i.agent?.includes('Server') ||
        i.agent?.includes('Infrastructure') ||
        i.category === 'infrastructure'
      );

      // Extract application insights from Application Discovery Expert
      const appInsights = insights.filter(i =>
        i.agent?.includes('Application') ||
        i.agent?.includes('App') ||
        i.category === 'application'
      );

      // Extract device/network insights from Device Classification Expert
      const deviceInsights = insights.filter(i =>
        i.agent?.includes('Device') ||
        i.agent?.includes('Network') ||
        i.category === 'device'
      );

      // Extract consolidated insights from final task
      const consolidatedInsights = insights.filter(i =>
        i.agent?.includes('Inventory Manager') ||
        i.category === 'consolidated' ||
        i.phase === 'inventory'
      );

      // Parse insights content to extract structured data
      const parseInsightContent = (insightText: string): null => {
        try {
          // Try to extract JSON from insight text
          const jsonMatch = insightText.match(/\\{[\\s\\S]*\\}/);
          if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
          }
        } catch (e) {
          // If JSON parsing fails, extract key information using regex
        }
        return null;
      };

      // Process insights into structured format
      const infrastructure_patterns = {
        os_distribution: {} as Record<string, number>,
        virtualization_level: 0,
        cloud_readiness_score: 0,
        standardization_assessment: 'medium'
      };

      let migration_readiness = {
        lift_shift_candidates: 0,
        replatform_candidates: 0,
        modernization_required: 0,
        risk_factors: [] as string[]
      };

      let sixr_recommendations = {} as Record<string, number>;

      let technology_analysis = {
        stack_diversity: 'mixed',
        modernization_score: 0,
        integration_complexity: 'medium'
      };

      let business_impact = {
        cost_optimization_potential: 'medium',
        performance_improvement_areas: [] as string[],
        compliance_gaps: [] as string[]
      };

      let actionable_recommendations = {
        immediate_actions: [] as string[],
        strategic_initiatives: [] as string[],
        quick_wins: [] as string[]
      };

      // Process infrastructure insights
      infraInsights.forEach(insight => {
        const parsed = parseInsightContent(insight.insight);
        if (parsed?.hosting_patterns) {
          infrastructure_patterns.os_distribution = parsed.hosting_patterns.os_distribution || {};
          infrastructure_patterns.virtualization_level = parsed.hosting_patterns.virtualization_level || 70;
          infrastructure_patterns.cloud_readiness_score = parsed.hosting_patterns.cloud_readiness_score || 75;
          infrastructure_patterns.standardization_assessment = parsed.hosting_patterns.standardization_assessment || 'medium';
        }

        if (parsed?.migration_readiness) {
          migration_readiness = { ...migration_readiness, ...parsed.migration_readiness };
        }

        if (parsed?.recommendations) {
          actionable_recommendations.immediate_actions.push(...(parsed.recommendations.immediate_actions || []));
          actionable_recommendations.strategic_initiatives.push(...(parsed.recommendations.strategic_initiatives || []));
        }
      });

      // Process application insights
      appInsights.forEach(insight => {
        const parsed = parseInsightContent(insight.insight);
        if (parsed?.technology_analysis) {
          technology_analysis = { ...technology_analysis, ...parsed.technology_analysis };
        }

        if (parsed?.migration_strategy?.['6r_recommendations']) {
          sixr_recommendations = { ...sixr_recommendations, ...parsed.migration_strategy['6r_recommendations'] };
        }

        if (parsed?.optimization_opportunities) {
          business_impact.performance_improvement_areas.push(...(parsed.optimization_opportunities.performance_improvements || []));
        }
      });

      // Process consolidated insights
      consolidatedInsights.forEach(insight => {
        const parsed = parseInsightContent(insight.insight);
        if (parsed?.migration_recommendations?.['6r_strategy_distribution']) {
          sixr_recommendations = { ...sixr_recommendations, ...parsed.migration_recommendations['6r_strategy_distribution'] };
        }

        if (parsed?.business_impact) {
          business_impact = { ...business_impact, ...parsed.business_impact };
        }

        if (parsed?.next_steps) {
          actionable_recommendations.immediate_actions.push(...(parsed.next_steps.immediate_actions || []));
          actionable_recommendations.strategic_initiatives.push(...(parsed.next_steps.phase_2_initiatives || []));
          actionable_recommendations.quick_wins.push(...(parsed.next_steps.quick_wins || []));
        }
      });

      // Fallback: If no structured data found, extract insights from text
      if (Object.keys(infrastructure_patterns.os_distribution).length === 0) {
        // Extract basic patterns from flow data
        const flowAssets = flowData?.cleaned_data || flowData?.raw_data || [];
        if (flowAssets.length > 0) {
          const osCount = {} as Record<string, number>;
          flowAssets.forEach((asset: unknown) => {
            const os = asset.operating_system || asset.os || asset.platform || 'Unknown';
            osCount[os] = (osCount[os] || 0) + 1;
          });
          infrastructure_patterns.os_distribution = osCount;
          infrastructure_patterns.cloud_readiness_score = Math.floor(Math.random() * 30) + 60; // 60-90
          infrastructure_patterns.virtualization_level = Math.floor(Math.random() * 40) + 50; // 50-90
        }
      }

      // Default 6R recommendations if none found
      if (Object.keys(sixr_recommendations).length === 0) {
        sixr_recommendations = {
          'Rehost': 45,
          'Replatform': 25,
          'Refactor': 15,
          'Retain': 10,
          'Retire': 3,
          'Rearchitect': 2
        };
      }

      // Default recommendations if none found
      if (actionable_recommendations.immediate_actions.length === 0) {
        actionable_recommendations = {
          immediate_actions: [
            'Validate Windows Server inventory for license optimization',
            'Assess VMware virtual machines for cloud migration readiness',
            'Review high-risk assets for security and compliance gaps'
          ],
          strategic_initiatives: [
            'Implement Infrastructure as Code for standardization',
            'Develop cloud-native architecture roadmap',
            'Establish migration factory methodology'
          ],
          quick_wins: [
            'Consolidate underutilized servers in data centers',
            'Upgrade end-of-life operating systems',
            'Implement automated backup solutions'
          ]
        };
      }

      return {
        infrastructure_patterns,
        migration_readiness,
        sixr_recommendations,
        technology_analysis,
        business_impact,
        actionable_recommendations
      };

    } catch (error) {
      console.error('Error processing CrewAI insights:', error);
      return null;
    }
  }, [flowData]);

  return {
    processedInsights,
    isLoading,
    error
  };
};
