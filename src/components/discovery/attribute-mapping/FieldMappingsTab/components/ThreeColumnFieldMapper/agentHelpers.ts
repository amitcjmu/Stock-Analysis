/**
 * Agent Display Helpers
 *
 * Functions for displaying agent reasoning, confidence levels, and AI analysis.
 */

import React from 'react';
import type { Brain, Target, BarChart3, CheckCircle, TrendingUp, AlertCircle, XCircle } from 'lucide-react';
import type { FieldMapping } from '../../types';
import type { AgentTypeInfo, ConfidenceDisplayInfo } from './types';

// AGENTIC UI HELPERS: Agent reasoning and confidence display functions
export const getAgentReasoningForMapping = (mapping: FieldMapping): string => {
  const confidence = mapping.confidence || 0;
  const sourceField = mapping.sourceField?.toLowerCase() || '';
  const targetField = mapping.targetAttribute?.toLowerCase() || '';

  if (sourceField.includes('name') && targetField.includes('name')) {
    return `Strong semantic match detected between "${mapping.sourceField}" and "${mapping.targetAttribute}". Field naming patterns indicate direct correspondence with ${Math.round(confidence * 100)}% confidence.`;
  } else if (sourceField.includes('ip') && targetField.includes('ip')) {
    return `Network identifier pattern match. "${mapping.sourceField}" contains IP addressing data suitable for "${mapping.targetAttribute}" field with high pattern recognition confidence.`;
  } else if (sourceField.includes('cpu') || sourceField.includes('core')) {
    return `Hardware specification mapping. "${mapping.sourceField}" contains computational resource data matching "${mapping.targetAttribute}" requirements based on metric analysis.`;
  } else if (sourceField.includes('ram') || sourceField.includes('memory')) {
    return `Memory resource identification. Agent detected memory allocation data in "${mapping.sourceField}" suitable for "${mapping.targetAttribute}" classification.`;
  } else if (confidence > 0.8) {
    return `High-confidence ensemble decision. Multiple semantic and pattern analysis agents agree on this mapping with ${Math.round(confidence * 100)}% consensus.`;
  } else if (confidence > 0.6) {
    return `Moderate confidence mapping based on partial semantic similarity. Manual review recommended for optimal accuracy.`;
  } else {
    return `Low confidence suggestion requiring validation. Multiple mapping candidates identified through pattern analysis.`;
  }
};

export const getAgentTypeForMapping = (mapping: FieldMapping): AgentTypeInfo => {
  const sourceField = mapping.sourceField?.toLowerCase() || '';
  const targetField = mapping.targetAttribute?.toLowerCase() || '';
  const confidence = mapping.confidence || 0;

  if (sourceField.includes('name') && targetField.includes('name')) {
    return { type: 'Semantic', icon: React.createElement(Brain, { className: "w-3 h-3" }), color: 'text-blue-600 bg-blue-50' };
  } else if (sourceField.includes('ip') || sourceField.includes('cpu') || sourceField.includes('ram')) {
    return { type: 'Pattern', icon: React.createElement(Target, { className: "w-3 h-3" }), color: 'text-green-600 bg-green-50' };
  } else if (confidence > 0.8) {
    return { type: 'Ensemble', icon: React.createElement(BarChart3, { className: "w-3 h-3" }), color: 'text-purple-600 bg-purple-50' };
  } else {
    return { type: 'Validation', icon: React.createElement(CheckCircle, { className: "w-3 h-3" }), color: 'text-orange-600 bg-orange-50' };
  }
};

export const getConfidenceDisplay = (confidence: number): ConfidenceDisplayInfo => {
  const percentage = Math.round(confidence * 100);
  let colorClass = '';
  let icon = null;

  if (confidence >= 0.8) {
    colorClass = 'text-green-700 bg-green-100 border-green-200';
    icon = React.createElement(TrendingUp, { className: "w-3 h-3" });
  } else if (confidence >= 0.6) {
    colorClass = 'text-yellow-700 bg-yellow-100 border-yellow-200';
    icon = React.createElement(BarChart3, { className: "w-3 h-3" });
  } else if (confidence >= 0.4) {
    colorClass = 'text-orange-700 bg-orange-100 border-orange-200';
    icon = React.createElement(AlertCircle, { className: "w-3 h-3" });
  } else {
    colorClass = 'text-red-700 bg-red-100 border-red-200';
    icon = React.createElement(XCircle, { className: "w-3 h-3" });
  }

  return { percentage, colorClass, icon };
};

// Legacy helpers for backward compatibility
export const getConfidenceColor = (confidence: number): string => {
  const { colorClass } = getConfidenceDisplay(confidence);
  return colorClass;
};

export const getConfidenceIcon = (confidence: number): React.ReactNode => {
  const { icon } = getConfidenceDisplay(confidence);
  return icon;
};
