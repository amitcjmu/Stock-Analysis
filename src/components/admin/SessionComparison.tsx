/**
 * Session Comparison Component for "what-if" scenario analysis
 * Provides side-by-side session comparison with comprehensive diff visualization
 */

import React from 'react';
import { SessionComparisonMain } from './session-comparison';

interface ComparisonResult {
  engagementId: string;
  differences: unknown[];
  summary: Record<string, unknown>;
}

interface SessionComparisonProps {
  engagementId: string;
  onComparisonComplete?: (comparison: ComparisonResult) => void;
}

export const SessionComparison: React.FC<SessionComparisonProps> = (props) => {
  return <SessionComparisonMain {...props} />;
};

export default SessionComparison; 