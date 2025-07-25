/**
 * Shared formatting utilities for observability components
 */

export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatDuration = (seconds: number): string => {
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(0)}ms`;
  } else if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

export const formatMemory = (mb: number): string => {
  if (mb < 1024) {
    return `${mb.toFixed(1)} MB`;
  } else {
    return `${(mb / 1024).toFixed(2)} GB`;
  }
};

export const formatNumber = (value: number): string => {
  if (value < 1000) {
    return value.toString();
  } else if (value < 1000000) {
    return `${(value / 1000).toFixed(1)}K`;
  } else {
    return `${(value / 1000000).toFixed(1)}M`;
  }
};

export const formatTimestamp = (timestamp: string | Date): string => {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
};

export const formatThroughput = (tasksPerHour: number): string => {
  if (tasksPerHour < 1) {
    return `${(tasksPerHour * 60).toFixed(1)}/min`;
  } else {
    return `${tasksPerHour.toFixed(1)}/hr`;
  }
};

export const formatConfidenceScore = (score: number): string => {
  const percentage = score * 100;
  if (percentage >= 90) {
    return `${percentage.toFixed(0)}% (High)`;
  } else if (percentage >= 70) {
    return `${percentage.toFixed(0)}% (Medium)`;
  } else {
    return `${percentage.toFixed(0)}% (Low)`;
  }
};

export const calculateImprovement = (current: number, projected: number): string => {
  const improvement = ((projected - current) / current) * 100;
  const sign = improvement > 0 ? '+' : '';
  return `${sign}${improvement.toFixed(1)}%`;
};

export const exportToJSON = (data: Record<string, unknown>, filename: string): void => {
  const dataStr = JSON.stringify(data, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.json`;
  link.click();
  URL.revokeObjectURL(url);
};
