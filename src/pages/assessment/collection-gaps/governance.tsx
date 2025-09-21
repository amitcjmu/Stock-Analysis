/**
 * Governance & Exceptions UI
 *
 * Submit approval requests, create migration exceptions, and track approval status
 * Location: src/pages/assessment/collection-gaps/governance.tsx
 */

import React, { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Layout components
import Sidebar from '@/components/Sidebar';
import ContextBreadcrumbs from '@/components/context/ContextBreadcrumbs';

// UI components
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Icons
import {
  Shield,
  ArrowLeft,
  Plus,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  User,
  Calendar,
  MoreHorizontal,
  Edit,
  Eye,
  Trash2,
  Info
} from 'lucide-react';

// Services and hooks
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

// Types
interface GovernanceRequirement {
  id: string;
  title: string;
  description: string;
  category: 'security' | 'compliance' | 'risk' | 'policy';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'inactive' | 'draft';
  applicable_scopes: Array<'tenant' | 'application' | 'asset'>;
  approval_workflow: string[];
  created_at: string;
  updated_at?: string;
}

interface MigrationException {
  id: string;
  requirement_id: string;
  title: string;
  justification: string;
  business_impact: string;
  mitigation_plan: string;
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  requested_by: string;
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn';
  priority: 'low' | 'medium' | 'high' | 'critical';
  expiry_date?: string;
  approval_history: Array<{
    approver: string;
    action: 'approved' | 'rejected' | 'requested_changes';
    timestamp: string;
    comments?: string;
  }>;
  created_at: string;
  updated_at?: string;
}

interface ApprovalRequest {
  id: string;
  title: string;
  description: string;
  request_type: 'policy_exception' | 'process_deviation' | 'risk_acceptance' | 'compliance_waiver';
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  business_justification: string;
  risk_assessment: string;
  mitigation_measures: string;
  requested_by: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected';
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  updated_at?: string;
}

interface ExceptionFormData {
  requirement_id: string;
  title: string;
  justification: string;
  business_impact: string;
  mitigation_plan: string;
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  expiry_date?: string;
}

interface ApprovalFormData {
  title: string;
  description: string;
  request_type: 'policy_exception' | 'process_deviation' | 'risk_acceptance' | 'compliance_waiver';
  scope: 'tenant' | 'application' | 'asset';
  scope_id: string;
  business_justification: string;
  risk_assessment: string;
  mitigation_measures: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

const GovernancePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const flowId = searchParams.get('flowId') || '';

  // State
  const [isExceptionDialogOpen, setIsExceptionDialogOpen] = useState(false);
  const [isApprovalDialogOpen, setIsApprovalDialogOpen] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState<GovernanceRequirement | null>(null);
  const [exceptionFormData, setExceptionFormData] = useState<ExceptionFormData>({
    requirement_id: '',
    title: '',
    justification: '',
    business_impact: '',
    mitigation_plan: '',
    scope: 'application',
    scope_id: '',
    priority: 'medium'
  });
  const [approvalFormData, setApprovalFormData] = useState<ApprovalFormData>({
    title: '',
    description: '',
    request_type: 'policy_exception',
    scope: 'application',
    scope_id: '',
    business_justification: '',
    risk_assessment: '',
    mitigation_measures: '',
    priority: 'medium'
  });

  // Fetch governance requirements
  const { data: requirements, isLoading: requirementsLoading } = useQuery({
    queryKey: ['governance-requirements'],
    queryFn: async (): Promise<GovernanceRequirement[]> => {
      // This will be replaced with: apiCall('/api/v1/collection/governance/requirements')
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

  // Fetch migration exceptions
  const { data: exceptions, isLoading: exceptionsLoading } = useQuery({
    queryKey: ['migration-exceptions'],
    queryFn: async (): Promise<MigrationException[]> => {
      // This will be replaced with: apiCall('/api/v1/collection/governance/exceptions')
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

  // Fetch approval requests
  const { data: approvalRequests, isLoading: approvalsLoading } = useQuery({
    queryKey: ['approval-requests'],
    queryFn: async (): Promise<ApprovalRequest[]> => {
      // This will be replaced with: apiCall('/api/v1/collection/governance/approval-requests')
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

  // Create exception mutation
  const createExceptionMutation = useMutation({
    mutationFn: async (data: ExceptionFormData): Promise<MigrationException> => {
      // This will be replaced with: apiCall('/api/v1/collection/governance/exceptions', { method: 'POST', body: data })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        id: Date.now().toString(),
        ...data,
        requested_by: 'Current User',
        status: 'pending',
        approval_history: [],
        created_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['migration-exceptions'] });
      setIsExceptionDialogOpen(false);
      resetExceptionForm();
      toast({
        title: 'Exception Request Submitted',
        description: 'Your migration exception request has been submitted for approval.'
      });
    },
    onError: (error) => {
      console.error('Failed to create exception:', error);
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit exception request. Please try again.',
        variant: 'destructive'
      });
    }
  });

  // Create approval request mutation
  const createApprovalMutation = useMutation({
    mutationFn: async (data: ApprovalFormData): Promise<ApprovalRequest> => {
      // This will be replaced with: apiCall('/api/v1/collection/governance/approval-requests', { method: 'POST', body: data })
      await new Promise(resolve => setTimeout(resolve, 1000));
      return {
        id: Date.now().toString(),
        ...data,
        requested_by: 'Current User',
        status: 'pending',
        created_at: new Date().toISOString()
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-requests'] });
      setIsApprovalDialogOpen(false);
      resetApprovalForm();
      toast({
        title: 'Approval Request Submitted',
        description: 'Your approval request has been submitted for review.'
      });
    },
    onError: (error) => {
      console.error('Failed to create approval request:', error);
      toast({
        title: 'Submission Failed',
        description: 'Failed to submit approval request. Please try again.',
        variant: 'destructive'
      });
    }
  });

  const resetExceptionForm = () => {
    setExceptionFormData({
      requirement_id: '',
      title: '',
      justification: '',
      business_impact: '',
      mitigation_plan: '',
      scope: 'application',
      scope_id: '',
      priority: 'medium'
    });
  };

  const resetApprovalForm = () => {
    setApprovalFormData({
      title: '',
      description: '',
      request_type: 'policy_exception',
      scope: 'application',
      scope_id: '',
      business_justification: '',
      risk_assessment: '',
      mitigation_measures: '',
      priority: 'medium'
    });
  };

  const handleCreateException = () => {
    if (!exceptionFormData.requirement_id || !exceptionFormData.title || !exceptionFormData.justification) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields.',
        variant: 'destructive'
      });
      return;
    }

    createExceptionMutation.mutate(exceptionFormData);
  };

  const handleCreateApproval = () => {
    if (!approvalFormData.title || !approvalFormData.business_justification) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields.',
        variant: 'destructive'
      });
      return;
    }

    createApprovalMutation.mutate(approvalFormData);
  };

  const handleRequestException = (requirement: GovernanceRequirement) => {
    setSelectedRequirement(requirement);
    setExceptionFormData({
      ...exceptionFormData,
      requirement_id: requirement.id,
      title: `Exception for: ${requirement.title}`
    });
    setIsExceptionDialogOpen(true);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'approved': return 'default';
      case 'pending': case 'under_review': return 'secondary';
      case 'rejected': case 'withdrawn': return 'destructive';
      case 'active': return 'default';
      case 'inactive': return 'secondary';
      default: return 'outline';
    }
  };

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

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
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/assessment/collection-gaps?flowId=${flowId}`)}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to Dashboard
                </Button>
                <div>
                  <h1 className="text-3xl font-bold">Governance & Exceptions</h1>
                  <p className="text-muted-foreground">
                    Submit approval requests and manage migration exceptions
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Dialog open={isApprovalDialogOpen} onOpenChange={setIsApprovalDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Request Approval
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Submit Approval Request</DialogTitle>
                      <DialogDescription>
                        Request approval for policy deviations, risk acceptance, or compliance waivers
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="approval_title">Title *</Label>
                          <Input
                            id="approval_title"
                            value={approvalFormData.title}
                            onChange={(e) => setApprovalFormData({ ...approvalFormData, title: e.target.value })}
                            placeholder="Brief title for the request"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="request_type">Request Type</Label>
                          <Select value={approvalFormData.request_type} onValueChange={(value: string) => setApprovalFormData({ ...approvalFormData, request_type: value })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="policy_exception">Policy Exception</SelectItem>
                              <SelectItem value="process_deviation">Process Deviation</SelectItem>
                              <SelectItem value="risk_acceptance">Risk Acceptance</SelectItem>
                              <SelectItem value="compliance_waiver">Compliance Waiver</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="approval_description">Description</Label>
                        <Textarea
                          id="approval_description"
                          value={approvalFormData.description}
                          onChange={(e) => setApprovalFormData({ ...approvalFormData, description: e.target.value })}
                          placeholder="Detailed description of the request"
                          rows={3}
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="approval_scope">Scope</Label>
                          <Select value={approvalFormData.scope} onValueChange={(value: string) => setApprovalFormData({ ...approvalFormData, scope: value })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="tenant">Tenant-wide</SelectItem>
                              <SelectItem value="application">Application</SelectItem>
                              <SelectItem value="asset">Asset</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="approval_scope_id">Scope ID</Label>
                          <Input
                            id="approval_scope_id"
                            value={approvalFormData.scope_id}
                            onChange={(e) => setApprovalFormData({ ...approvalFormData, scope_id: e.target.value })}
                            placeholder="Specific ID"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="approval_priority">Priority</Label>
                          <Select value={approvalFormData.priority} onValueChange={(value: string) => setApprovalFormData({ ...approvalFormData, priority: value })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="low">Low</SelectItem>
                              <SelectItem value="medium">Medium</SelectItem>
                              <SelectItem value="high">High</SelectItem>
                              <SelectItem value="critical">Critical</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="business_justification">Business Justification *</Label>
                        <Textarea
                          id="business_justification"
                          value={approvalFormData.business_justification}
                          onChange={(e) => setApprovalFormData({ ...approvalFormData, business_justification: e.target.value })}
                          placeholder="Explain the business need for this request"
                          rows={3}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="risk_assessment">Risk Assessment</Label>
                        <Textarea
                          id="risk_assessment"
                          value={approvalFormData.risk_assessment}
                          onChange={(e) => setApprovalFormData({ ...approvalFormData, risk_assessment: e.target.value })}
                          placeholder="Assess the risks associated with this request"
                          rows={2}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="mitigation_measures">Mitigation Measures</Label>
                        <Textarea
                          id="mitigation_measures"
                          value={approvalFormData.mitigation_measures}
                          onChange={(e) => setApprovalFormData({ ...approvalFormData, mitigation_measures: e.target.value })}
                          placeholder="Describe how risks will be mitigated"
                          rows={2}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsApprovalDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button onClick={handleCreateApproval} disabled={createApprovalMutation.isPending}>
                        {createApprovalMutation.isPending ? 'Submitting...' : 'Submit Request'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>

            {/* Main Content */}
            <Tabs defaultValue="requirements" className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="requirements">Requirements</TabsTrigger>
                <TabsTrigger value="exceptions">Exceptions</TabsTrigger>
                <TabsTrigger value="approvals">Approval Requests</TabsTrigger>
              </TabsList>

              <TabsContent value="requirements" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Governance Requirements ({requirements?.length || 0})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {requirementsLoading ? (
                      <div className="p-6">
                        <div className="space-y-3">
                          {[...Array(3)].map((_, i) => (
                            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
                          ))}
                        </div>
                      </div>
                    ) : requirements && requirements.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Requirement</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>Priority</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Scope</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {requirements.map((requirement) => (
                            <TableRow key={requirement.id}>
                              <TableCell>
                                <div className="space-y-1">
                                  <div className="font-medium">{requirement.title}</div>
                                  <div className="text-sm text-muted-foreground">
                                    {requirement.description}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="capitalize">
                                  {requirement.category}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getPriorityBadgeVariant(requirement.priority)}>
                                  {requirement.priority}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getStatusBadgeVariant(requirement.status)}>
                                  {requirement.status}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1">
                                  {requirement.applicable_scopes.map((scope) => (
                                    <Badge key={scope} variant="outline" className="text-xs">
                                      {scope}
                                    </Badge>
                                  ))}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRequestException(requirement)}
                                  className="flex items-center gap-1"
                                >
                                  <FileText className="h-3 w-3" />
                                  Request Exception
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <div className="p-6 text-center">
                        <Shield className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No requirements found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          No governance requirements are currently defined.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="exceptions" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Migration Exceptions ({exceptions?.length || 0})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {exceptionsLoading ? (
                      <div className="p-6">
                        <div className="space-y-3">
                          {[...Array(3)].map((_, i) => (
                            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
                          ))}
                        </div>
                      </div>
                    ) : exceptions && exceptions.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Exception</TableHead>
                            <TableHead>Priority</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Scope</TableHead>
                            <TableHead>Requested By</TableHead>
                            <TableHead>Created</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {exceptions.map((exception) => (
                            <TableRow key={exception.id}>
                              <TableCell>
                                <div className="space-y-1">
                                  <div className="font-medium">{exception.title}</div>
                                  <div className="text-sm text-muted-foreground">
                                    {exception.justification.substring(0, 100)}
                                    {exception.justification.length > 100 && '...'}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getPriorityBadgeVariant(exception.priority)}>
                                  {exception.priority}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  <Badge variant={getStatusBadgeVariant(exception.status)}>
                                    {exception.status}
                                  </Badge>
                                  {exception.status === 'approved' && exception.approval_history.length > 0 && (
                                    <div className="text-xs text-green-600 flex items-center gap-1">
                                      <CheckCircle className="h-3 w-3" />
                                      {new Date(exception.approval_history[exception.approval_history.length - 1].timestamp).toLocaleDateString()}
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  <Badge variant="outline" className="capitalize">
                                    {exception.scope}
                                  </Badge>
                                  <div className="text-xs text-muted-foreground">
                                    {exception.scope_id}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm">
                                  <User className="h-3 w-3" />
                                  {exception.requested_by}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(exception.created_at).toLocaleDateString()}
                                </div>
                              </TableCell>
                              <TableCell>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                      <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end">
                                    <DropdownMenuItem>
                                      <Eye className="mr-2 h-4 w-4" />
                                      View Details
                                    </DropdownMenuItem>
                                    {exception.status === 'pending' && (
                                      <DropdownMenuItem>
                                        <Edit className="mr-2 h-4 w-4" />
                                        Edit
                                      </DropdownMenuItem>
                                    )}
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <div className="p-6 text-center">
                        <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No exceptions found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          No migration exceptions have been submitted yet.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="approvals" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Approval Requests ({approvalRequests?.length || 0})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {approvalsLoading ? (
                      <div className="p-6">
                        <div className="space-y-3">
                          {[...Array(3)].map((_, i) => (
                            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
                          ))}
                        </div>
                      </div>
                    ) : approvalRequests && approvalRequests.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Request</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Priority</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Scope</TableHead>
                            <TableHead>Requested By</TableHead>
                            <TableHead>Created</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {approvalRequests.map((request) => (
                            <TableRow key={request.id}>
                              <TableCell>
                                <div className="space-y-1">
                                  <div className="font-medium">{request.title}</div>
                                  <div className="text-sm text-muted-foreground">
                                    {request.description.substring(0, 100)}
                                    {request.description.length > 100 && '...'}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="capitalize">
                                  {request.request_type.replace('_', ' ')}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getPriorityBadgeVariant(request.priority)}>
                                  {request.priority}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getStatusBadgeVariant(request.status)}>
                                  {request.status.replace('_', ' ')}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  <Badge variant="outline" className="capitalize">
                                    {request.scope}
                                  </Badge>
                                  <div className="text-xs text-muted-foreground">
                                    {request.scope_id}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm">
                                  <User className="h-3 w-3" />
                                  {request.requested_by}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm">
                                  <Calendar className="h-3 w-3" />
                                  {new Date(request.created_at).toLocaleDateString()}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <div className="p-6 text-center">
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No approval requests found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          No approval requests have been submitted yet.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Exception Request Dialog */}
          <Dialog open={isExceptionDialogOpen} onOpenChange={setIsExceptionDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Request Migration Exception</DialogTitle>
                <DialogDescription>
                  Submit an exception request for: {selectedRequirement?.title}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <div className="space-y-2">
                  <Label htmlFor="exception_title">Exception Title *</Label>
                  <Input
                    id="exception_title"
                    value={exceptionFormData.title}
                    onChange={(e) => setExceptionFormData({ ...exceptionFormData, title: e.target.value })}
                    placeholder="Brief title for this exception"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="justification">Justification *</Label>
                  <Textarea
                    id="justification"
                    value={exceptionFormData.justification}
                    onChange={(e) => setExceptionFormData({ ...exceptionFormData, justification: e.target.value })}
                    placeholder="Explain why this exception is needed"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="business_impact">Business Impact</Label>
                  <Textarea
                    id="business_impact"
                    value={exceptionFormData.business_impact}
                    onChange={(e) => setExceptionFormData({ ...exceptionFormData, business_impact: e.target.value })}
                    placeholder="Describe the business impact of not granting this exception"
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mitigation_plan">Mitigation Plan</Label>
                  <Textarea
                    id="mitigation_plan"
                    value={exceptionFormData.mitigation_plan}
                    onChange={(e) => setExceptionFormData({ ...exceptionFormData, mitigation_plan: e.target.value })}
                    placeholder="Describe how risks will be mitigated"
                    rows={2}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="exception_scope">Scope</Label>
                    <Select value={exceptionFormData.scope} onValueChange={(value: string) => setExceptionFormData({ ...exceptionFormData, scope: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tenant">Tenant-wide</SelectItem>
                        <SelectItem value="application">Application</SelectItem>
                        <SelectItem value="asset">Asset</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="exception_scope_id">Scope ID</Label>
                    <Input
                      id="exception_scope_id"
                      value={exceptionFormData.scope_id}
                      onChange={(e) => setExceptionFormData({ ...exceptionFormData, scope_id: e.target.value })}
                      placeholder="Specific ID"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="exception_priority">Priority</Label>
                    <Select value={exceptionFormData.priority} onValueChange={(value: string) => setExceptionFormData({ ...exceptionFormData, priority: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="expiry_date">Expiry Date (Optional)</Label>
                  <Input
                    id="expiry_date"
                    type="date"
                    value={exceptionFormData.expiry_date || ''}
                    onChange={(e) => setExceptionFormData({ ...exceptionFormData, expiry_date: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsExceptionDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateException} disabled={createExceptionMutation.isPending}>
                  {createExceptionMutation.isPending ? 'Submitting...' : 'Submit Exception'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
};

export default GovernancePage;
