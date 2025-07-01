import React from 'react';
import { RefreshCw, Zap, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { AttributeMappingState } from '../types';

interface AttributeMappingHeaderProps {
  mappingProgress: any;
  isAgenticLoading: boolean;
  canContinueToDataCleansing: boolean;
  onRefetch: () => void;
  onTriggerAnalysis: () => void;
  onContinueToDataCleansing: () => void;
}

export const AttributeMappingHeader: React.FC<AttributeMappingHeaderProps> = ({
  mappingProgress,
  isAgenticLoading,
  canContinueToDataCleansing,
  onRefetch,
  onTriggerAnalysis,
  onContinueToDataCleansing
}) => {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center space-x-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Field Mapping & Critical Attributes</h1>
          <p className="text-gray-600">
            {mappingProgress.total > 0 
              ? `${mappingProgress.total} attributes analyzed with ${mappingProgress.mapped} mapped and ${mappingProgress.critical_mapped} migration-critical` 
              : 'AI-powered field mapping and critical attribute identification'
            }
          </p>
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        <Button
          onClick={onRefetch}
          disabled={isAgenticLoading}
          variant="outline"
          className="flex items-center space-x-2"
        >
          {isAgenticLoading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span>Refresh</span>
        </Button>

        <Button
          onClick={onTriggerAnalysis}
          disabled={isAgenticLoading}
          variant="outline"
          className="flex items-center space-x-2"
        >
          <Zap className="h-4 w-4" />
          <span>Trigger Analysis</span>
        </Button>

        {canContinueToDataCleansing && (
          <Button
            onClick={onContinueToDataCleansing}
            className="bg-green-600 hover:bg-green-700 flex items-center space-x-2"
          >
            <span>Continue to Data Cleansing</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
};