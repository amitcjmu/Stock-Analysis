import type React from 'react';
import { useState } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { Download, FileText, FileSpreadsheet, Package, AlertCircle, Loader2 } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import PlanNavigation from '@/components/plan/PlanNavigation';
import { useToast } from '@/hooks/use-toast';
import { planningFlowApi } from '@/lib/api/planningFlowService';

const Export = (): JSX.Element => {
  const [searchParams] = useSearchParams();
  const routeParams = useParams<{ flowId?: string }>();
  const { toast } = useToast();
  const [downloading, setDownloading] = useState<string | null>(null);

  // Bug #961 Fix: Support both query param and path param for flow ID
  // Query: /plan/export?planning_flow_id=xxx
  // Path: /plan/export/:flowId
  const planning_flow_id = searchParams.get('planning_flow_id') || routeParams.flowId || null;

  /**
   * Handle export in different formats
   * @param format - Export format (json, pdf, excel)
   */
  const handleExport = async (format: 'json' | 'pdf' | 'excel') => {
    if (!planning_flow_id) {
      toast({
        title: 'Error',
        description: 'No planning flow selected. Please navigate from the planning page.',
        variant: 'destructive',
      });
      return;
    }

    setDownloading(format);
    try {
      // Call the export API
      const response = await planningFlowApi.exportPlanningData(planning_flow_id, format);

      // Create a blob and download file
      const timestamp = new Date().toISOString().split('T')[0];
      let filename = '';
      let blob: Blob;

      if (format === 'json') {
        // For JSON, stringify the response
        blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
        filename = `migration-plan-${timestamp}.json`;
      } else if (format === 'pdf') {
        // PDF will be binary data
        blob = new Blob([response], { type: 'application/pdf' });
        filename = `migration-plan-${timestamp}.pdf`;
      } else if (format === 'excel') {
        // Excel will be binary data
        blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        filename = `migration-plan-${timestamp}.xlsx`;
      } else {
        throw new Error('Unsupported format');
      }

      // Trigger download with delayed cleanup for browser compatibility
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      // Delay cleanup to ensure download initiates across all browsers
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 150);

      toast({
        title: 'Success',
        description: `Planning data exported successfully as ${format.toUpperCase()}`,
      });
    } catch (error: any) {
      console.error('Export failed:', error);

      // Handle 501 Not Implemented for PDF/Excel
      if (error?.response?.status === 501) {
        toast({
          title: 'Feature Not Available',
          description: error?.response?.data?.detail || `${format.toUpperCase()} export is not yet implemented. Please use JSON format.`,
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'Export Failed',
          description: error?.message || 'Failed to export planning data. Please try again.',
          variant: 'destructive',
        });
      }
    } finally {
      setDownloading(null);
    }
  };

  // Show error if no planning flow ID
  if (!planning_flow_id) {
    return (
      <SidebarProvider>
        <div className="min-h-screen bg-gray-50 flex">
          <Sidebar />
          <div className="flex-1 ml-64">
            <main className="p-8">
              <ContextBreadcrumbs showContextSelector={true} />
              <PlanNavigation />

              <div className="max-w-7xl mx-auto">
                <Card className="p-8">
                  <div className="flex flex-col items-center justify-center text-center space-y-4">
                    <div className="bg-yellow-100 p-4 rounded-full">
                      <AlertCircle className="h-12 w-12 text-yellow-600" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900">No Planning Flow Selected</h2>
                    <p className="text-gray-600 max-w-lg">
                      Please navigate to this page from the planning flow to export data.
                    </p>
                  </div>
                </Card>
              </div>
            </main>
          </div>
        </div>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">
            {/* Context Breadcrumbs */}
            <ContextBreadcrumbs showContextSelector={true} />

            {/* Plan Navigation Tabs */}
            <PlanNavigation />

            <div className="max-w-7xl mx-auto">
              <div className="mb-8">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Export Plan Data</h1>
                    <p className="text-lg text-gray-600">
                      Export migration plans, timelines, and resource allocations
                    </p>
                  </div>
                </div>
              </div>

              {/* Export Options */}
              <Card className="p-8">
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <div className="bg-blue-100 p-4 rounded-full">
                    <Download className="h-12 w-12 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900">Export Planning Data</h2>
                  <p className="text-gray-600 max-w-lg">
                    Choose your preferred format to export migration plans, timelines, and resource allocations.
                  </p>
                </div>
              </Card>

              {/* Export Options */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Options</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card className="p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="bg-green-100 p-2 rounded-lg">
                        <FileSpreadsheet className="h-6 w-6 text-green-600" />
                      </div>
                      <h4 className="font-semibold text-gray-900">Excel Report</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Complete migration plan with all waves, applications, and resource assignments
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => handleExport('excel')}
                      disabled={downloading !== null}
                      className="w-full"
                    >
                      {downloading === 'excel' ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <Download className="h-4 w-4 mr-2" />
                          Export to Excel
                        </>
                      )}
                    </Button>
                  </Card>

                  <Card className="p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="bg-blue-100 p-2 rounded-lg">
                        <FileText className="h-6 w-6 text-blue-600" />
                      </div>
                      <h4 className="font-semibold text-gray-900">PDF Summary</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Executive summary with key metrics, timelines, and risk analysis
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => handleExport('pdf')}
                      disabled={downloading !== null}
                      className="w-full"
                    >
                      {downloading === 'pdf' ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <Download className="h-4 w-4 mr-2" />
                          Export to PDF
                        </>
                      )}
                    </Button>
                  </Card>

                  <Card className="p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="bg-purple-100 p-2 rounded-lg">
                        <Package className="h-6 w-6 text-purple-600" />
                      </div>
                      <h4 className="font-semibold text-gray-900">JSON Package</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Complete data export in JSON format for integration with other tools
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => handleExport('json')}
                      disabled={downloading !== null}
                      className="w-full"
                    >
                      {downloading === 'json' ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <Download className="h-4 w-4 mr-2" />
                          Export to JSON
                        </>
                      )}
                    </Button>
                  </Card>
                </div>
              </div>

              {/* Information Note */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-blue-800 text-sm">
                      <strong>Note:</strong> JSON export is currently available. PDF and Excel exports will be available in a future release (issue #714). Export functionality will include customizable templates, scheduled exports, and API integration options.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Export;
