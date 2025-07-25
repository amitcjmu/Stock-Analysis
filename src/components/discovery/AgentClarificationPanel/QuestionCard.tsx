/**
 * Question Card Component
 *
 * Individual question card with response interface and context display.
 */

import React from 'react'
import { useState } from 'react'
import {
  Send,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Server
} from 'lucide-react';
import type { AgentQuestion, AssetDetails } from './types';
import { getPriorityColor } from './utils'
import { getConfidenceIcon, formatTimestamp, getPriorityBadgeClass } from './utils'
import AssetCard from './AssetCard';

interface QuestionCardProps {
  question: AgentQuestion;
  response: string;
  isSubmitting: boolean;
  expandedQuestion: string | null;
  expandedAssetDetails: Set<string>;
  assetDetails: Record<string, AssetDetails>;
  onResponseChange: (questionId: string, value: string) => void;
  onResponseSubmit: (questionId: string) => void;
  onMultipleChoiceResponse: (questionId: string, option: string) => void;
  onToggleExpanded: (questionId: string) => void;
  onToggleAssetDetails: (componentName: string) => void;
}

const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  response,
  isSubmitting,
  expandedQuestion,
  expandedAssetDetails,
  assetDetails,
  onResponseChange,
  onResponseSubmit,
  onMultipleChoiceResponse,
  onToggleExpanded,
  onToggleAssetDetails
}) => {
  return (
    <div className={`border-l-4 p-4 ${getPriorityColor(question.priority)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="font-medium text-gray-900">{question.agent_name}</span>
            {getConfidenceIcon(question.confidence)}
            <span className="text-xs text-gray-500">
              {formatTimestamp(question.created_at)}
            </span>
            <span className={`text-xs px-2 py-1 rounded-full ${getPriorityBadgeClass(question.priority)}`}>
              {question.priority} priority
            </span>
          </div>

          <h4 className="font-medium text-gray-900 mb-2">{question.title}</h4>
          <p className="text-gray-700 mb-3">{question.question}</p>

          {/* Enhanced Asset Context for Application Boundary Questions */}
          {question.question_type === 'application_boundary' && question.context?.components && (
            <div className="mb-4">
              <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                <Server className="w-4 h-4 mr-2 text-blue-600" />
                Asset Details ({question.context.components.length} component{question.context.components.length !== 1 ? 's' : ''})
              </h5>
              <div className="space-y-3">
                {question.context.components.map((componentName: string) => {
                  const asset = assetDetails[componentName];
                  if (!asset) return null;

                  return (
                    <AssetCard
                      key={componentName}
                      componentName={componentName}
                      asset={asset}
                      isExpanded={expandedAssetDetails.has(componentName)}
                      onToggleExpanded={onToggleAssetDetails}
                    />
                  );
                })}
              </div>
              {question.context.reason && (
                <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <span className="font-medium text-yellow-800">Agent Analysis: </span>
                      <span className="text-yellow-700">{question.context.reason}</span>
                      {question.context.confidence && (
                        <span className="block text-sm text-yellow-600 mt-1">
                          Confidence: {Math.round(question.context.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Multiple Choice Options */}
          {question.options && question.options.length > 0 && (
            <div className="space-y-2 mb-3">
              {question.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => onMultipleChoiceResponse(question.id, option)}
                  disabled={isSubmitting}
                  className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors disabled:opacity-50"
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {/* Text Response Input */}
          {(!question.options || question.options.length === 0) && (
            <div className="flex space-x-2">
              <input
                type="text"
                value={response || ''}
                onChange={(e) => onResponseChange(question.id, e.target.value)}
                placeholder="Type your response..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    onResponseSubmit(question.id);
                  }
                }}
              />
              <button
                onClick={() => onResponseSubmit(question.id)}
                disabled={isSubmitting || !response?.trim()}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          )}

          {/* Context Information */}
          {question.context && Object.keys(question.context).length > 0 && question.question_type !== 'application_boundary' && (
            <button
              onClick={() => onToggleExpanded(question.id)}
              className="mt-3 flex items-center text-sm text-gray-600 hover:text-gray-800"
            >
              {expandedQuestion === question.id ? (
                <ChevronUp className="w-4 h-4 mr-1" />
              ) : (
                <ChevronDown className="w-4 h-4 mr-1" />
              )}
              Show context
            </button>
          )}

          {expandedQuestion === question.id && question.context && question.question_type !== 'application_boundary' && (
            <div className="mt-2 p-3 bg-gray-50 rounded-md">
              <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                {JSON.stringify(question.context, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionCard;
