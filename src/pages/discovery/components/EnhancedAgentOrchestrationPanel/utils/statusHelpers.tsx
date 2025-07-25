import type React from 'react';
import { Activity } from 'lucide-react'
import { CheckCircle2, Clock, AlertCircle, Timer } from 'lucide-react'
import { Badge } from '@/components/ui/badge';

export const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case 'running':
    case 'active':
      return <Clock className="h-4 w-4 text-blue-500" />;
    case 'failed':
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Timer className="h-4 w-4 text-gray-400" />;
  }
};

export const getStatusBadge = (status: string) => {
  const statusConfig = {
    completed: { variant: 'default' as const, className: 'bg-green-100 text-green-800' },
    running: { variant: 'secondary' as const, className: 'bg-blue-100 text-blue-800' },
    active: { variant: 'secondary' as const, className: 'bg-blue-100 text-blue-800' },
    failed: { variant: 'destructive' as const, className: '' },
    error: { variant: 'destructive' as const, className: '' },
    pending: { variant: 'outline' as const, className: '' },
    idle: { variant: 'outline' as const, className: '' }
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

  return (
    <Badge variant={config.variant} className={config.className}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
};

export const getProgressColor = (progress: number): string => {
  if (progress >= 80) return 'bg-green-500';
  if (progress >= 50) return 'bg-blue-500';
  if (progress >= 20) return 'bg-yellow-500';
  return 'bg-gray-400';
};
