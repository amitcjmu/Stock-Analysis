import React from 'react';
import { FolderPlus } from 'lucide-react';

export interface ProjectInfo {
  name: string;
  description: string;
  saveToDatabase: boolean;
}

interface ProjectDialogProps {
  isOpen: boolean;
  projectInfo: ProjectInfo;
  onProjectInfoChange: (info: ProjectInfo) => void;
  onCancel: () => void;
  onConfirm: () => void;
  isProcessing: boolean;
}

const ProjectDialog: React.FC<ProjectDialogProps> = ({
  isOpen,
  projectInfo,
  onProjectInfoChange,
  onCancel,
  onConfirm,
  isProcessing
}) => {
  if (!isOpen) return null;

  const handleInputChange = (field: keyof ProjectInfo, value: string | boolean) => {
    onProjectInfoChange({
      ...projectInfo,
      [field]: value
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <FolderPlus className="h-5 w-5 mr-2" />
            Project Information
          </h2>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Name *
              </label>
              <input
                type="text"
                value={projectInfo.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter project name"
                disabled={isProcessing}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={projectInfo.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Enter project description"
                disabled={isProcessing}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="saveToDatabase"
                checked={projectInfo.saveToDatabase}
                onChange={(e) => handleInputChange('saveToDatabase', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={isProcessing}
              />
              <label htmlFor="saveToDatabase" className="ml-2 block text-sm text-gray-700">
                Save project to database
              </label>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            disabled={isProcessing}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!projectInfo.name.trim() || isProcessing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? 'Processing...' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProjectDialog;
