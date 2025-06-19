import React from 'react';
import { Brain } from 'lucide-react';
import Sidebar from '../../Sidebar';
import NoDataPlaceholder from '../../NoDataPlaceholder';

interface AttributeMappingStateProviderProps {
  isLoading: boolean;
  hasError: boolean;
  errorMessage?: string;
  hasData: boolean;
  onTriggerAnalysis: () => void;
  isAnalyzing: boolean;
  children: React.ReactNode;
}

const AttributeMappingStateProvider: React.FC<AttributeMappingStateProviderProps> = ({
  isLoading,
  hasError,
  errorMessage,
  hasData,
  onTriggerAnalysis,
  isAnalyzing,
  children
}) => {
  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Brain className="h-12 w-12 text-blue-600 animate-pulse mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Loading Attribute Mapping Analysis
            </h2>
            <p className="text-gray-600">
              Fetching field mapping analysis...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="Discovery Flow Error"
            description={`Failed to initialize Discovery Flow: ${errorMessage}`}
            actions={
              <button 
                onClick={onTriggerAnalysis}
                disabled={isAnalyzing}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <span>{isAnalyzing ? 'Analyzing...' : 'Retry Analysis'}</span>
              </button>
            }
          />
        </div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <NoDataPlaceholder
            title="No Field Mapping Available"
            description="No field mapping data available. Please import data or trigger field mapping analysis."
            actions={
              <button 
                onClick={onTriggerAnalysis}
                disabled={isAnalyzing}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Field Mapping'}</span>
              </button>
            }
          />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default AttributeMappingStateProvider; 