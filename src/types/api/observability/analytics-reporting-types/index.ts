/**
 * Analytics and Reporting Types - Modular Index
 *
 * Centralized exports for all analytics and reporting type definitions.
 * This modular structure provides focused modules for each domain:
 * - Shared Types: common types used across modules
 * - Performance Analysis: bottleneck detection, performance insights
 * - SLA Reporting: compliance tracking, breach analysis
 * - Capacity Planning: resource projections, growth planning
 * - Observability Analytics: metrics analysis, health monitoring
 * - Report Generation: customizable report templates and formats
 */

// Shared Supporting Types
export type * from './shared-types';

// Performance Analysis Types
export type * from './performance-analysis';

// SLA Reporting Types
export type * from './sla-reporting';

// Capacity Planning Types
export type * from './capacity-planning';

// Observability Analytics Types
export type * from './observability-analytics';

// Report Generation Types
export type * from './report-generation';
