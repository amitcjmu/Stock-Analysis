import React from 'react';

interface StatusFiltersProps {
  visibleStatuses: Record<string, boolean>;
  onStatusToggle: (status: string) => void;
}

export const StatusFilters: React.FC<StatusFiltersProps> = ({
  visibleStatuses,
  onStatusToggle
}) => {
  const statusInfo = [
    { key: 'pending', label: 'Pending Review', color: 'text-blue-600' },
    { key: 'approved', label: 'Approved', color: 'text-green-600' },
    { key: 'rejected', label: 'Rejected', color: 'text-red-600' }
  ];

  return (
    <div className="flex flex-wrap gap-4 mb-4">
      <span className="text-sm font-medium text-gray-700">Show:</span>
      {statusInfo.map((status) => (
        <label key={status.key} className="flex items-center">
          <input
            type="checkbox"
            checked={visibleStatuses[status.key]}
            onChange={() => onStatusToggle(status.key)}
            className="mr-2"
          />
          <span className={`text-sm ${status.color}`}>
            {status.label}
          </span>
        </label>
      ))}
    </div>
  );
};
