import React from 'react';
import { RefreshCw } from 'lucide-react';

interface DataCleansingHeaderProps {
  isAnalyzing: boolean;
  rawDataLength: number;
  onRefreshAnalysis: () => void;
}

const DataCleansingHeader: React.FC<DataCleansingHeaderProps> = ({
  isAnalyzing,
  rawDataLength,
  onRefreshAnalysis
}) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Agentic Data Cleansing
          </h1>
          <p className="text-lg text-gray-600">
            AI-powered data quality assessment and intelligent cleanup recommendations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={onRefreshAnalysis}
            disabled={isAnalyzing || rawDataLength === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>Refresh Analysis</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataCleansingHeader; 