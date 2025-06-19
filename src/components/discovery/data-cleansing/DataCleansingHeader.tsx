import React from 'react';
import { Button } from '../../ui/button';
import { Database, Activity, RefreshCw, Zap } from 'lucide-react';

interface DataCleansingHeaderProps {
  totalRecords: number;
  qualityScore: number;
  completionPercentage: number;
  issuesCount: number;
  recommendationsCount: number;
  isAnalyzing: boolean;
  isLoading: boolean;
  onRefresh: () => void;
  onTriggerAnalysis: () => void;
}

const DataCleansingHeader: React.FC<DataCleansingHeaderProps> = ({
  totalRecords,
  qualityScore,
  completionPercentage,
  issuesCount,
  recommendationsCount,
  isAnalyzing,
  isLoading,
  onRefresh,
  onTriggerAnalysis
}) => {
  const getQualityScoreClass = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800 border border-green-200';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
    return 'bg-red-100 text-red-800 border border-red-200';
  };

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center space-x-3">
        <Database className="h-8 w-8 text-green-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Cleansing & Quality Analysis</h1>
          <p className="text-gray-600">
            {totalRecords > 0 
              ? `${totalRecords} records analyzed with ${issuesCount} quality issues found and ${recommendationsCount} improvement recommendations` 
              : 'AI-powered data quality analysis and standardization recommendations'
            }
          </p>
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        {/* Quality Score */}
        {qualityScore > 0 && (
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium ${getQualityScoreClass(qualityScore)}`}>
            <Activity className="h-4 w-4" />
            <span>{qualityScore}% Quality Score</span>
          </div>
        )}
        
        {/* Completion Status */}
        {completionPercentage > 0 && (
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
            <span className="font-medium">{completionPercentage}% Complete</span>
          </div>
        )}
        
        {/* Manual Refresh Button */}
        <Button
          onClick={onRefresh}
          disabled={isLoading}
          variant="outline"
          className="flex items-center space-x-2"
        >
          {isLoading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span>Refresh Analysis</span>
        </Button>
        
        {/* Crew Analysis Button */}
        <Button
          onClick={onTriggerAnalysis}
          disabled={isAnalyzing}
          className="flex items-center space-x-2"
        >
          {isAnalyzing ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Zap className="h-4 w-4" />
          )}
          <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Analysis'}</span>
        </Button>
      </div>
    </div>
  );
};

export default DataCleansingHeader; 