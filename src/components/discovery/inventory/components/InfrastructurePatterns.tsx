/**
 * InfrastructurePatterns Component
 * Extracted from EnhancedInventoryInsights.tsx for modularization
 */

import React from 'react';
import { Server } from 'lucide-react';
import { Badge } from '../../../ui/badge';
import type { InfrastructurePatternsProps } from '../types/InventoryInsightsTypes';

export const InfrastructurePatterns: React.FC<InfrastructurePatternsProps> = ({ patterns }) => {
  return (
    <div>
      <h4 className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-3">
        <Server className="h-4 w-4 text-blue-500" />
        Infrastructure Pattern Analysis
      </h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Cloud Readiness:</span>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full" 
                style={{ width: `${patterns.cloud_readiness_score}%` }}
              />
            </div>
            <span className="font-medium">{patterns.cloud_readiness_score}%</span>
          </div>
        </div>
        <div>
          <span className="text-gray-600">Virtualization Level:</span>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full" 
                style={{ width: `${patterns.virtualization_level}%` }}
              />
            </div>
            <span className="font-medium">{patterns.virtualization_level}%</span>
          </div>
        </div>
      </div>
      
      {Object.keys(patterns.os_distribution).length > 0 && (
        <div className="mt-3">
          <span className="text-gray-600 text-sm">OS Distribution:</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(patterns.os_distribution).map(([os, count]) => (
              <Badge key={os} variant="outline" className="text-xs">
                {os}: {count}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};