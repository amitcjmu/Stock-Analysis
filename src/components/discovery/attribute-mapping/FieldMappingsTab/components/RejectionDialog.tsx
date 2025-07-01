import React, { useState } from 'react';
import { RejectionDialogProps } from '../types';

export const RejectionDialog: React.FC<RejectionDialogProps> = ({
  isOpen,
  mappingId,
  sourceField,
  targetField,
  onConfirm,
  onCancel
}) => {
  const [reason, setReason] = useState('');
  const [selectedReason, setSelectedReason] = useState('');

  const commonReasons = [
    'Incorrect field mapping',
    'Wrong data type',
    'Field not relevant for migration',
    'Better alternative available',
    'Data quality concerns',
    'Security/privacy concerns',
    'Custom field needed'
  ];

  const handleConfirm = () => {
    const finalReason = selectedReason || reason || 'User rejected this mapping';
    onConfirm(finalReason);
    setReason('');
    setSelectedReason('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold mb-4">Reject Field Mapping</h3>
        <p className="text-gray-600 mb-4">
          Why are you rejecting the mapping of <strong>{sourceField}</strong> to <strong>{targetField}</strong>?
        </p>
        
        <div className="space-y-3 mb-4">
          <label className="block text-sm font-medium text-gray-700">Common reasons:</label>
          {commonReasons.map((commonReason) => (
            <label key={commonReason} className="flex items-center">
              <input
                type="radio"
                name="rejectionReason"
                value={commonReason}
                checked={selectedReason === commonReason}
                onChange={(e) => setSelectedReason(e.target.value)}
                className="mr-2"
              />
              <span className="text-sm">{commonReason}</span>
            </label>
          ))}
          <label className="flex items-center">
            <input
              type="radio"
              name="rejectionReason"
              value="custom"
              checked={selectedReason === 'custom'}
              onChange={(e) => setSelectedReason(e.target.value)}
              className="mr-2"
            />
            <span className="text-sm">Other (specify below)</span>
          </label>
        </div>

        {selectedReason === 'custom' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom reason:
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
              rows={3}
              placeholder="Please explain why you're rejecting this mapping..."
            />
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Reject Mapping
          </button>
        </div>
      </div>
    </div>
  );
};