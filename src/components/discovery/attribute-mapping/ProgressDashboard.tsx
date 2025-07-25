import React from 'react';
import { Database, CheckCircle, Target, Brain } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  accuracy: number;
}

interface ProgressDashboardProps {
  progress?: MappingProgress;
  agentAnalysis?: unknown;
  flowId?: string;
  effectiveFlowId?: string;
  availableDataImports?: unknown[];
  selectedDataImportId?: string;
  onDataImportSelection?: (importId: string) => void;
  isLoading?: boolean;
}

const ProgressDashboard: React.FC<ProgressDashboardProps> = ({
  progress: mappingProgress,
  isLoading = false
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  const progress = mappingProgress || { total: 0, mapped: 0, critical_mapped: 0, accuracy: 0 };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{progress.total}</h3>
            <p className="text-xs text-gray-600">Total Fields</p>
          </div>
          <Database className="h-6 w-6 text-blue-500" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-green-600">{progress.mapped}</h3>
            <p className="text-xs text-gray-600">Mapped</p>
          </div>
          <CheckCircle className="h-6 w-6 text-green-500" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-purple-600">{progress.critical_mapped}</h3>
            <p className="text-xs text-gray-600">Critical Mapped</p>
          </div>
          <Target className="h-6 w-6 text-purple-500" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-indigo-600">
              {Math.round(progress.accuracy)}%
            </h3>
            <p className="text-xs text-gray-600">Accuracy</p>
          </div>
          <Brain className="h-6 w-6 text-indigo-500" />
        </div>
      </div>
    </div>
  );
};

export default ProgressDashboard;
