/**
 * Shared Admin Toast Hook
 * Provides consistent toast messaging across admin components
 */

import { useToast } from '@/components/ui/use-toast';

export const useAdminToasts = () => {
  const { toast } = useToast();

  const showSuccessToast = (title: string, description?: string) => {
    toast({
      title,
      description,
      variant: "default"
    });
  };

  const showErrorToast = (title: string, description?: string) => {
    toast({
      title,
      description,
      variant: "destructive"
    });
  };

  const showWarningToast = (title: string, description?: string) => {
    toast({
      title,
      description,
      className: "border-orange-200 bg-orange-50"
    });
  };

  // Specific admin operation toasts
  const showUserApprovedToast = (userName: string) => {
    showSuccessToast(
      "User Approved",
      `${userName} has been approved and granted access`
    );
  };

  const showUserRejectedToast = (userName: string) => {
    showSuccessToast(
      "User Rejected",
      `${userName}'s request has been rejected`
    );
  };

  const showUserDeactivatedToast = (userName: string) => {
    showSuccessToast(
      "User Deactivated",
      `${userName} has been deactivated`
    );
  };

  const showUserActivatedToast = (userName: string) => {
    showSuccessToast(
      "User Activated",
      `${userName} has been activated`
    );
  };

  const showPurgeApprovedToast = (message?: string) => {
    showSuccessToast(
      "Purge Approved",
      message || "Purge request has been approved"
    );
  };

  const showPurgeRejectedToast = (message?: string) => {
    showSuccessToast(
      "Purge Rejected",
      message || "Purge request has been rejected"
    );
  };

  const showDataFetchErrorToast = () => {
    showErrorToast(
      "Error",
      "Failed to fetch data. Please try again."
    );
  };

  const showGenericErrorToast = (operation: string) => {
    showErrorToast(
      "Error",
      `Failed to ${operation}. Please try again.`
    );
  };

  const showDemoDataWarningToast = (errorMessage?: string) => {
    showWarningToast(
      "Using Demo Data",
      `There was an issue fetching live data. Showing demo statistics. ${errorMessage ? `Error: ${errorMessage}` : ''}`
    );
  };

  return {
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showUserApprovedToast,
    showUserRejectedToast,
    showUserDeactivatedToast,
    showUserActivatedToast,
    showPurgeApprovedToast,
    showPurgeRejectedToast,
    showDataFetchErrorToast,
    showGenericErrorToast,
    showDemoDataWarningToast
  };
};
