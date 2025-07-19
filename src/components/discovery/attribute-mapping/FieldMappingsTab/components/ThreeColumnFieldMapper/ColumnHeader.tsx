/**
 * Column Header Component
 * 
 * Reusable header component for the three-column layout.
 */

import React from 'react';
import { ColumnHeaderProps } from './types';

const ColumnHeader: React.FC<ColumnHeaderProps> = ({ title, count, icon, bgColor }) => (
  <div className={`${bgColor} p-4 rounded-lg mb-4`}>
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <span className="bg-white px-2 py-1 rounded-full text-sm font-medium text-gray-600">
        {count}
      </span>
    </div>
  </div>
);

export default ColumnHeader;