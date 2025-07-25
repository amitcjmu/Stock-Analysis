/**
 * Utility Functions
 *
 * Helper functions for styling and formatting.
 */

import React from 'react';
import { CheckCircle, AlertCircle, HelpCircle } from 'lucide-react';

export const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'high': return 'border-red-500 bg-red-50';
    case 'medium': return 'border-yellow-500 bg-yellow-50';
    case 'low': return 'border-green-500 bg-green-50';
    default: return 'border-gray-300 bg-gray-50';
  }
};

export const getConfidenceIcon = (confidence: string): React.ReactElement => {
  switch (confidence) {
    case 'high': return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'medium': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    case 'low': return <HelpCircle className="w-4 h-4 text-orange-500" />;
    case 'uncertain': return <AlertCircle className="w-4 h-4 text-red-500" />;
    default: return <HelpCircle className="w-4 h-4 text-gray-500" />;
  }
};

export const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const getPriorityBadgeClass = (priority: string): string => {
  switch (priority) {
    case 'high': return 'bg-red-100 text-red-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'low': return 'bg-green-100 text-green-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export const getCriticalityColor = (criticality: string): string => {
  switch (criticality?.toLowerCase()) {
    case 'critical': return 'text-red-600';
    case 'high': return 'text-orange-600';
    case 'medium': return 'text-yellow-600';
    default: return 'text-green-600';
  }
};
