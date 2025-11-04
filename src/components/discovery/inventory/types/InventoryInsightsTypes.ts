/**
 * Types for EnhancedInventoryInsights functionality
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import type { Asset } from '../../../types/asset';
import type { InventoryProgress } from './inventory.types';

// Asset dependency interface
export interface AssetDependency {
  id: string;
  name: string;
  type: 'application' | 'database' | 'service' | 'network' | 'storage';
  relationship: 'depends_on' | 'supports' | 'connects_to';
  criticality: 'low' | 'medium' | 'high' | 'critical';
  metadata?: Record<string, unknown>;
}

export interface EnhancedInventoryInsightsProps {
  assets: Asset[];
  inventoryProgress: InventoryProgress;
  className?: string;
}

export interface CrewAIInsight {
  agent: string;
  insight: string;
  phase: string;
  category?: string;
  confidence?: number;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ProcessedInsights {
  infrastructure_patterns: {
    os_distribution: Record<string, number>;
    virtualization_level: number;
    cloud_readiness_score: number;
    standardization_assessment: string;
  };
  migration_readiness: {
    lift_shift_candidates: number;
    replatform_candidates: number;
    modernization_required: number;
    risk_factors: string[];
  };
  sixr_recommendations: Record<string, number>;
  technology_analysis: {
    stack_diversity: string;
    modernization_score: number;
    integration_complexity: string;
  };
  business_impact: {
    cost_optimization_potential: string;
    performance_improvement_areas: string[];
    compliance_gaps: string[];
  };
  actionable_recommendations: {
    immediate_actions: string[];
    strategic_initiatives: string[];
    quick_wins: string[];
  };
}

export interface InfrastructurePatternsProps {
  patterns: ProcessedInsights['infrastructure_patterns'];
}

export interface MigrationReadinessProps {
  readiness: ProcessedInsights['migration_readiness'];
}

export interface SixRRecommendationsProps {
  recommendations: ProcessedInsights['sixr_recommendations'];
}

export interface ActionableRecommendationsProps {
  recommendations: ProcessedInsights['actionable_recommendations'];
}
