/**
 * Assessment Flow Page Utils
 * Server-side props and utility functions for assessment flow pages
 */

import type { GetServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async (context) => {
  return {
    props: {
      flowId: context.params?.flowId as string
    }
  };
};

/**
 * Map backend assessment phase to frontend URL path
 *
 * Backend phases (from AssessmentPhase enum):
 * - initialization → architecture (default start page)
 * - readiness_assessment → architecture
 * - complexity_analysis → complexity
 * - dependency_analysis → dependency
 * - tech_debt_assessment → tech-debt
 * - risk_assessment → risk
 * - recommendation_generation → sixr-review
 * - finalization → summary
 */
export function getPhaseUrl(flowId: string, phase: string): string {
  const phaseUrlMap: Record<string, string> = {
    'initialization': 'architecture',
    'readiness_assessment': 'architecture',
    'complexity_analysis': 'complexity',
    'dependency_analysis': 'dependency',
    'tech_debt_assessment': 'tech-debt',
    'risk_assessment': 'risk',
    'recommendation_generation': 'sixr-review',
    'finalization': 'summary',
    // Legacy phase names (for backward compatibility)
    'architecture_minimums': 'architecture',
    'tech_debt_analysis': 'tech-debt',
    'component_sixr_strategies': 'risk',
    'app_on_page_generation': 'sixr-review',
  };

  const urlPath = phaseUrlMap[phase] || 'architecture'; // Default to architecture
  return `/assessment/${flowId}/${urlPath}`;
}
