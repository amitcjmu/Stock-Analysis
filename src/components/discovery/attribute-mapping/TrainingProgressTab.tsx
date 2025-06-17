import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertCircle, CheckCircle, Clock, Target, Users, Bot } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall, API_CONFIG } from '../../../config/api';

interface TrainingProgressTabProps {
  className?: string;
}

interface TrainingMetrics {
  total_mappings: number;
  ai_successful: number;
  human_intervention: number;
  pending_review: number;
  accuracy_score: number;
  confidence_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  learning_improvements: {
    pattern_recognition: number;
    field_matching: number;
    confidence_calibration: number;
  };
}

interface MappingQuality {
  field_name: string;
  ai_confidence: number;
  human_validated: boolean;
  accuracy_score: number;
  intervention_reason?: string;
  learning_applied: boolean;
}

const TrainingProgressTab: React.FC<TrainingProgressTabProps> = ({ className = "" }) => {
  const { getAuthHeaders } = useAuth();
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics | null>(null);
  const [mappingQuality, setMappingQuality] = useState<MappingQuality[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrainingProgress();
  }, []);

  const fetchTrainingProgress = async () => {
    try {
      setIsLoading(true);
      
      const authHeaders = getAuthHeaders();
      
      // Mock training progress data since the backend endpoint might not exist yet
      const mockMetrics: TrainingMetrics = {
        total_mappings: 18,
        ai_successful: 14,
        human_intervention: 3,
        pending_review: 1,
        accuracy_score: 0.87,
        confidence_distribution: {
          high: 12,
          medium: 4,
          low: 2
        },
        learning_improvements: {
          pattern_recognition: 0.15,
          field_matching: 0.22,
          confidence_calibration: 0.08
        }
      };

      const mockQuality: MappingQuality[] = [
        { field_name: "hostname", ai_confidence: 0.95, human_validated: true, accuracy_score: 0.98, learning_applied: true },
        { field_name: "ip_address", ai_confidence: 0.92, human_validated: true, accuracy_score: 0.95, learning_applied: true },
        { field_name: "operating_system", ai_confidence: 0.88, human_validated: true, accuracy_score: 0.90, learning_applied: false },
        { field_name: "business_owner", ai_confidence: 0.45, human_validated: false, accuracy_score: 0.60, intervention_reason: "Ambiguous field mapping", learning_applied: false },
        { field_name: "department", ai_confidence: 0.52, human_validated: false, accuracy_score: 0.65, intervention_reason: "Multiple valid mappings", learning_applied: false },
        { field_name: "environment", ai_confidence: 0.78, human_validated: true, accuracy_score: 0.85, learning_applied: true }
      ];

      setTrainingMetrics(mockMetrics);
      setMappingQuality(mockQuality);
      
    } catch (err) {
      console.error('Error fetching training progress:', err);
      setError('Failed to load training progress');
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return 'text-green-600';
    if (accuracy >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Brain className="w-6 h-6 animate-pulse text-purple-500 mr-2" />
          <span className="text-gray-600">Loading training progress...</span>
        </div>
      </div>
    );
  }

  if (error || !trainingMetrics) {
    return (
      <div className={`bg-white rounded-lg border shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center py-8 text-red-600">
          <AlertCircle className="w-6 h-6 mr-2" />
          <span>{error || 'No training data available'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 className="font-medium text-gray-900">Training Progress</h3>
          <span className="text-sm text-gray-500">
            AI Learning & Human Collaboration
          </span>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900">Total Mappings</p>
                <p className="text-2xl font-bold text-blue-600">{trainingMetrics.total_mappings}</p>
              </div>
              <Target className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-900">AI Successful</p>
                <p className="text-2xl font-bold text-green-600">{trainingMetrics.ai_successful}</p>
                <p className="text-xs text-green-700">
                  {Math.round((trainingMetrics.ai_successful / trainingMetrics.total_mappings) * 100)}% success rate
                </p>
              </div>
              <Bot className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-900">Human Needed</p>
                <p className="text-2xl font-bold text-orange-600">{trainingMetrics.human_intervention}</p>
                <p className="text-xs text-orange-700">Requires review</p>
              </div>
              <Users className="w-8 h-8 text-orange-500" />
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-900">Overall Accuracy</p>
                <p className="text-2xl font-bold text-purple-600">
                  {Math.round(trainingMetrics.accuracy_score * 100)}%
                </p>
                <p className="text-xs text-purple-700">AI performance</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="mb-8">
          <h4 className="font-medium text-gray-900 mb-4">Confidence Distribution</h4>
          <div className="space-y-3">
            <div className="flex items-center">
              <span className="w-16 text-sm text-gray-600">High</span>
              <div className="flex-1 mx-4 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${(trainingMetrics.confidence_distribution.high / trainingMetrics.total_mappings) * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{trainingMetrics.confidence_distribution.high} mappings</span>
            </div>
            <div className="flex items-center">
              <span className="w-16 text-sm text-gray-600">Medium</span>
              <div className="flex-1 mx-4 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-yellow-500 h-2 rounded-full" 
                  style={{ width: `${(trainingMetrics.confidence_distribution.medium / trainingMetrics.total_mappings) * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{trainingMetrics.confidence_distribution.medium} mappings</span>
            </div>
            <div className="flex items-center">
              <span className="w-16 text-sm text-gray-600">Low</span>
              <div className="flex-1 mx-4 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full" 
                  style={{ width: `${(trainingMetrics.confidence_distribution.low / trainingMetrics.total_mappings) * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{trainingMetrics.confidence_distribution.low} mappings</span>
            </div>
          </div>
        </div>

        {/* Learning Improvements */}
        <div className="mb-8">
          <h4 className="font-medium text-gray-900 mb-4">Learning Improvements</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Pattern Recognition</span>
                <span className="text-sm text-green-600">+{Math.round(trainingMetrics.learning_improvements.pattern_recognition * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${trainingMetrics.learning_improvements.pattern_recognition * 100}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Field Matching</span>
                <span className="text-sm text-green-600">+{Math.round(trainingMetrics.learning_improvements.field_matching * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${trainingMetrics.learning_improvements.field_matching * 100}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Confidence Calibration</span>
                <span className="text-sm text-green-600">+{Math.round(trainingMetrics.learning_improvements.confidence_calibration * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${trainingMetrics.learning_improvements.confidence_calibration * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Field-by-Field Quality */}
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Field Mapping Quality</h4>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Field Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Confidence
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Learning Applied
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {mappingQuality.map((mapping, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {mapping.field_name}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${getConfidenceColor(mapping.ai_confidence)}`}>
                        {Math.round(mapping.ai_confidence * 100)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`font-medium ${getAccuracyColor(mapping.accuracy_score)}`}>
                        {Math.round(mapping.accuracy_score * 100)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {mapping.human_validated ? (
                        <div className="flex items-center text-green-600">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          <span>Validated</span>
                        </div>
                      ) : mapping.intervention_reason ? (
                        <div className="flex items-center text-orange-600">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>Needs Review</span>
                        </div>
                      ) : (
                        <div className="flex items-center text-blue-600">
                          <Bot className="w-4 h-4 mr-1" />
                          <span>AI Mapped</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {mapping.learning_applied ? (
                        <span className="text-green-600">✓ Applied</span>
                      ) : (
                        <span className="text-gray-400">Pending</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingProgressTab; 