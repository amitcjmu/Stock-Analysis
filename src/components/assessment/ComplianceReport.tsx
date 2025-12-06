/**
 * ComplianceReport - Technology Compliance Validation Display
 *
 * ADR-039: Architecture Standards Compliance and EOL Lifecycle Integration
 *
 * Features:
 * - Summary cards (Compliant, Non-Compliant, EOL Expired, EOL Soon)
 * - Per-application compliance issues with severity badges
 * - EOL risk timeline visualization
 * - Expandable detailed view per application
 *
 * Backend Integration:
 * - Fetches from: GET /api/v1/master-flows/{flow_id}/compliance
 * - Uses snake_case for ALL field names (ADR compliance)
 * - Follows TanStack Query patterns with 30s refetch interval
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronRight,
  Shield,
  AlertOctagon,
  Calendar,
  Server,
  Info,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/apiClient';

// ============================================================================
// Types (using snake_case per ADR)
// ============================================================================

export interface ComplianceIssue {
  field: string;
  current: string;
  required: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
}

export interface ApplicationComplianceResult {
  application_id: string;
  application_name?: string;
  is_compliant: boolean;
  issues: ComplianceIssue[];
  checked_fields: number;
  passed_fields: number;
}

export interface EOLStatusInfo {
  product: string;
  version: string;
  status: 'active' | 'eol_soon' | 'eol_expired' | 'unknown';
  eol_date?: string;
  support_type: 'mainstream' | 'extended' | 'none';
  source: string;
  confidence: number;
}

export interface ComplianceValidationResponse {
  flow_id: string;
  standards_applied: Record<string, unknown>;
  summary: {
    total_applications: number;
    compliant_count: number;
    non_compliant_count: number;
  };
  applications: Record<string, ApplicationComplianceResult>;
  eol_status: EOLStatusInfo[];
  validated_at?: string;
}

// ============================================================================
// Component Props
// ============================================================================

export interface ComplianceReportProps {
  flow_id: string;
  /** Compact mode for embedding in other components */
  compact?: boolean;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface SummaryCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  description?: string;
  onClick?: () => void;
  isExpanded?: boolean;
  hasItems?: boolean;
}

const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  icon,
  color,
  description,
  onClick,
  isExpanded,
  hasItems,
}) => (
  <Card
    className={cn(
      hasItems && 'cursor-pointer hover:shadow-md transition-shadow',
      isExpanded && 'ring-2 ring-primary'
    )}
    onClick={hasItems ? onClick : undefined}
  >
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className={cn('p-3 rounded-full bg-opacity-10', color.replace('text-', 'bg-'))}>
          <div className={color}>{icon}</div>
        </div>
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
        </div>
        {hasItems && (
          <div className="text-muted-foreground">
            {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const variants: Record<string, string> = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-500 text-black',
    low: 'bg-blue-500 text-white',
  };

  return (
    <Badge className={cn('text-xs', variants[severity] || variants.medium)}>
      {severity.toUpperCase()}
    </Badge>
  );
};

const EOLStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const configs: Record<string, { color: string; label: string }> = {
    eol_expired: { color: 'bg-red-600 text-white', label: 'EOL Expired' },
    eol_soon: { color: 'bg-orange-500 text-white', label: 'EOL Soon' },
    active: { color: 'bg-green-600 text-white', label: 'Active' },
    unknown: { color: 'bg-gray-500 text-white', label: 'Unknown' },
  };

  const config = configs[status] || configs.unknown;

  return <Badge className={cn('text-xs', config.color)}>{config.label}</Badge>;
};

// ============================================================================
// Main Component
// ============================================================================

export const ComplianceReport: React.FC<ComplianceReportProps> = ({
  flow_id,
  compact = false,
}) => {
  const [expandedApps, setExpandedApps] = useState<Set<string>>(new Set());
  const [showEOLDetails, setShowEOLDetails] = useState(false);
  const [expandedTile, setExpandedTile] = useState<string | null>(null);

  // ============================================================================
  // Data Fetching
  // ============================================================================

  const {
    data: complianceData,
    isLoading,
    isError,
    error,
  } = useQuery<ComplianceValidationResponse>({
    queryKey: ['compliance-validation', flow_id],
    queryFn: async () => {
      return await apiClient.get<ComplianceValidationResponse>(
        `/master-flows/${flow_id}/compliance`
      );
    },
    enabled: !!flow_id,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refresh every minute
  });

  // ============================================================================
  // Computed Values
  // ============================================================================

  const eolCounts = useMemo(() => {
    if (!complianceData?.eol_status) {
      return { expired: 0, soon: 0, active: 0 };
    }
    return complianceData.eol_status.reduce(
      (acc, eol) => {
        if (eol.status === 'eol_expired') acc.expired++;
        else if (eol.status === 'eol_soon') acc.soon++;
        else if (eol.status === 'active') acc.active++;
        return acc;
      },
      { expired: 0, soon: 0, active: 0 }
    );
  }, [complianceData]);

  const nonCompliantApps = useMemo(() => {
    if (!complianceData?.applications) return [];
    return Object.entries(complianceData.applications)
      .filter(([_, app]) => !app.is_compliant)
      .map(([id, app]) => ({ id, ...app }));
  }, [complianceData]);

  const compliantApps = useMemo(() => {
    if (!complianceData?.applications) return [];
    return Object.entries(complianceData.applications)
      .filter(([_, app]) => app.is_compliant)
      .map(([id, app]) => ({ id, ...app }));
  }, [complianceData]);

  const eolExpiredItems = useMemo(() => {
    if (!complianceData?.eol_status) return [];
    return complianceData.eol_status.filter(eol => eol.status === 'eol_expired');
  }, [complianceData]);

  const eolSoonItems = useMemo(() => {
    if (!complianceData?.eol_status) return [];
    return complianceData.eol_status.filter(eol => eol.status === 'eol_soon');
  }, [complianceData]);

  const toggleTile = (tileId: string) => {
    setExpandedTile(prev => prev === tileId ? null : tileId);
  };

  const toggleApp = (appId: string) => {
    setExpandedApps((prev) => {
      const next = new Set(prev);
      if (next.has(appId)) {
        next.delete(appId);
      } else {
        next.add(appId);
      }
      return next;
    });
  };

  // ============================================================================
  // Render States
  // ============================================================================

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Technology Compliance
          </CardTitle>
          <CardDescription>Loading compliance validation...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Technology Compliance
          </CardTitle>
          <CardDescription className="text-destructive">
            Failed to load compliance data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>{error instanceof Error ? error.message : 'An error occurred'}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!complianceData || !complianceData.summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Technology Compliance
          </CardTitle>
          <CardDescription>No compliance data available</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          <Info className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">
            Compliance validation will be available after the Architecture Standards phase completes.
          </p>
        </CardContent>
      </Card>
    );
  }

  const { summary } = complianceData;
  const allCompliant = summary.non_compliant_count === 0;

  // ============================================================================
  // Compact Render (for embedding)
  // ============================================================================

  if (compact) {
    return (
      <Card className={cn(allCompliant ? 'border-green-200' : 'border-orange-200')}>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {allCompliant ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-orange-500" />
              )}
              <div>
                <p className="font-medium">
                  {allCompliant ? 'All Technologies Compliant' : `${summary.non_compliant_count} Non-Compliant`}
                </p>
                <p className="text-sm text-muted-foreground">
                  {summary.total_applications} applications checked
                </p>
              </div>
            </div>
            {eolCounts.expired > 0 && (
              <Badge variant="destructive">
                {eolCounts.expired} EOL
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // ============================================================================
  // Full Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Summary Cards - Clickable tiles with expand functionality */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Compliant Apps"
          value={summary.compliant_count}
          icon={<CheckCircle className="h-5 w-5" />}
          color="text-green-600"
          description={`${Math.round((summary.compliant_count / summary.total_applications) * 100)}% of total`}
          onClick={() => toggleTile('compliant')}
          isExpanded={expandedTile === 'compliant'}
          hasItems={compliantApps.length > 0}
        />
        <SummaryCard
          title="Non-Compliant"
          value={summary.non_compliant_count}
          icon={<AlertTriangle className="h-5 w-5" />}
          color="text-orange-500"
          description={summary.non_compliant_count > 0 ? 'Requires attention' : 'All clear'}
          onClick={() => toggleTile('non-compliant')}
          isExpanded={expandedTile === 'non-compliant'}
          hasItems={nonCompliantApps.length > 0}
        />
        <SummaryCard
          title="EOL Expired"
          value={eolCounts.expired}
          icon={<AlertOctagon className="h-5 w-5" />}
          color="text-red-600"
          description={eolCounts.expired > 0 ? 'High risk' : 'No expired technologies'}
          onClick={() => toggleTile('eol-expired')}
          isExpanded={expandedTile === 'eol-expired'}
          hasItems={eolExpiredItems.length > 0}
        />
        <SummaryCard
          title="EOL Soon"
          value={eolCounts.soon}
          icon={<Clock className="h-5 w-5" />}
          color="text-yellow-600"
          description={eolCounts.soon > 0 ? 'Plan upgrades' : 'No upcoming EOL'}
          onClick={() => toggleTile('eol-soon')}
          isExpanded={expandedTile === 'eol-soon'}
          hasItems={eolSoonItems.length > 0}
        />
      </div>

      {/* Expanded Tile Content - Shows artifact list when tile is clicked */}
      {expandedTile === 'compliant' && compliantApps.length > 0 && (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Compliant Applications ({compliantApps.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {compliantApps.map((app) => (
                <div
                  key={app.id}
                  className="p-3 bg-white rounded-lg border border-green-200 flex items-center gap-3"
                >
                  <Server className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="font-medium text-sm">{app.application_name || app.application_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {app.passed_fields}/{app.checked_fields} checks passed
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {expandedTile === 'non-compliant' && nonCompliantApps.length > 0 && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Non-Compliant Applications ({nonCompliantApps.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {nonCompliantApps.map((app) => (
                <div
                  key={app.id}
                  className="p-3 bg-white rounded-lg border border-orange-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-orange-500" />
                      <span className="font-medium">{app.application_name || app.application_id}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {app.issues.length} issue{app.issues.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    {app.issues.slice(0, 3).map((issue, idx) => (
                      <div key={idx} className="text-xs text-muted-foreground flex items-center gap-2">
                        <SeverityBadge severity={issue.severity} />
                        <span>{issue.field}: {issue.current} → {issue.required}</span>
                      </div>
                    ))}
                    {app.issues.length > 3 && (
                      <p className="text-xs text-muted-foreground">
                        +{app.issues.length - 3} more issues
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {expandedTile === 'eol-expired' && eolExpiredItems.length > 0 && (
        <Card className="border-red-200 bg-red-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertOctagon className="h-5 w-5 text-red-600" />
              EOL Expired Technologies ({eolExpiredItems.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {eolExpiredItems.map((eol, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-white rounded-lg border border-red-200 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <Server className="h-4 w-4 text-red-600" />
                    <div>
                      <p className="font-medium text-sm">{eol.product} {eol.version}</p>
                      {eol.eol_date && (
                        <p className="text-xs text-muted-foreground">
                          EOL: {new Date(eol.eol_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <EOLStatusBadge status={eol.status} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {expandedTile === 'eol-soon' && eolSoonItems.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              EOL Approaching Technologies ({eolSoonItems.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {eolSoonItems.map((eol, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-white rounded-lg border border-yellow-200 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <Server className="h-4 w-4 text-yellow-600" />
                    <div>
                      <p className="font-medium text-sm">{eol.product} {eol.version}</p>
                      {eol.eol_date && (
                        <p className="text-xs text-muted-foreground">
                          EOL: {new Date(eol.eol_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <EOLStatusBadge status={eol.status} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Compliant Celebration */}
      {allCompliant && eolCounts.expired === 0 && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-950">
          <CardContent className="flex items-center justify-center gap-4 py-8">
            <Shield className="h-12 w-12 text-green-600" />
            <div>
              <h3 className="text-xl font-semibold text-green-900 dark:text-green-100">
                Fully Compliant!
              </h3>
              <p className="text-green-700 dark:text-green-300">
                All applications meet technology version requirements
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Non-Compliant Applications */}
      {nonCompliantApps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Non-Compliant Applications
            </CardTitle>
            <CardDescription>
              {nonCompliantApps.length} applications have version compliance issues
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {nonCompliantApps.map((app) => (
              <Collapsible
                key={app.id}
                open={expandedApps.has(app.id)}
                onOpenChange={() => toggleApp(app.id)}
              >
                <Card className="border-orange-200">
                  <CollapsibleTrigger className="w-full">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Server className="h-5 w-5 text-muted-foreground" />
                          <div className="text-left">
                            <p className="font-medium">
                              {app.application_name || app.application_id}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {app.issues.length} issue{app.issues.length !== 1 ? 's' : ''} found
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {app.passed_fields}/{app.checked_fields} passed
                          </Badge>
                          {expandedApps.has(app.id) ? (
                            <ChevronDown className="h-5 w-5" />
                          ) : (
                            <ChevronRight className="h-5 w-5" />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <CardContent className="pt-0">
                      <div className="space-y-3 mt-2">
                        {app.issues.map((issue, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-muted/50 rounded-lg border"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium">{issue.field}</span>
                                  <SeverityBadge severity={issue.severity} />
                                </div>
                                <p className="text-sm text-muted-foreground">
                                  Current: <span className="font-mono text-red-600">{issue.current}</span>
                                  {' → '}
                                  Required: <span className="font-mono text-green-600">{issue.required}</span>
                                </p>
                                {issue.recommendation && (
                                  <p className="text-sm mt-2 text-muted-foreground">
                                    {issue.recommendation}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            ))}
          </CardContent>
        </Card>
      )}

      {/* EOL Status Overview */}
      {complianceData.eol_status && complianceData.eol_status.length > 0 && (
        <Card>
          <Collapsible open={showEOLDetails} onOpenChange={setShowEOLDetails}>
            <CardHeader>
              <CollapsibleTrigger className="w-full">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-muted-foreground" />
                    <CardTitle>End-of-Life Status</CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">
                      {complianceData.eol_status.length} technologies
                    </Badge>
                    {showEOLDetails ? (
                      <ChevronDown className="h-5 w-5" />
                    ) : (
                      <ChevronRight className="h-5 w-5" />
                    )}
                  </div>
                </div>
              </CollapsibleTrigger>
              <CardDescription>
                Technology lifecycle status from endoflife.date and vendor catalogs
              </CardDescription>
            </CardHeader>
            <CollapsibleContent>
              <CardContent>
                <div className="space-y-3">
                  {complianceData.eol_status.map((eol, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'p-3 rounded-lg border flex items-center justify-between',
                        eol.status === 'eol_expired' && 'bg-red-50 border-red-200',
                        eol.status === 'eol_soon' && 'bg-yellow-50 border-yellow-200',
                        eol.status === 'active' && 'bg-green-50 border-green-200'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <Server className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">
                            {eol.product} {eol.version}
                          </p>
                          {eol.eol_date && (
                            <p className="text-sm text-muted-foreground">
                              EOL: {new Date(eol.eol_date).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {eol.support_type}
                        </Badge>
                        <EOLStatusBadge status={eol.status} />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      )}

      {/* Validation Timestamp */}
      {complianceData.validated_at && (
        <p className="text-xs text-muted-foreground text-center">
          Last validated: {new Date(complianceData.validated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default ComplianceReport;
