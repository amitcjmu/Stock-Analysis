import React from 'react';
import { Users } from 'lucide-react';

interface CrewAnalysis {
  agent: string;
  task: string;
  findings: string[];
  recommendations: string[];
  confidence: number;
}

interface CrewAnalysisPanelProps {
  crewAnalysis: CrewAnalysis[];
}

const CrewAnalysisPanel: React.FC<CrewAnalysisPanelProps> = ({ crewAnalysis }) => {
  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'text-green-600 bg-green-100';
    if (progress >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (crewAnalysis.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Users className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900">AI Crew Analysis</h2>
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {crewAnalysis.map((analysis, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{analysis.agent}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${getProgressColor(analysis.confidence * 100)}`}>
                    {Math.round(analysis.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3 font-medium">{analysis.task}</p>
                
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Findings:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {analysis.findings.map((finding, idx) => (
                      <li key={idx}>• {finding}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="bg-blue-50 border-l-4 border-blue-400 p-3">
                  <h4 className="text-sm font-medium text-blue-800 mb-1">Recommendations:</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    {analysis.recommendations.map((rec, idx) => (
                      <li key={idx}>• {rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CrewAnalysisPanel; 