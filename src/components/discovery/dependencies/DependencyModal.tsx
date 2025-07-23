import React from 'react'
import type { useState } from 'react'
import { useEffect } from 'react'

interface DependencyModalProps {
  selectedDependency: unknown;
  showModal: boolean;
  onClose: () => void;
  onSave: (dependency: unknown) => void;
  onDelete?: (dependency: unknown) => void;
}

export const DependencyModal: React.FC<DependencyModalProps> = ({
  selectedDependency,
  showModal,
  onClose,
  onSave,
  onDelete
}) => {
  const [editedDependency, setEditedDependency] = useState(selectedDependency);

  useEffect(() => {
    setEditedDependency(selectedDependency);
  }, [selectedDependency]);

  if (!showModal || !selectedDependency) {
    return null;
  }

  const handleSave = () => {
    onSave(editedDependency);
    onClose();
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(editedDependency);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-90vh overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {editedDependency?.source_app ? 'Edit Dependency' : 'Add New Dependency'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Source Application */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source Application
            </label>
            <input
              type="text"
              value={editedDependency?.source_app?.name || ''}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                source_app: {
                  ...editedDependency?.source_app,
                  name: e.target.value
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Enter source application name"
            />
          </div>
          
          {/* Target Application */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Application
            </label>
            <input
              type="text"
              value={editedDependency?.target_app?.name || ''}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                target_app: {
                  ...editedDependency?.target_app,
                  name: e.target.value
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Enter target application name"
            />
          </div>
          
          {/* Dependency Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dependency Type
            </label>
            <select
              value={editedDependency?.dependency?.dependency_type || 'application_to_server'}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                dependency: {
                  ...editedDependency?.dependency,
                  dependency_type: e.target.value
                }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="application_to_server">Application to Server</option>
              <option value="application_dependency">Application Dependency</option>
              <option value="database_connection">Database Connection</option>
              <option value="network_dependency">Network Dependency</option>
              <option value="infrastructure_dependency">Infrastructure Dependency</option>
            </select>
          </div>
          
          {/* Impact Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Impact Level
            </label>
            <select
              value={editedDependency?.impact_level || 'medium'}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                impact_level: e.target.value
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          
          {/* Confidence */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confidence ({Math.round((editedDependency?.dependency?.confidence || 0) * 100)}%)
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={editedDependency?.dependency?.confidence || 0}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                dependency: {
                  ...editedDependency?.dependency,
                  confidence: parseFloat(e.target.value)
                }
              })}
              className="w-full"
            />
          </div>
          
          {/* Business Impact */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Business Impact (Optional)
            </label>
            <textarea
              value={editedDependency?.business_impact || ''}
              onChange={(e) => setEditedDependency({
                ...editedDependency,
                business_impact: e.target.value
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Describe the business impact of this dependency"
            />
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end space-x-4">
          {onDelete && (
            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 transition-colors"
            >
              Delete Dependency
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}; 