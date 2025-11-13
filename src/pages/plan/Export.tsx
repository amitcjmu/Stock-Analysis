import type React from 'react';
import { Download, FileText, FileSpreadsheet, Package, AlertCircle } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import PlanNavigation from '@/components/plan/PlanNavigation';

const Export = (): JSX.Element => {
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

              {/* Coming Soon Notice */}
              <Card className="p-8">
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <div className="bg-blue-100 p-4 rounded-full">
                    <Download className="h-12 w-12 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900">Export Features Coming Soon</h2>
                  <p className="text-gray-600 max-w-lg">
                    Export functionality for migration plans, timelines, and resource allocations will be available in the next release.
                  </p>
                </div>
              </Card>

              {/* Placeholder Export Options (Preview) */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Planned Export Options</h3>
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
                    <Button variant="outline" disabled className="w-full">
                      <Download className="h-4 w-4 mr-2" />
                      Export to Excel
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
                    <Button variant="outline" disabled className="w-full">
                      <Download className="h-4 w-4 mr-2" />
                      Export to PDF
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
                    <Button variant="outline" disabled className="w-full">
                      <Download className="h-4 w-4 mr-2" />
                      Export to JSON
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
                      <strong>Note:</strong> This feature is planned for issue #714. Export functionality will include customizable templates, scheduled exports, and API integration options.
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
