/**
 * Governance & Exceptions Page
 * Main orchestrator component for governance requirements, exceptions, and approval requests
 *
 * Location: src/pages/assessment/collection-gaps/governance/index.tsx
 * Modularized from: src/pages/assessment/collection-gaps/governance.tsx (1056 lines)
 *
 * Architecture:
 * - Orchestrates child components (header, tables, dialogs)
 * - Manages data fetching via custom hooks
 * - Delegates form state to specialized hooks
 * - Preserves all original functionality
 */

import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Info } from 'lucide-react';

// Layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// Page-specific components
import { GovernanceHeader } from './components/GovernanceHeader';
import { RequirementsTable } from './components/RequirementsTable';
import { ExceptionsTable } from './components/ExceptionsTable';
import { ApprovalRequestsTable } from './components/ApprovalRequestsTable';
import { ExceptionDialog } from './components/ExceptionDialog';
import { ApprovalDialog } from './components/ApprovalDialog';

// Custom hooks
import {
  useGovernanceRequirements,
  useMigrationExceptions,
  useApprovalRequests
} from './hooks/useGovernanceData';
import { useExceptionForm } from './hooks/useExceptionForm';
import { useApprovalForm } from './hooks/useApprovalForm';

const GovernancePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const flowId = searchParams.get('flowId') || '';

  // Data fetching hooks
  const { data: requirements, isLoading: requirementsLoading } = useGovernanceRequirements();
  const { data: exceptions, isLoading: exceptionsLoading } = useMigrationExceptions();
  const { data: approvalRequests, isLoading: approvalsLoading } = useApprovalRequests();

  // Exception form management
  const exceptionForm = useExceptionForm();

  // Approval form management
  const approvalForm = useApprovalForm();

  // Exception view/edit handlers
  const handleViewException = (exception: import('./types').MigrationException) => {
    // TODO: Implement view exception details modal/page
    console.log('View exception:', exception);
  };

  const handleEditException = (exception: import('./types').MigrationException) => {
    // Pre-fill the exception form with existing data for editing
    exceptionForm.setFormData({
      requirement_id: exception.requirement_id || '',
      justification: exception.justification,
      business_impact: exception.business_impact,
      mitigation_plan: exception.mitigation_plan,
      scope: exception.scope,
      scope_id: exception.scope_id,
      priority: exception.priority,
    });
    exceptionForm.setIsDialogOpen(true);
  };

  // No flow ID - show error state
  if (!flowId) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Flow ID is required to manage governance and exceptions. Please navigate from an active collection flow.
              </AlertDescription>
            </Alert>
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

          <div className="space-y-6">
            {/* Header with navigation and actions */}
            <GovernanceHeader
              flowId={flowId}
              onRequestApproval={() => approvalForm.setIsDialogOpen(true)}
            />

            {/* Main content tabs */}
            <Tabs defaultValue="requirements" className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="requirements">Requirements</TabsTrigger>
                <TabsTrigger value="exceptions">Exceptions</TabsTrigger>
                <TabsTrigger value="approvals">Approval Requests</TabsTrigger>
              </TabsList>

              {/* Requirements tab */}
              <TabsContent value="requirements" className="space-y-6">
                <RequirementsTable
                  requirements={requirements}
                  isLoading={requirementsLoading}
                  onRequestException={exceptionForm.handleRequestException}
                />
              </TabsContent>

              {/* Exceptions tab */}
              <TabsContent value="exceptions" className="space-y-6">
                <ExceptionsTable
                  exceptions={exceptions}
                  isLoading={exceptionsLoading}
                  onViewException={handleViewException}
                  onEditException={handleEditException}
                />
              </TabsContent>

              {/* Approval requests tab */}
              <TabsContent value="approvals" className="space-y-6">
                <ApprovalRequestsTable
                  approvalRequests={approvalRequests}
                  isLoading={approvalsLoading}
                />
              </TabsContent>
            </Tabs>
          </div>

          {/* Exception request dialog */}
          <ExceptionDialog
            isOpen={exceptionForm.isDialogOpen}
            onOpenChange={exceptionForm.setIsDialogOpen}
            formData={exceptionForm.formData}
            onFormDataChange={exceptionForm.setFormData}
            selectedRequirement={exceptionForm.selectedRequirement}
            isSubmitting={exceptionForm.isSubmitting}
            onSubmit={exceptionForm.handleSubmit}
          />

          {/* Approval request dialog */}
          <ApprovalDialog
            isOpen={approvalForm.isDialogOpen}
            onOpenChange={approvalForm.setIsDialogOpen}
            formData={approvalForm.formData}
            onFormDataChange={approvalForm.setFormData}
            isSubmitting={approvalForm.isSubmitting}
            onSubmit={approvalForm.handleSubmit}
          />
        </div>
      </div>
    </div>
  );
};

export default GovernancePage;
