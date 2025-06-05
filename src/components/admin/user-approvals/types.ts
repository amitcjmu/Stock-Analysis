/**
 * Types for User Approvals Component Module
 */

export interface PendingUser {
  user_id: string;
  email: string;
  full_name: string;
  username: string;
  organization: string;
  role_description: string;
  registration_reason: string;
  requested_access_level: string;
  phone_number?: string;
  manager_email?: string;
  linkedin_profile?: string;
  registration_requested_at: string;
  status: string;
}

export interface ActiveUser {
  user_id: string;
  email: string;
  full_name: string;
  username: string;
  organization: string;
  role_description: string;
  access_level: string;
  role_name: string;
  is_active: boolean;
  approved_at: string;
  last_login?: string;
}

export interface ApprovalData {
  access_level: string;
  role_name: string;
  client_access: string[];
  notes?: string;
}

export interface RejectionData {
  rejection_reason: string;
}

export interface UserApprovalsProps {
  // Main component props if needed
}

export interface UserListProps {
  pendingUsers: PendingUser[];
  activeUsers: ActiveUser[];
  activeTab: 'pending' | 'active';
  actionLoading: string | null;
  onUserSelect: (user: PendingUser) => void;
  onApprove: (user: PendingUser) => void;
  onReject: (user: PendingUser) => void;
  onViewDetails: (user: PendingUser) => void;
  onDeactivateUser: (user: ActiveUser) => void;
  onActivateUser: (user: ActiveUser) => void;
}

export interface UserStatsProps {
  pendingUsers: PendingUser[];
  activeUsers: ActiveUser[];
}

export interface ApprovalActionsProps {
  user: PendingUser;
  actionLoading: string | null;
  onApprove: () => void;
  onReject: () => void;
  onViewDetails: () => void;
}

export interface UserDetailsModalProps {
  user: PendingUser | null;
  isOpen: boolean;
  onClose: () => void;
  formatDate: (dateString: string) => string;
  getAccessLevelColor: (level: string) => string;
}

export interface UserFiltersProps {
  // Future filtering props
  onFilterChange?: (filters: any) => void;
} 