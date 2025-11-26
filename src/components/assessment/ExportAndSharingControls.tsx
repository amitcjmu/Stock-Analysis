import React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Download, Share, FileText, FileSpreadsheet, Mail } from 'lucide-react';
import { assessmentFlowApi } from '@/lib/api/assessmentFlow';
import { useToast } from '@/components/ui/use-toast';

interface ExportAndSharingControlsProps {
  flowId: string;
  assessmentData?: Record<string, unknown>;
}

export const ExportAndSharingControls: React.FC<ExportAndSharingControlsProps> = ({
  flowId,
  assessmentData
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  /**
   * GAP-6 FIX: Wire export to actual backend endpoint.
   * Calls POST /assessment-flow/{flowId}/export?format={format}
   */
  const handleExport = async (format: 'json' | 'pdf' | 'excel'): Promise<void> => {
    if (!flowId) {
      toast({
        title: 'Export Error',
        description: 'No assessment flow ID available for export',
        variant: 'destructive',
      });
      return;
    }

    setIsExporting(true);
    try {
      // Call actual backend export API
      await assessmentFlowApi.downloadExport(flowId, format);

      toast({
        title: 'Export Successful',
        description: `Assessment exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = (method: string): void => {
    console.log(`Sharing assessment via ${method}`, assessmentData);
    alert(`Sharing functionality for ${method} would be implemented here`);
  };

  return (
    <div className="flex items-center space-x-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" disabled={isExporting}>
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => handleExport('pdf')}>
            <FileText className="h-4 w-4 mr-2" />
            Export as PDF
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleExport('excel')}>
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Export as Excel
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleExport('json')}>
            <FileText className="h-4 w-4 mr-2" />
            Export as JSON
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline">
            <Share className="h-4 w-4 mr-2" />
            Share
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => handleShare('email')}>
            <Mail className="h-4 w-4 mr-2" />
            Share via Email
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleShare('link')}>
            <Share className="h-4 w-4 mr-2" />
            Generate Share Link
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
