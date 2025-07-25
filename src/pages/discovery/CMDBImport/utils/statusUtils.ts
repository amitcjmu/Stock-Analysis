import {
  Loader2,
  Brain,
  Cog,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  FileCheck
} from 'lucide-react';

export const getStatusIcon = (status: string) => {
  switch (status) {
    case 'uploading': return Loader2;
    case 'validating': return Brain;
    case 'processing': return Cog;
    case 'approved': return CheckCircle;
    case 'approved_with_warnings': return AlertTriangle;
    case 'rejected': return AlertTriangle;
    case 'error': return AlertCircle;
    default: return FileCheck;
  }
};

export const getStatusColor = (status: string) => {
  switch (status) {
    case 'uploading': return 'bg-blue-100 text-blue-800';
    case 'validating': return 'bg-orange-100 text-orange-800';
    case 'processing': return 'bg-purple-100 text-purple-800';
    case 'approved': return 'bg-green-100 text-green-800';
    case 'approved_with_warnings': return 'bg-yellow-100 text-yellow-800';
    case 'rejected': return 'bg-red-100 text-red-800';
    case 'error': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export const getStatusStyling = (status: string) => {
  switch (status) {
    case 'passed':
      return {
        bg: 'bg-green-50 border-green-200',
        icon: 'text-green-600',
        text: 'text-green-900'
      };
    case 'failed':
      return {
        bg: 'bg-red-50 border-red-200',
        icon: 'text-red-600',
        text: 'text-red-900'
      };
    case 'warning':
      return {
        bg: 'bg-yellow-50 border-yellow-200',
        icon: 'text-yellow-600',
        text: 'text-yellow-900'
      };
    default:
      return {
        bg: 'bg-gray-50 border-gray-200',
        icon: 'text-gray-400',
        text: 'text-gray-600'
      };
  }
};
