import React from 'react';
import { Upload } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { UploadCategory } from '../CMDBImport.types';

interface CMDBUploadSectionProps {
  categories: UploadCategory[];
  selectedCategory: string | null;
  setSelectedCategory: (categoryId: string) => void;
  isDragging: boolean;
  onFileUpload: (files: File[], categoryId: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, categoryId: string) => void;
  disabled?: boolean;
}

export const CMDBUploadSection: React.FC<CMDBUploadSectionProps> = ({
  categories,
  selectedCategory,
  setSelectedCategory,
  isDragging,
  onFileUpload,
  onDragOver,
  onDragLeave,
  onDrop,
  disabled = false
}) => {
  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Choose Data Category</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {categories.map((category) => (
          <Card 
            key={category.id}
            className={`relative cursor-pointer transition-all hover:shadow-md border-2 ${
              selectedCategory === category.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            } ${isDragging ? 'border-dashed border-blue-400 bg-blue-50' : ''}`}
            onClick={() => setSelectedCategory(category.id)}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={(e) => onDrop(e, category.id)}
          >
            <CardHeader>
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${category.color} text-white`}>
                  <category.icon className="h-6 w-6" />
                </div>
                <div>
                  <CardTitle className="text-lg">{category.title}</CardTitle>
                  <div className="flex items-center space-x-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {category.securityLevel} security
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {category.agents.length} validation agents
                    </Badge>
                  </div>
                </div>
              </div>
              <CardDescription className="mt-2">
                {category.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Accepted formats:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {category.acceptedTypes.map(type => (
                      <Badge key={type} variant="secondary" className="text-xs">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Examples:</p>
                  <p className="text-sm text-gray-600">{category.examples.join(', ')}</p>
                </div>
              </div>
              
              {/* File Input */}
              <div className="mt-4">
                <input
                  type="file"
                  id={`file-${category.id}`}
                  accept={category.acceptedTypes.join(',')}
                  onChange={(e) => {
                    console.log('🔍 File Input Change Event:', {
                      categoryId: category.id,
                      files: e.target.files,
                      fileCount: e.target.files?.length || 0
                    });
                    const files = Array.from(e.target.files || []);
                    if (files.length > 0) {
                      console.log('🔍 Calling handleFileUpload with:', files[0].name);
                      onFileUpload(files, category.id);
                    } else {
                      console.log('🔍 No files selected');
                    }
                  }}
                  className="hidden"
                />
                <Button
                  onClick={() => {
                    console.log('🔍 Upload Button Clicked:', {
                      categoryId: category.id,
                      categoryTitle: category.title,
                      inputElement: document.getElementById(`file-${category.id}`)
                    });
                    document.getElementById(`file-${category.id}`)?.click();
                  }}
                  variant="outline"
                  className="w-full"
                  disabled={disabled}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload {category.title}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};