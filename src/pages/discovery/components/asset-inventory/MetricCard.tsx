import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color?: string;
  subtitle?: string;
  trend?: {
    value: number;
    label: string;
    positiveIsGood?: boolean;
  };
  className?: string;
  onClick?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  color = 'text-blue-600',
  subtitle,
  trend,
  className = '',
  onClick,
}) => {
  const isPositive = trend ? (trend.value >= 0) : false;
  const trendColor = trend ? (
    isPositive === (trend.positiveIsGood ?? true) ? 'text-green-600' : 'text-red-600'
  ) : '';

  return (
    <div 
      className={cn(
        'bg-white rounded-lg shadow-sm border border-gray-200 p-6 transition-all duration-200',
        onClick ? 'hover:shadow-md hover:border-gray-300 cursor-pointer' : '',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline mt-1">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {trend && (
              <span className={cn('ml-2 text-sm font-medium', trendColor)}>
                {trend.value > 0 ? '↑' : trend.value < 0 ? '↓' : '→'} {Math.abs(trend.value)}% {trend.label}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-gray-500 mt-1.5">{subtitle}</p>}
        </div>
        <div className={cn('p-2.5 rounded-lg', color.replace('text-', 'bg-').replace('-600', '-100'))}>
          {React.cloneElement(icon as React.ReactElement, { className: 'h-5 w-5' })}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
