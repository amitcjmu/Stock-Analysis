export const matchesDateRange = (analysisDate: Date, dateRange: string): boolean => {
  if (dateRange === 'all') return true;

  const now = new Date();
  const date = new Date(analysisDate);
  const timeDiff = now.getTime() - date.getTime();

  switch (dateRange) {
    case 'week':
      return timeDiff <= 7 * 24 * 60 * 60 * 1000;
    case 'month':
      return timeDiff <= 30 * 24 * 60 * 60 * 1000;
    case 'quarter':
      return timeDiff <= 90 * 24 * 60 * 60 * 1000;
    default:
      return true;
  }
};

export const formatDate = (date: Date): string => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};
