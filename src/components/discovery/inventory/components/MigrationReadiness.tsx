/**
 * MigrationReadiness Component
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import React from 'react';
import { Cloud } from 'lucide-react';
import { MigrationReadinessProps } from '../types/InventoryInsightsTypes';

export const MigrationReadiness: React.FC<MigrationReadinessProps> = ({ readiness }) => {
  return (
    <div>
      <h4 className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-3">
        <Cloud className="h-4 w-4 text-green-500" />
        Migration Readiness Intelligence
      </h4>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">{readiness.lift_shift_candidates}</div>
          <div className="text-gray-600">Lift & Shift Ready</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-orange-600">{readiness.replatform_candidates}</div>
          <div className="text-gray-600">Replatform Required</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-red-600">{readiness.modernization_required}</div>
          <div className="text-gray-600">Modernization Needed</div>
        </div>
      </div>
    </div>
  );
};