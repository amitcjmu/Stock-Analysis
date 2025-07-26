/**
 * Shared Admin Toast Hook
 * Provides consistent toast messaging across admin components
 */

import { useToast } from '@/components/ui/use-toast';

export const useAdminToasts = (): {
  showSuccessToast: (title: string, description?: string) => void;
  showErrorToast: (title: string, description?: string) => void;
  showWarningToast: (title: string, description?: string) => void;
  showUserApprovedToast: (userName: string) => void;
  showUserRejectedToast: (userName: string) => void;
  showUserDeactivatedToast: (userName: string) => void;
  showUserActivatedToast: (userName: string) => void;
  showPurgeApprovedToast: (message?: string) => void;
  showPurgeRejectedToast: (message?: string) => void;
  showDataFetchErrorToast: () => void;
  showGenericErrorToast: (operation: string) => void;
  showDemoDataWarningToast: (errorMessage?: string) => void;
} => {
  const { toast } = useToast();

  const showSuccessToast = (title: string, description?: string): any => {
    toast({
      title,
      description,
      variant: "default"
    });
  };

  const showErrorToast = (title: string, description?: string): any => {
    toast({
      title,
      description,
      variant: "destructive"
    });
  };

  const showWarningToast = (title: string, description?: string): any => {
    toast({
      title,
      description,
      className: "border-orange-200 bg-orange-50"
    });
  };

  // Specific admin operation toasts
  const showUserApprovedToast = (userName: string): any => {
    showSuccessToast(
      "User Approved",
      `${userName} has been approved and granted access`
    );
  };

  const showUserRejectedToast = (userName: string): any => {
    showSuccessToast(
      "User Rejected",
      `${userName}'s request has been rejected`
    );
  };

  const showUserDeactivatedToast = (userName: string): any => {
    showSuccessToast(
      "User Deactivated",
      `${userName} has been deactivated`
    );
  };

  const showUserActivatedToast = (userName: string): any => {
    showSuccessToast(
      "User Activated",
      `${userName} has been activated`
    );
  };

  const showPurgeApprovedToast = (message?: string): any => {
    showSuccessToast(
      "Purge Approved",
      message || "Purge request has been approved"
    );
  };

  const showPurgeRejectedToast = (message?: string): any => {
    showSuccessToast(
      "Purge Rejected",
      message || "Purge request has been rejected"
    );
  };

  const showDataFetchErrorToast = (): any => {
    showErrorToast(
      "Error",
      "Failed to fetch data. Please try again."
    );
  };

  const showGenericErrorToast = (operation: string): any => {
    showErrorToast(
      "Error",
      `Failed to ${operation}. Please try again.`
    );
  };

  const showDemoDataWarningToast = (errorMessage?: string): any => {
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
