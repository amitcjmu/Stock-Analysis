import React from 'react';
import type { VersionDisplayProps } from './types';

const VersionDisplay: React.FC<VersionDisplayProps> = ({
  versionInfo,
  onVersionClick
}) => {
  return (
    <div
      className="text-xs text-gray-400 text-center cursor-pointer hover:text-blue-400 transition-colors duration-200 py-2 px-3 rounded-lg hover:bg-gray-700"
      onClick={onVersionClick}
      title="Click to view feedback and reports"
    >
      {versionInfo.fullVersion}
      <div className="text-[10px] text-gray-500 mt-1">
        Click for feedback
      </div>
    </div>
  );
};

export default VersionDisplay;
