/**
 * AnalysisHistory - Simplified Component
 *
 * Note: Original complex modular AnalysisHistory directory was deleted in Phase 5.
 * This is a simplified functional version for backward compatibility.
 *
 * TODO: Enhance with Assessment Flow history data when backend API is ready
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { History, Download, Archive, Trash2, Eye, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import type { Analysis } from '@/types/assessment';

interface AnalysisHistoryProps {
  analyses: Analysis[];
  onSelect?: (id: string) => void;
  onCompare?: (ids: string[]) => void;
  onExport?: (id: string) => void;
  onDelete?: (id: string) => void;
  onArchive?: (id: string) => void;
  onViewDetails?: (id: string) => void;
  className?: string;
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({
  analyses,
  onViewDetails,
  onExport,
  onArchive,
  onDelete,
  className = ''
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const handleAction = (id: string, action: string) => {
    switch (action) {
      case 'view':
        onViewDetails?.(id);
        toast.success('Opening analysis details');
        break;
      case 'export':
        onExport?.(id);
        toast.success('Exporting analysis');
        break;
      case 'archive':
        onArchive?.(id);
        toast.success('Analysis archived');
        break;
      case 'delete':
        onDelete?.(id);
        toast.success('Analysis deleted');
        break;
    }
  };

  if (analyses.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Analysis History
          </CardTitle>
          <CardDescription>
            View and manage previous assessment analyses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-6 mb-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                  Assessment Flow Migration
                </h3>
                <p className="text-sm text-yellow-800 mb-3">
                  Analysis history is now managed through the Assessment Flow system.
                  Historical 6R Analysis data was archived during the migration.
                </p>
                <p className="text-sm text-yellow-800 font-medium">
                  Please use the Assessment Flow interface: <code className="bg-yellow-100 px-2 py-1 rounded">/assessment</code>
                </p>
              </div>
            </div>
          </div>

          <div className="text-center py-12">
            <History className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-700 mb-2">No Analysis History</h4>
            <p className="text-sm text-gray-500 mb-6">
              Start a new assessment to see your analysis history here
            </p>
            <a
              href="/assessment"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Assessment Flow
            </a>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="w-5 h-5" />
          Analysis History ({analyses.length})
        </CardTitle>
        <CardDescription>
          View and manage previous assessment analyses
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {analyses.map((analysis: any) => (
            <div
              key={analysis.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium">{analysis.name || `Analysis ${analysis.id}`}</h4>
                  {analysis.status && (
                    <Badge variant={analysis.status === 'completed' ? 'default' : 'secondary'}>
                      {analysis.status}
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-500">
                  {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : 'No date'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAction(analysis.id, 'view')}
                >
                  <Eye className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAction(analysis.id, 'export')}
                >
                  <Download className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAction(analysis.id, 'archive')}
                >
                  <Archive className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAction(analysis.id, 'delete')}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AnalysisHistory;
