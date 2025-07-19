/**
 * Metrics and Performance Types
 * 
 * Performance and session metrics types for session comparison.
 */

export interface SessionMetrics {
  pageViews: number;
  uniquePages: number;
  totalClicks: number;
  totalKeystrokes: number;
  idleTime: number;
  activeTime: number;
  bounceRate: number;
  engagementScore: number;
  performanceMetrics: PerformanceMetrics;
  errorCount: number;
  warningCount: number;
}

export interface PerformanceMetrics {
  averagePageLoadTime: number;
  averageResponseTime: number;
  networkLatency: number;
  renderTime: number;
  resourceLoadTime: number;
  jsExecutionTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
}