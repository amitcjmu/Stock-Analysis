import React from 'react';
import { Inbox } from 'lucide-react';

interface NoDataPlaceholderProps {
  title: string;
  description: string;
  actions?: React.ReactNode;
}

const NoDataPlaceholder: React.FC<NoDataPlaceholderProps> = ({ title, description, actions }) => {
  return (
    <div className="text-center bg-white rounded-lg shadow-md p-12">
      <Inbox className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-2 text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
      {actions && (
        <div className="mt-6">
          {actions}
        </div>
      )}
    </div>
  );
};

export default NoDataPlaceholder;
