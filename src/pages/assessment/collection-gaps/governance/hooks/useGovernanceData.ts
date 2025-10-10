/**
 * useGovernanceData Hook
 * Manages data fetching for governance requirements, exceptions, and approval requests
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import type {
  GovernanceRequirement,
  MigrationException,
  ApprovalRequest
} from '../types';

/**
 * Fetch governance requirements
 */
export function useGovernanceRequirements(): UseQueryResult<GovernanceRequirement[], Error> {
  return useQuery({
    queryKey: ['governance-requirements'],
    queryFn: async (): Promise<GovernanceRequirement[]> => {
      // TODO: Replace with actual API call: apiCall('/api/v1/collection/governance/requirements')
      await new Promise(resolve => setTimeout(resolve, 1000));

      return [
        {
          id: '1',
          title: 'Data Encryption in Transit',
          description: 'All data must be encrypted during transmission using TLS 1.2 or higher',
          category: 'security',
          priority: 'critical',
          status: 'active',
          applicable_scopes: ['tenant', 'application'],
          approval_workflow: ['security_team', 'compliance_officer'],
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: '2',
          title: 'PCI DSS Compliance',
          description: 'Systems handling payment data must maintain PCI DSS compliance',
          category: 'compliance',
          priority: 'critical',
          status: 'active',
          applicable_scopes: ['application', 'asset'],
          approval_workflow: ['compliance_officer', 'ciso'],
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: '3',
          title: 'Change Management Process',
          description: 'All production changes must follow the established change management process',
          category: 'policy',
          priority: 'high',
          status: 'active',
          applicable_scopes: ['tenant', 'application', 'asset'],
          approval_workflow: ['change_manager', 'technical_lead'],
          created_at: '2024-01-01T00:00:00Z'
        }
      ];
    },
    refetchInterval: 60000,
    staleTime: 30000
  });
}

/**
 * Fetch migration exceptions
 */
export function useMigrationExceptions(): UseQueryResult<MigrationException[], Error> {
  return useQuery({
    queryKey: ['migration-exceptions'],
    queryFn: async (): Promise<MigrationException[]> => {
      // TODO: Replace with actual API call: apiCall('/api/v1/collection/governance/exceptions')
      await new Promise(resolve => setTimeout(resolve, 1000));

      return [
        {
          id: '1',
          requirement_id: '1',
          title: 'Legacy API Encryption Exception',
          justification: 'Legacy API cannot support TLS 1.2 due to hardware limitations',
          business_impact: 'Critical for maintaining legacy customer integrations',
          mitigation_plan: 'Implement application-level encryption and plan hardware upgrade',
          scope: 'application',
          scope_id: 'app-legacy-api',
          requested_by: 'John Doe',
          status: 'pending',
          priority: 'high',
          approval_history: [],
          created_at: '2024-02-01T00:00:00Z'
        },
        {
          id: '2',
          requirement_id: '2',
          title: 'PCI Scope Reduction',
          justification: 'Application will be removed from PCI scope through network segmentation',
          business_impact: 'Reduces compliance overhead while maintaining security',
          mitigation_plan: 'Complete network segmentation and implement data flow controls',
          scope: 'application',
          scope_id: 'app-reporting',
          requested_by: 'Jane Smith',
          status: 'approved',
          priority: 'medium',
          approval_history: [
            {
              approver: 'compliance_officer',
              action: 'approved',
              timestamp: '2024-02-05T10:30:00Z',
              comments: 'Approved with network segmentation validation requirement'
            }
          ],
          created_at: '2024-02-01T00:00:00Z',
          updated_at: '2024-02-05T10:30:00Z'
        }
      ];
    },
    refetchInterval: 60000,
    staleTime: 30000
  });
}

/**
 * Fetch approval requests
 */
export function useApprovalRequests(): UseQueryResult<ApprovalRequest[], Error> {
  return useQuery({
    queryKey: ['approval-requests'],
    queryFn: async (): Promise<ApprovalRequest[]> => {
      // TODO: Replace with actual API call: apiCall('/api/v1/collection/governance/approval-requests')
      await new Promise(resolve => setTimeout(resolve, 1000));

      return [
        {
          id: '1',
          title: 'Emergency Deployment Process Deviation',
          description: 'Request to bypass standard deployment process for critical security patch',
          request_type: 'process_deviation',
          scope: 'application',
          scope_id: 'app-payment-service',
          business_justification: 'Critical security vulnerability requires immediate patching',
          risk_assessment: 'Low risk with proper testing and monitoring',
          mitigation_measures: 'Deploy during low-traffic hours with full rollback plan',
          requested_by: 'Security Team',
          status: 'pending',
          priority: 'critical',
          created_at: '2024-02-10T00:00:00Z'
        }
      ];
    },
    refetchInterval: 60000,
    staleTime: 30000
  });
}
