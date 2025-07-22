import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Plus, Trash2, Edit3, Check, X, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ApplicationOverride {
  application_id: string;
  application_name: string;
  exception_type: string;
  rationale: string;
  alternative_approach?: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  approval_status: 'pending' | 'approved' | 'rejected';
  business_justification: string;
  technical_justification?: string;
  compensating_controls?: string[];
  review_date?: string;
  approved_by?: string;
}

interface ApplicationOverrideData {
  application_name: string;
  exception_type: string;
  rationale: string;
  alternative_approach?: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  approval_status: 'pending' | 'approved' | 'rejected';
  business_justification: string;
  technical_justification?: string;
  compensating_controls?: string[];
  review_date?: string;
  approved_by?: string;
}

interface ApplicationOverridesProps {
  applications: string[];
  overrides: Record<string, ApplicationOverrideData>;
  onChange: (overrides: Record<string, ApplicationOverrideData>) => void;
}

const EXCEPTION_TYPES = [
  { value: 'security', label: 'Security Exception', color: 'bg-red-100 text-red-700' },
  { value: 'performance', label: 'Performance Exception', color: 'bg-orange-100 text-orange-700' },
  { value: 'compliance', label: 'Compliance Exception', color: 'bg-purple-100 text-purple-700' },
  { value: 'technical', label: 'Technical Limitation', color: 'bg-blue-100 text-blue-700' },
  { value: 'legacy', label: 'Legacy System', color: 'bg-gray-100 text-gray-700' },
  { value: 'cost', label: 'Cost Constraint', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'timeline', label: 'Timeline Constraint', color: 'bg-green-100 text-green-700' }
];

const RISK_LEVELS = [
  { value: 'low', label: 'Low Risk', color: 'bg-green-100 text-green-700 border-green-200' },
  { value: 'medium', label: 'Medium Risk', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
  { value: 'high', label: 'High Risk', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { value: 'critical', label: 'Critical Risk', color: 'bg-red-100 text-red-700 border-red-200' }
];

const APPROVAL_STATUS = [
  { value: 'pending', label: 'Pending Review', color: 'bg-gray-100 text-gray-700' },
  { value: 'approved', label: 'Approved', color: 'bg-green-100 text-green-700' },
  { value: 'rejected', label: 'Rejected', color: 'bg-red-100 text-red-700' }
];

export const ApplicationOverrides: React.FC<ApplicationOverridesProps> = ({
  applications,
  overrides,
  onChange
}) => {
  const [editingApp, setEditingApp] = useState<string | null>(null);
  const [newOverride, setNewOverride] = useState<Partial<ApplicationOverride>>({
    application_id: '',
    application_name: '',
    exception_type: '',
    rationale: '',
    risk_level: 'low',
    approval_status: 'pending',
    business_justification: '',
    compensating_controls: []
  });

  const existingOverrides = Object.entries(overrides).map(([appId, data]) => ({
    application_id: appId,
    ...data
  })) as ApplicationOverride[];

  const applicationsWithoutOverrides = applications.filter(
    appId => !overrides[appId]
  );

  const addOverride = () => {
    if (!newOverride.application_id || !newOverride.exception_type || !newOverride.rationale) return;

    const updatedOverrides = {
      ...overrides,
      [newOverride.application_id]: {
        application_name: newOverride.application_name,
        exception_type: newOverride.exception_type,
        rationale: newOverride.rationale,
        alternative_approach: newOverride.alternative_approach,
        risk_level: newOverride.risk_level,
        approval_status: newOverride.approval_status,
        business_justification: newOverride.business_justification,
        technical_justification: newOverride.technical_justification,
        compensating_controls: newOverride.compensating_controls || [],
        review_date: new Date().toISOString().split('T')[0]
      }
    };

    onChange(updatedOverrides);
    setNewOverride({
      application_id: '',
      application_name: '',
      exception_type: '',
      rationale: '',
      risk_level: 'low',
      approval_status: 'pending',
      business_justification: '',
      compensating_controls: []
    });
  };

  const updateOverride = (appId: string, updates: Partial<ApplicationOverride>) => {
    const updatedOverrides = {
      ...overrides,
      [appId]: { ...overrides[appId], ...updates }
    };
    onChange(updatedOverrides);
  };

  const removeOverride = (appId: string) => {
    const { [appId]: removed, ...remaining } = overrides;
    onChange(remaining);
  };

  const getExceptionTypeColor = (type: string) => {
    const exceptionType = EXCEPTION_TYPES.find(et => et.value === type);
    return exceptionType?.color || 'bg-gray-100 text-gray-700';
  };

  const getRiskLevelColor = (level: string) => {
    const riskLevel = RISK_LEVELS.find(rl => rl.value === level);
    return riskLevel?.color || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getApprovalStatusColor = (status: string) => {
    const approvalStatus = APPROVAL_STATUS.find(as => as.value === status);
    return approvalStatus?.color || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="existing">
            Existing Overrides ({existingOverrides.length})
          </TabsTrigger>
          <TabsTrigger value="add-new">Add New Override</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Total Applications</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{applications.length}</div>
                <p className="text-sm text-gray-600">Applications in assessment</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Overrides Required</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">{existingOverrides.length}</div>
                <p className="text-sm text-gray-600">Applications with exceptions</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Standard Compliant</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {applications.length - existingOverrides.length}
                </div>
                <p className="text-sm text-gray-600">No exceptions needed</p>
              </CardContent>
            </Card>
          </div>

          {existingOverrides.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Risk Summary</CardTitle>
                <CardDescription>
                  Overview of risk levels across all application overrides
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {RISK_LEVELS.map(level => {
                    const count = existingOverrides.filter(override => override.risk_level === level.value).length;
                    return (
                      <div key={level.value} className={`p-3 rounded-lg border ${level.color}`}>
                        <div className="text-lg font-semibold">{count}</div>
                        <div className="text-sm">{level.label}</div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="existing" className="space-y-4">
          {existingOverrides.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Overrides Defined</h3>
                <p className="text-gray-600 mb-4">
                  All applications are expected to meet the standard architecture requirements.
                </p>
                <Button onClick={() => document.querySelector('[value="add-new"]')?.click()}>
                  Add First Override
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {existingOverrides.map((override) => (
                <OverrideCard
                  key={override.application_id}
                  override={override}
                  isEditing={editingApp === override.application_id}
                  onEdit={() => setEditingApp(override.application_id)}
                  onSave={(updates) => {
                    updateOverride(override.application_id, updates);
                    setEditingApp(null);
                  }}
                  onCancel={() => setEditingApp(null)}
                  onRemove={() => removeOverride(override.application_id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="add-new">
          <Card>
            <CardHeader>
              <CardTitle>Add Application Override</CardTitle>
              <CardDescription>
                Define an exception for an application that cannot meet the standard requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="application">Application</Label>
                  <Select
                    value={newOverride.application_id}
                    onValueChange={(value) => {
                      setNewOverride({
                        ...newOverride,
                        application_id: value,
                        application_name: value // In real implementation, get name from application data
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select application" />
                    </SelectTrigger>
                    <SelectContent>
                      {applicationsWithoutOverrides.map((appId) => (
                        <SelectItem key={appId} value={appId}>
                          {appId} {/* In real implementation, show application name */}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="exception-type">Exception Type</Label>
                  <Select
                    value={newOverride.exception_type}
                    onValueChange={(value) => setNewOverride({ ...newOverride, exception_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select exception type" />
                    </SelectTrigger>
                    <SelectContent>
                      {EXCEPTION_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rationale">Rationale</Label>
                <Textarea
                  id="rationale"
                  placeholder="Explain why this application cannot meet the standard requirements..."
                  value={newOverride.rationale}
                  onChange={(e) => setNewOverride({ ...newOverride, rationale: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="business-justification">Business Justification</Label>
                <Textarea
                  id="business-justification"
                  placeholder="Provide business justification for this exception..."
                  value={newOverride.business_justification}
                  onChange={(e) => setNewOverride({ ...newOverride, business_justification: e.target.value })}
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="risk-level">Risk Level</Label>
                  <Select
                    value={newOverride.risk_level}
                    onValueChange={(value) => setNewOverride({ ...newOverride, risk_level: value as ApplicationOverride['risk_level'] })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {RISK_LEVELS.map((level) => (
                        <SelectItem key={level.value} value={level.value}>
                          {level.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="approval-status">Approval Status</Label>
                  <Select
                    value={newOverride.approval_status}
                    onValueChange={(value) => setNewOverride({ ...newOverride, approval_status: value as ApplicationOverride['approval_status'] })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {APPROVAL_STATUS.map((status) => (
                        <SelectItem key={status.value} value={status.value}>
                          {status.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                onClick={addOverride}
                disabled={!newOverride.application_id || !newOverride.exception_type || !newOverride.rationale}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Override
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

interface OverrideCardProps {
  override: ApplicationOverride;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (updates: Partial<ApplicationOverride>) => void;
  onCancel: () => void;
  onRemove: () => void;
}

const OverrideCard: React.FC<OverrideCardProps> = ({
  override,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onRemove
}) => {
  const [editData, setEditData] = useState<Partial<ApplicationOverride>>(override);

  const getExceptionTypeColor = (type: string) => {
    const exceptionType = EXCEPTION_TYPES.find(et => et.value === type);
    return exceptionType?.color || 'bg-gray-100 text-gray-700';
  };

  const getRiskLevelColor = (level: string) => {
    const riskLevel = RISK_LEVELS.find(rl => rl.value === level);
    return riskLevel?.color || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getApprovalStatusColor = (status: string) => {
    const approvalStatus = APPROVAL_STATUS.find(as => as.value === status);
    return approvalStatus?.color || 'bg-gray-100 text-gray-700';
  };

  if (isEditing) {
    return (
      <Card className="border-blue-200">
        <CardContent className="pt-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Exception Type</Label>
              <Select
                value={editData.exception_type}
                onValueChange={(value) => setEditData({ ...editData, exception_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EXCEPTION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Risk Level</Label>
              <Select
                value={editData.risk_level}
                onValueChange={(value) => setEditData({ ...editData, risk_level: value as ApplicationOverride['risk_level'] })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RISK_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Rationale</Label>
            <Textarea
              value={editData.rationale}
              onChange={(e) => setEditData({ ...editData, rationale: e.target.value })}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label>Business Justification</Label>
            <Textarea
              value={editData.business_justification}
              onChange={(e) => setEditData({ ...editData, business_justification: e.target.value })}
              rows={2}
            />
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" size="sm" onClick={onCancel}>
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button size="sm" onClick={() => onSave(editData)}>
              <Check className="h-4 w-4 mr-1" />
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-gray-900">
                {override.application_name || override.application_id}
              </h3>
              <Badge className={getExceptionTypeColor(override.exception_type)}>
                {EXCEPTION_TYPES.find(et => et.value === override.exception_type)?.label || override.exception_type}
              </Badge>
            </div>

            <div className="flex items-center space-x-2">
              <Badge className={getRiskLevelColor(override.risk_level)}>
                {RISK_LEVELS.find(rl => rl.value === override.risk_level)?.label || override.risk_level}
              </Badge>
              <Badge className={getApprovalStatusColor(override.approval_status)}>
                {APPROVAL_STATUS.find(as => as.value === override.approval_status)?.label || override.approval_status}
              </Badge>
              {override.risk_level === 'critical' && (
                <AlertTriangle className="h-4 w-4 text-red-600" />
              )}
            </div>

            <p className="text-sm text-gray-700">{override.rationale}</p>

            <p className="text-sm text-gray-600">{override.business_justification}</p>

            {override.review_date && (
              <p className="text-xs text-gray-500">
                Review Date: {new Date(override.review_date).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="flex items-center space-x-1 ml-4">
            <Button variant="ghost" size="sm" onClick={onEdit}>
              <Edit3 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onRemove} className="text-red-600 hover:text-red-700">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};