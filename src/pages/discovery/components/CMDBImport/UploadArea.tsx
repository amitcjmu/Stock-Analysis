import React from 'react';
import { FileSpreadsheet, Database, Monitor, Activity, FileText } from 'lucide-react'
import { Upload } from 'lucide-react'

interface UploadAreaProps {
  area: {
    id: string;
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    acceptedTypes: string[];
    examples: string[];
  };
  onDrop: (files: File[], type: string) => void;
  isSelected: boolean;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Database,
  Monitor,
  Activity,
  FileText,
  FileSpreadsheet,
};

export const UploadArea: React.FC<UploadAreaProps> = ({ area, onDrop, isSelected }) => {
  const Icon = iconMap[area.icon.name] || FileSpreadsheet;
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  const handleZoneClick = (): void => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files.length > 0) {
      onDrop(Array.from(e.target.files), area.id);
      e.target.value = ''; // Reset input
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onDrop(Array.from(e.dataTransfer.files), area.id);
    }
  };

  return (
    <div
      className={`relative border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer ${
        isSelected
          ? 'border-blue-500 bg-blue-50'
          : isDragging
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-blue-500'
      }`}
      onClick={handleZoneClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="text-center pointer-events-none">
        <div className={`${area.color} mx-auto h-12 w-12 rounded-lg flex items-center justify-center mb-4`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{area.title}</h3>
        <p className="text-sm text-gray-600 mb-4">{area.description}</p>

        <div className="text-xs text-gray-500 mb-2">
          <strong>Accepted formats:</strong> {area.acceptedTypes.join(', ')}
        </div>

        <div className="text-xs text-gray-500 mb-4">
          <strong>Examples:</strong> {area.examples.join(', ')}
        </div>

        <div className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">
          <Upload className="h-4 w-4 mr-2" />
          {isDragging ? 'Drop files here' : 'Click to upload files'}
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={area.acceptedTypes.join(',')}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};
