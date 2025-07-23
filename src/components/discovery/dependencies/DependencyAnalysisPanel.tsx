import React from 'react';
import { Card } from '../../ui/card';
import { DependencyData } from '../../../types/dependency';
import { Loader2 } from 'lucide-react';

interface DependencyAnalysisPanelProps {
  data: DependencyData | null;
  isLoading: boolean;
  activeView: 'app-server' | 'app-app';
}

const DependencyAnalysisPanel: React.FC<DependencyAnalysisPanelProps> = ({
  data,
  isLoading,
  activeView
}) => {
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          <span className="ml-3 text-gray-500">Analyzing dependencies...</span>
        </div>
      </Card>
    );
  }

  if (!data) return null;

  const renderAppServerAnalysis = () => {
    const { hosting_relationships = [], suggested_mappings = [], confidence_scores = {} } = data?.app_server_mapping || {};
    const confirmedCount = hosting_relationships.filter(r => r?.status === 'confirmed').length;
    const pendingCount = hosting_relationships.filter(r => r?.status === 'pending').length;
    const confidenceValues = Object.values(confidence_scores || {});
    const averageConfidence = confidenceValues.length > 0 ? confidenceValues.reduce((a, b) => (a || 0) + (b || 0), 0) / confidenceValues.length : 0;

    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium mb-2">Hosting Relationships</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{confirmedCount}</div>
              <div className="text-sm text-green-700">Confirmed</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
              <div className="text-sm text-yellow-700">Pending</div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2">Suggested Mappings</h3>
          <div className="space-y-2">
            {suggested_mappings.slice(0, 3).map((mapping, index) => (
              <div key={index} className="bg-blue-50 p-2 rounded-lg">
                <div className="text-sm font-medium text-blue-700">
                  {mapping?.application_name || 'Unknown'} → {mapping?.server_name || 'Unknown'}
                </div>
                <div className="text-xs text-blue-600">
                  Confidence: {Math.round((mapping?.confidence || 0) * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2">Analysis Confidence</h3>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round(averageConfidence * 100)}%
            </div>
            <div className="text-sm text-purple-700">Average Confidence</div>
          </div>
        </div>
      </div>
    );
  };

  const renderAppAppAnalysis = () => {
    const { cross_app_dependencies = [], application_clusters = [], suggested_patterns = [], confidence_scores = {} } = data?.cross_application_mapping || {};
    const confirmedCount = cross_app_dependencies.filter(d => d?.status === 'confirmed').length;
    const pendingCount = cross_app_dependencies.filter(d => d?.status === 'pending').length;
    const confidenceValues = Object.values(confidence_scores || {});
    const averageConfidence = confidenceValues.length > 0 ? confidenceValues.reduce((a, b) => (a || 0) + (b || 0), 0) / confidenceValues.length : 0;

    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium mb-2">Application Dependencies</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{confirmedCount}</div>
              <div className="text-sm text-green-700">Confirmed</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
              <div className="text-sm text-yellow-700">Pending</div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2">Application Clusters</h3>
          <div className="space-y-2">
            {application_clusters.slice(0, 3).map((cluster, index) => (
              <div key={index} className="bg-blue-50 p-2 rounded-lg">
                <div className="text-sm font-medium text-blue-700">
                  {cluster?.cluster_type || 'Cluster'} ({(cluster?.applications || []).length} apps)
                </div>
                <div className="text-xs text-blue-600">
                  Confidence: {Math.round((cluster?.confidence || 0) * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2">Analysis Confidence</h3>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round(averageConfidence * 100)}%
            </div>
            <div className="text-sm text-purple-700">Average Confidence</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className="p-4">
      <h2 className="text-lg font-semibold mb-4">Analysis Results</h2>
      {activeView === 'app-server' ? renderAppServerAnalysis() : renderAppAppAnalysis()}
    </Card>
  );
};

export default DependencyAnalysisPanel; 