import React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ApplicationComponent, TechDebtItem } from '@/hooks/useAssessmentFlow';
import { Save, X, Edit3 } from 'lucide-react';

interface UserModificationFormProps {
  type: 'component' | 'tech-debt';
  item: ApplicationComponent | TechDebtItem | undefined;
  onSave: (item: ApplicationComponent | TechDebtItem) => void;
  onCancel: () => void;
}

export const UserModificationForm: React.FC<UserModificationFormProps> = ({
  type,
  item,
  onSave,
  onCancel
}) => {
  const [editData, setEditData] = useState<ApplicationComponent | TechDebtItem>(item || {} as ApplicationComponent | TechDebtItem);

  const handleSave = (): void => {
    onSave(editData);
  };

  if (type === 'component') {
    const component = editData as Partial<ApplicationComponent>;

    return (
      <Card className="border-blue-200 bg-blue-50/30">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Edit3 className="h-5 w-5" />
            <span>Edit Component</span>
          </CardTitle>
          <CardDescription>
            Modify the component details identified by AI analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="component-name">Component Name</Label>
              <Input
                id="component-name"
                value={component.component_name || ''}
                onChange={(e) => setEditData({ ...editData, component_name: e.target.value })}
                placeholder="e.g., User Service API"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="component-type">Component Type</Label>
              <Select
                value={component.component_type || ''}
                onValueChange={(value) => setEditData({ ...editData, component_type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="web_frontend">Web Frontend</SelectItem>
                  <SelectItem value="api_service">API Service</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                  <SelectItem value="message_queue">Message Queue</SelectItem>
                  <SelectItem value="batch_job">Batch Job</SelectItem>
                  <SelectItem value="microservice">Microservice</SelectItem>
                  <SelectItem value="monolith">Monolithic Application</SelectItem>
                  <SelectItem value="integration">Integration Layer</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="dependencies">Dependencies (comma-separated)</Label>
            <Input
              id="dependencies"
              value={component.dependencies?.join(', ') || ''}
              onChange={(e) => setEditData({
                ...editData,
                dependencies: e.target.value.split(',').map(d => d.trim()).filter(Boolean)
              })}
              placeholder="e.g., Database, External API, Message Queue"
            />
          </div>

          <div className="space-y-2">
            <Label>Technology Stack</Label>
            <div className="text-sm text-gray-600">
              Current: {component.technology_stack ?
                Object.entries(component.technology_stack).map(([key, value]) => `${key}: ${value}`).join(', ') :
                'None specified'
              }
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t border-gray-200">
            <Button variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-1" />
              Save Changes
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Tech Debt Item Form
  const techDebt = editData as Partial<TechDebtItem>;

  return (
    <Card className="border-orange-200 bg-orange-50/30">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Edit3 className="h-5 w-5" />
          <span>Edit Technical Debt Item</span>
        </CardTitle>
        <CardDescription>
          Modify the technical debt analysis identified by AI
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={techDebt.category || ''}
              onValueChange={(value) => setEditData({ ...editData, category: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Code Quality">Code Quality</SelectItem>
                <SelectItem value="Security Vulnerabilities">Security Vulnerabilities</SelectItem>
                <SelectItem value="Performance Issues">Performance Issues</SelectItem>
                <SelectItem value="Deprecated Dependencies">Deprecated Dependencies</SelectItem>
                <SelectItem value="Architecture Violations">Architecture Violations</SelectItem>
                <SelectItem value="Testing Gaps">Testing Gaps</SelectItem>
                <SelectItem value="Documentation Debt">Documentation Debt</SelectItem>
                <SelectItem value="Infrastructure Debt">Infrastructure Debt</SelectItem>
                <SelectItem value="Configuration Management">Configuration Management</SelectItem>
                <SelectItem value="Monitoring & Observability">Monitoring & Observability</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="severity">Severity</Label>
            <Select
              value={techDebt.severity || ''}
              onValueChange={(value) => setEditData({ ...editData, severity: value as 'critical' | 'high' | 'medium' | 'low' })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={techDebt.description || ''}
            onChange={(e) => setEditData({ ...editData, description: e.target.value })}
            placeholder="Describe the technical debt issue..."
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="effort">Remediation Effort (Hours)</Label>
            <Input
              id="effort"
              type="number"
              value={techDebt.remediation_effort_hours || ''}
              onChange={(e) => setEditData({ ...editData, remediation_effort_hours: parseInt(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="score">Tech Debt Score (0-100)</Label>
            <Input
              id="score"
              type="number"
              min="0"
              max="100"
              value={techDebt.tech_debt_score || ''}
              onChange={(e) => setEditData({ ...editData, tech_debt_score: parseInt(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="migration-impact">Impact on Migration</Label>
          <Textarea
            id="migration-impact"
            value={techDebt.impact_on_migration || ''}
            onChange={(e) => setEditData({ ...editData, impact_on_migration: e.target.value })}
            placeholder="How does this technical debt affect the migration process?"
            rows={2}
          />
        </div>

        <div className="flex justify-end space-x-2 pt-4 border-t border-gray-200">
          <Button variant="outline" onClick={onCancel}>
            <X className="h-4 w-4 mr-1" />
            Cancel
          </Button>
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-1" />
            Save Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
