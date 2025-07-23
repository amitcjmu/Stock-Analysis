/**
 * Enhanced RBAC Hook
 * Provides role-based access control functionality with hierarchical permissions
 */

import type { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import type { 
  EnhancedUserProfile, 
  UserAccessScope,
  RolePermissions 
} from '@/types/rbac';
import { 
  RoleLevel, 
  DataScope 
} from '@/types/rbac';

interface UseEnhancedRBACReturn {
  userProfile: EnhancedUserProfile | null;
  userAccessScope: UserAccessScope | null;
  rolePermissions: RolePermissions | null;
  loading: boolean;
  error: string | null;
  
  // Role checking functions
  isPlatformAdmin: boolean;
  isClientAdmin: boolean;
  isEngagementManager: boolean;
  isAnalyst: boolean;
  isViewer: boolean;
  isAnonymous: boolean;
  
  // Permission checking functions
  canManagePlatform: boolean;
  canManageAllClients: boolean;
  canManageUsers: boolean;
  canPurgeData: boolean;
  canDeleteData: boolean;
  canModifyData: boolean;
  canViewAnalytics: boolean;
  canConfigureAgents: boolean;
  
  // Access validation functions
  canAccessClient: (clientId: string) => boolean;
  canAccessEngagement: (engagementId: string, clientId?: string) => boolean;
  hasPermission: (permission: keyof RolePermissions) => boolean;
  
  // Data operations
  refreshUserProfile: () => Promise<void>;
  checkUserAccess: (userId: string) => Promise<UserAccessScope | null>;
}

export const useEnhancedRBAC = (): UseEnhancedRBACReturn => {
  const { user, getAuthHeaders } = useAuth();
  const [userProfile, setUserProfile] = useState<EnhancedUserProfile | null>(null);
  const [userAccessScope, setUserAccessScope] = useState<UserAccessScope | null>(null);
  const [rolePermissions, setRolePermissions] = useState<RolePermissions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch user profile and permissions
  const fetchUserProfile = useCallback(async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch enhanced user profile
      const profileResponse = await apiCall(`/api/v1/rbac/user-profile/${user.id}`, {
        headers: getAuthHeaders()
      });

      if (profileResponse.status === 'success') {
        setUserProfile(profileResponse.user_profile);

        // Fetch user access scope
        const scopeResponse = await apiCall(`/api/v1/rbac/user-access-scope/${user.id}`, {
          headers: getAuthHeaders()
        });

        if (scopeResponse.status === 'success') {
          setUserAccessScope(scopeResponse.access_scope);
        }

        // Fetch role permissions
        const permissionsResponse = await apiCall(`/api/v1/rbac/role-permissions/${profileResponse.user_profile.role_level}`, {
          headers: getAuthHeaders()
        });

        if (permissionsResponse.status === 'success') {
          setRolePermissions(permissionsResponse.permissions);
        }
      } else {
        throw new Error(profileResponse.message || 'Failed to fetch user profile');
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load user profile');
      
      // Set fallback values for demo users
      if (user?.id === 'admin_user' || user?.email === 'admin@aiforce.com') {
        setUserProfile({
          user_id: user.id,
          role_level: RoleLevel.PLATFORM_ADMIN,
          data_scope: DataScope.PLATFORM,
          status: 'active',
          approval_requested_at: new Date().toISOString(),
          approved_at: new Date().toISOString(),
          organization: 'AI Modernize Platform',
          role_description: 'Platform Administrator',
          login_count: 0,
          failed_login_attempts: 0,
          notification_preferences: {
            email_notifications: true,
            system_alerts: true,
            learning_updates: true,
            weekly_reports: true
          },
          is_deleted: false,
          created_at: new Date().toISOString()
        } as EnhancedUserProfile);

        setUserAccessScope({
          client_account_ids: [],
          engagement_ids: [],
          scope: 'platform',
          include_demo: true
        });
      }
    } finally {
      setLoading(false);
    }
  }, [user, getAuthHeaders]);

  // Refresh user profile
  const refreshUserProfile = useCallback(async () => {
    await fetchUserProfile();
  }, [fetchUserProfile]);

  // Check user access for another user (admin function)
  const checkUserAccess = useCallback(async (userId: string): Promise<UserAccessScope | null> => {
    try {
      const response = await apiCall(`/api/v1/rbac/user-access-scope/${userId}`, {
        headers: getAuthHeaders()
      });

      if (response.status === 'success') {
        return response.access_scope;
      }
      return null;
    } catch (err) {
      console.error('Error checking user access:', err);
      return null;
    }
  }, [getAuthHeaders]);

  // Access validation functions
  const canAccessClient = useCallback((clientId: string): boolean => {
    if (!userProfile || !userAccessScope) return false;
    
    // Platform admins can access all clients
    if (userProfile.role_level === RoleLevel.PLATFORM_ADMIN) return true;
    
    // Check if client is in accessible list (empty list means all for platform admin)
    return userAccessScope.client_account_ids.length === 0 || 
           userAccessScope.client_account_ids.includes(clientId);
  }, [userProfile, userAccessScope]);

  const canAccessEngagement = useCallback((engagementId: string, clientId?: string): boolean => {
    if (!userProfile || !userAccessScope) return false;
    
    // Platform admins can access all engagements
    if (userProfile.role_level === RoleLevel.PLATFORM_ADMIN) return true;
    
    // Check client access first if provided
    if (clientId && !canAccessClient(clientId)) return false;
    
    // Check engagement access
    return userAccessScope.engagement_ids.length === 0 || 
           userAccessScope.engagement_ids.includes(engagementId);
  }, [userProfile, userAccessScope, canAccessClient]);

  const hasPermission = useCallback((permission: keyof RolePermissions): boolean => {
    if (!rolePermissions) return false;
    return rolePermissions[permission] as boolean;
  }, [rolePermissions]);

  // Fetch profile on mount and when user changes
  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  // Computed role checks
  const isPlatformAdmin = userProfile?.role_level === RoleLevel.PLATFORM_ADMIN;
  const isClientAdmin = userProfile?.role_level === RoleLevel.CLIENT_ADMIN;
  const isEngagementManager = userProfile?.role_level === RoleLevel.ENGAGEMENT_MANAGER;
  const isAnalyst = userProfile?.role_level === RoleLevel.ANALYST;
  const isViewer = userProfile?.role_level === RoleLevel.VIEWER;
  const isAnonymous = userProfile?.role_level === RoleLevel.ANONYMOUS || !userProfile;

  // Computed permission checks
  const canManagePlatform = hasPermission('can_manage_platform_settings');
  const canManageAllClients = hasPermission('can_manage_all_clients');
  const canManageUsers = hasPermission('can_manage_all_users');
  const canPurgeData = hasPermission('can_purge_deleted_data');
  const canDeleteData = hasPermission('can_delete_client_data') || hasPermission('can_delete_engagement_data');
  const canModifyData = hasPermission('can_modify_data');
  const canViewAnalytics = hasPermission('can_view_analytics');
  const canConfigureAgents = hasPermission('can_configure_agents');

  return {
    userProfile,
    userAccessScope,
    rolePermissions,
    loading,
    error,
    
    // Role checks
    isPlatformAdmin,
    isClientAdmin,
    isEngagementManager,
    isAnalyst,
    isViewer,
    isAnonymous,
    
    // Permission checks
    canManagePlatform,
    canManageAllClients,
    canManageUsers,
    canPurgeData,
    canDeleteData,
    canModifyData,
    canViewAnalytics,
    canConfigureAgents,
    
    // Access validation
    canAccessClient,
    canAccessEngagement,
    hasPermission,
    
    // Data operations
    refreshUserProfile,
    checkUserAccess
  };
}; 