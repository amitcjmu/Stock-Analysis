import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  className?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ className }) => {
  return (
    <div className="p-6 space-y-6">
      {/* Header Skeleton */}
      <div className="space-y-4">
        <div className="h-8 w-1/3 bg-gray-200 rounded-md animate-pulse" />
        <div className="h-4 w-2/3 bg-gray-200 rounded-md animate-pulse" />
      </div>

      {/* Content Skeletons */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-white p-6 rounded-lg shadow-sm"
          >
            <div className="h-4 w-2/3 bg-gray-200 rounded-md animate-pulse mb-2" />
            <div className="h-8 w-1/3 bg-gray-200 rounded-md animate-pulse" />
          </div>
        ))}
      </div>

      {/* List Skeletons */}
      <div className={`space-y-4 ${className || ''}`}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white p-6 rounded-lg shadow-sm"
          >
            <div className="flex items-center space-x-4">
              <div className="h-12 w-12 bg-gray-200 rounded-full animate-pulse" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 bg-gray-200 rounded-md animate-pulse" />
                <div className="h-4 w-1/2 bg-gray-200 rounded-md animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoadingSkeleton; 