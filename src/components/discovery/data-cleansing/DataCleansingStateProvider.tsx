import React from 'react';
import { Brain } from 'lucide-react';
import Sidebar from '../../Sidebar';
import NoDataPlaceholder from '../../NoDataPlaceholder';

interface DataCleansingStateProviderProps {
  isLoading: boolean;
  hasError: boolean;
  errorMessage?: string;
  hasData: boolean;
  onBackToAttributeMapping: () => void;
  onTriggerAnalysis: () => void;
  isAnalyzing: boolean;
  children: React.ReactNode;
}

const DataCleansingStateProvider: React.FC<DataCleansingStateProviderProps> = ({
  isLoading,
  hasError,
  errorMessage,
  hasData,
  onBackToAttributeMapping,
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
              Loading Data Cleansing Analysis
            </h2>
            <p className="text-gray-600">
              Fetching data quality analysis...
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
                onClick={onBackToAttributeMapping}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <span>Return to Attribute Mapping</span>
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
            title="No Data Available for Cleansing"
            description="The Data Cleansing phase requires data from previous phases. Please ensure you have completed data import and field mapping, or that your discovery flow is properly configured with data."
            actions={
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={onBackToAttributeMapping}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <span>Go to Attribute Mapping</span>
                </button>
                <button
                  onClick={onTriggerAnalysis}
                  disabled={isAnalyzing}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <span>{isAnalyzing ? 'Re-analyze Flow' : 'Trigger Analysis'}</span>
                </button>
              </div>
            }
          />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default DataCleansingStateProvider;
