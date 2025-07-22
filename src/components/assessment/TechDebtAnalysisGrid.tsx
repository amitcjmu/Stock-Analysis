import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TechDebtItem } from '@/hooks/useAssessmentFlow';
import { Plus, Edit3, Trash2, AlertTriangle, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TechDebtAnalysisGridProps {
  techDebtItems: TechDebtItem[];
  onTechDebtChange: (items: TechDebtItem[]) => void;
  editingItem: string | null;
  onEditItem: (category: string | null) => void;
}

const DEBT_CATEGORIES = [
  'Code Quality',
  'Security Vulnerabilities',
  'Performance Issues',
  'Deprecated Dependencies',
  'Architecture Violations',
  'Testing Gaps',
  'Documentation Debt',
  'Infrastructure Debt',
  'Configuration Management',
  'Monitoring & Observability'
];

const SEVERITY_LEVELS = [
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-700 border-red-200', icon: AlertTriangle },
  { value: 'high', label: 'High', color: 'bg-orange-100 text-orange-700 border-orange-200', icon: AlertTriangle },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: Clock },
  { value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-700 border-blue-200', icon: Zap }
];

export const TechDebtAnalysisGrid: React.FC<TechDebtAnalysisGridProps> = ({
  techDebtItems,
  onTechDebtChange,
  editingItem,
  onEditItem
}) => {
  const [newItem, setNewItem] = useState<Partial<TechDebtItem>>({
    category: '',
    severity: 'medium',
    description: '',
    remediation_effort_hours: 0,
    impact_on_migration: '',
    tech_debt_score: 0
  });

  const addTechDebtItem = () => {
    if (!newItem.category || !newItem.description) return;

    const item: TechDebtItem = {
      category: newItem.category,
      severity: newItem.severity as unknown,
      description: newItem.description,
      remediation_effort_hours: newItem.remediation_effort_hours || 0,
      impact_on_migration: newItem.impact_on_migration || '',
      tech_debt_score: newItem.tech_debt_score || 0
    };

    onTechDebtChange([...techDebtItems, item]);
    setNewItem({
      category: '',
      severity: 'medium',
      description: '',
      remediation_effort_hours: 0,
      impact_on_migration: '',
      tech_debt_score: 0
    });
  };

  const updateTechDebtItem = (oldCategory: string, updatedItem: TechDebtItem) => {
    const updatedItems = techDebtItems.map(item =>
      item.category === oldCategory ? updatedItem : item
    );
    onTechDebtChange(updatedItems);
  };

  const removeTechDebtItem = (category: string) => {
    onTechDebtChange(techDebtItems.filter(item => item.category !== category));
  };

  const getSeverityInfo = (severity: string) => {
    return SEVERITY_LEVELS.find(sl => sl.value === severity) || SEVERITY_LEVELS[2];
  };

  const getTechDebtScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      {/* Add New Tech Debt Item */}
      <Card>
        <CardHeader>
          <CardTitle>Add Technical Debt Item</CardTitle>
          <CardDescription>
            Identify a new technical debt issue that affects migration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={newItem.category}
                onValueChange={(value) => setNewItem({ ...newItem, category: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {DEBT_CATEGORIES.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <Select
                value={newItem.severity}
                onValueChange={(value) => setNewItem({ ...newItem, severity: value as unknown })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITY_LEVELS.map((level) => {
                    const Icon = level.icon;
                    return (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4" />
                          <span>{level.label}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe the technical debt issue..."
              value={newItem.description}
              onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="effort">Remediation Effort (Hours)</Label>
              <Input
                id="effort"
                type="number"
                placeholder="0"
                value={newItem.remediation_effort_hours}
                onChange={(e) => setNewItem({ ...newItem, remediation_effort_hours: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="score">Tech Debt Score (0-100)</Label>
              <Input
                id="score"
                type="number"
                placeholder="0"
                min="0"
                max="100"
                value={newItem.tech_debt_score}
                onChange={(e) => setNewItem({ ...newItem, tech_debt_score: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="migration-impact">Impact on Migration</Label>
            <Textarea
              id="migration-impact"
              placeholder="How does this technical debt affect the migration process?"
              value={newItem.impact_on_migration}
              onChange={(e) => setNewItem({ ...newItem, impact_on_migration: e.target.value })}
              rows={2}
            />
          </div>

          <Button 
            onClick={addTechDebtItem}
            disabled={!newItem.category || !newItem.description}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Tech Debt Item
          </Button>
        </CardContent>
      </Card>

      {/* Tech Debt Items Grid */}
      {techDebtItems.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Technical Debt Identified</h3>
            <p className="text-gray-600">
              Add technical debt items that may impact the migration process.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {techDebtItems.map((item) => (
            <TechDebtCard
              key={item.category}
              item={item}
              isEditing={editingItem === item.category}
              onEdit={() => onEditItem(item.category)}
              onSave={(updated) => {
                updateTechDebtItem(item.category, updated);
                onEditItem(null);
              }}
              onCancel={() => onEditItem(null)}
              onRemove={() => removeTechDebtItem(item.category)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface TechDebtCardProps {
  item: TechDebtItem;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (item: TechDebtItem) => void;
  onCancel: () => void;
  onRemove: () => void;
}

const TechDebtCard: React.FC<TechDebtCardProps> = ({
  item,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onRemove
}) => {
  const [editData, setEditData] = useState<TechDebtItem>(item);

  const getSeverityInfo = (severity: string) => {
    return SEVERITY_LEVELS.find(sl => sl.value === severity) || SEVERITY_LEVELS[2];
  };

  const getTechDebtScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  const severityInfo = getSeverityInfo(item.severity);
  const SeverityIcon = severityInfo.icon;

  if (isEditing) {
    return (
      <Card className="border-blue-200">
        <CardContent className="pt-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Category</Label>
              <Select
                value={editData.category}
                onValueChange={(value) => setEditData({ ...editData, category: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEBT_CATEGORIES.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Severity</Label>
              <Select
                value={editData.severity}
                onValueChange={(value) => setEditData({ ...editData, severity: value as unknown })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITY_LEVELS.map((level) => {
                    const Icon = level.icon;
                    return (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4" />
                          <span>{level.label}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Description</Label>
            <Textarea
              value={editData.description}
              onChange={(e) => setEditData({ ...editData, description: e.target.value })}
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Effort (Hours)</Label>
              <Input
                type="number"
                value={editData.remediation_effort_hours}
                onChange={(e) => setEditData({ ...editData, remediation_effort_hours: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label>Score (0-100)</Label>
              <Input
                type="number"
                min="0"
                max="100"
                value={editData.tech_debt_score}
                onChange={(e) => setEditData({ ...editData, tech_debt_score: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" size="sm" onClick={onCancel}>
              Cancel
            </Button>
            <Button size="sm" onClick={() => onSave(editData)}>
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
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">{item.category}</h3>
              <div className="flex items-center space-x-2">
                <Badge className={severityInfo.color}>
                  <SeverityIcon className="h-3 w-3 mr-1" />
                  {severityInfo.label}
                </Badge>
              </div>
            </div>

            <p className="text-sm text-gray-700">{item.description}</p>

            {item.impact_on_migration && (
              <div className="p-2 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-xs font-medium text-orange-700 mb-1">Migration Impact:</p>
                <p className="text-xs text-orange-600">{item.impact_on_migration}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Effort:</p>
                <p className="font-medium">{item.remediation_effort_hours || 0} hours</p>
              </div>
              <div>
                <p className="text-gray-600">Debt Score:</p>
                <div className="flex items-center space-x-2">
                  <span className={cn("font-medium", getTechDebtScoreColor(item.tech_debt_score || 0))}>
                    {item.tech_debt_score || 0}/100
                  </span>
                  <Progress 
                    value={item.tech_debt_score || 0} 
                    className="h-2 flex-1"
                  />
                </div>
              </div>
            </div>
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