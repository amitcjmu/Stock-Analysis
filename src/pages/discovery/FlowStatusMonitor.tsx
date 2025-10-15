import type React from 'react';
import { useParams } from 'react-router-dom';
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';
import FlowStatusWidget from '@/components/discovery/FlowStatusWidget';
import { useAuth } from '@/contexts/AuthContext';

/**
 * FlowStatusMonitor Page
 *
 * Dedicated page for monitoring flow status for flows in:
 * - initialization
 * - running
 * - failed
 * - error
 * states
 *
 * This page wraps the FlowStatusWidget component and provides
 * a standalone view for monitoring flow progress.
 */
const FlowStatusMonitor: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>();
  const { client, engagement } = useAuth();

  // Validation for required context
  if (!client?.id || !engagement?.id) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center max-w-md">
                <div className="mb-4">
                  <div className="mx-auto h-12 w-12 rounded-full bg-yellow-100 flex items-center justify-center">
                    <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Missing Required Context</h2>
                <p className="text-gray-600">
                  Client and engagement context is required to monitor flow status.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Validation for flow ID
  if (!flowId) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center max-w-md">
                <div className="mb-4">
                  <div className="mx-auto h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                    <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Flow ID Required</h2>
                <p className="text-gray-600">
                  No flow ID was provided. Please navigate to this page from a flow overview.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Flow Status Monitor</h1>
                <p className="text-gray-600">
                  Real-time monitoring and AI-powered analysis of your discovery flow
                </p>
              </div>
            </div>
          </div>

          {/* Flow Status Widget */}
          <div className="max-w-4xl mx-auto">
            <FlowStatusWidget
              flowId={flowId}
              flowType="discovery"
              className="shadow-lg"
            />
          </div>

          {/* Additional Information */}
          <div className="mt-6 max-w-4xl mx-auto">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">About Flow Monitoring</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>
                      This page provides real-time monitoring of your discovery flow. The AI-powered
                      analysis helps you understand the current state, progress, and recommended
                      next steps for your flow.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowStatusMonitor;
