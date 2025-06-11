import React from 'react';

interface ProgressBarProps {
  percentage: number;
  color?: string;
  height?: 'sm' | 'md' | 'lg';
  className?: string;
}

const heightMap = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

const ProgressBar: React.FC<ProgressBarProps> = ({
  percentage,
  color = 'bg-blue-500',
  height = 'md',
  className = '',
}) => {
  const heightClass = heightMap[height];
  const safePercentage = Math.min(100, Math.max(0, percentage));

  return (
    <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClass} ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-300 ${color}`}
        style={{ width: `${safePercentage}%` }}
        role="progressbar"
        aria-valuenow={safePercentage}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span className="sr-only">{safePercentage}% complete</span>
      </div>
    </div>
  );
};

export default ProgressBar;
