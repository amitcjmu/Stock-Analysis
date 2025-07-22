/**
 * Session Comparison Component for "what-if" scenario analysis
 * Provides side-by-side session comparison with comprehensive diff visualization
 */

import type { SessionComparison as SessionComparisonType } from '../../types/components/admin/session-comparison/comparison-types';
import React from 'react';
import { SessionComparisonMain } from './session-comparison';

interface SessionComparisonProps {
  engagementId: string;
  onComparisonComplete?: (comparison: SessionComparisonType) => void;
}

export const SessionComparison: React.FC<SessionComparisonProps> = (props) => {
  return <SessionComparisonMain {...props} />;
};

export default SessionComparison; 