import React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button';
import type { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ArchitectureStandard } from '@/hooks/useAssessmentFlow';
import { Plus, Trash2, Edit3, Check, X } from 'lucide-react';
import type { cn } from '@/lib/utils';

interface ArchitectureStandardsFormProps {
  standards: ArchitectureStandard[];
  onChange: (standards: ArchitectureStandard[]) => void;
}

const REQUIREMENT_TYPES = [
  { value: 'security', label: 'Security', color: 'bg-red-100 text-red-700' },
  { value: 'performance', label: 'Performance', color: 'bg-orange-100 text-orange-700' },
  { value: 'availability', label: 'Availability', color: 'bg-green-100 text-green-700' },
  { value: 'scalability', label: 'Scalability', color: 'bg-blue-100 text-blue-700' },
  { value: 'compliance', label: 'Compliance', color: 'bg-purple-100 text-purple-700' },
  { value: 'integration', label: 'Integration', color: 'bg-indigo-100 text-indigo-700' },
  { value: 'data', label: 'Data Management', color: 'bg-teal-100 text-teal-700' },
  { value: 'monitoring', label: 'Monitoring', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'backup', label: 'Backup & Recovery', color: 'bg-gray-100 text-gray-700' },
  { value: 'networking', label: 'Networking', color: 'bg-cyan-100 text-cyan-700' }
];

const VERIFICATION_STATUSES = [
  { value: 'pending', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'needs_revision', label: 'Needs Revision' },
  { value: 'rejected', label: 'Rejected' }
];

export const ArchitectureStandardsForm: React.FC<ArchitectureStandardsFormProps> = ({
  standards,
  onChange
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newStandard, setNewStandard] = useState<Partial<ArchitectureStandard>>({
    requirement_type: '',
    description: '',
    mandatory: true,
    supported_versions: {},
    requirement_details: {},
    verification_status: 'pending'
  });
  
  const getRequirementTypeColor = (type: string) => {
    const reqType = REQUIREMENT_TYPES.find(rt => rt.value === type);
    return reqType?.color || 'bg-gray-100 text-gray-700';
  };
  
  const addNewStandard = () => {
    if (!newStandard.requirement_type || !newStandard.description) return;
    
    const standard: ArchitectureStandard = {
      id: `standard_${Date.now()}`,
      requirement_type: newStandard.requirement_type,
      description: newStandard.description,
      mandatory: newStandard.mandatory || false,
      supported_versions: newStandard.supported_versions || {},
      requirement_details: newStandard.requirement_details || {},
      verification_status: newStandard.verification_status || 'pending'
    };
    
    onChange([...standards, standard]);
    setNewStandard({
      requirement_type: '',
      description: '',
      mandatory: true,
      supported_versions: {},
      requirement_details: {},
      verification_status: 'pending'
    });
  };
  
  const updateStandard = (id: string, updates: Partial<ArchitectureStandard>) => {
    const updatedStandards = standards.map(standard =>
      standard.id === id ? { ...standard, ...updates } : standard
    );
    onChange(updatedStandards);
  };
  
  const removeStandard = (id: string) => {
    onChange(standards.filter(standard => standard.id !== id));
  };
  
  const groupedStandards = standards.reduce((groups, standard) => {
    const type = standard.requirement_type;
    if (!groups[type]) groups[type] = [];
    groups[type].push(standard);
    return groups;
  }, {} as Record<string, ArchitectureStandard[]>);
  
  return (
    <div className="space-y-6">
      <Tabs defaultValue="by-category" className="space-y-4">
        <TabsList>
          <TabsTrigger value="by-category">By Category</TabsTrigger>
          <TabsTrigger value="all-standards">All Standards</TabsTrigger>
          <TabsTrigger value="add-new">Add New</TabsTrigger>
        </TabsList>
        
        <TabsContent value="by-category" className="space-y-4">
          {Object.entries(groupedStandards).map(([type, typeStandards]) => {
            const reqType = REQUIREMENT_TYPES.find(rt => rt.value === type);
            return (
              <Card key={type}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Badge className={getRequirementTypeColor(type)}>
                        {reqType?.label || type}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        {typeStandards.length} standard{typeStandards.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {typeStandards.map((standard) => (
                    <StandardCard
                      key={standard.id}
                      standard={standard}
                      isEditing={editingId === standard.id}
                      onEdit={() => setEditingId(standard.id)}
                      onSave={(updates) => {
                        updateStandard(standard.id, updates);
                        setEditingId(null);
                      }}
                      onCancel={() => setEditingId(null)}
                      onRemove={() => removeStandard(standard.id)}
                    />
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>
        
        <TabsContent value="all-standards" className="space-y-3">
          {standards.map((standard) => (
            <StandardCard
              key={standard.id}
              standard={standard}
              isEditing={editingId === standard.id}
              onEdit={() => setEditingId(standard.id)}
              onSave={(updates) => {
                updateStandard(standard.id, updates);
                setEditingId(null);
              }}
              onCancel={() => setEditingId(null)}
              onRemove={() => removeStandard(standard.id)}
            />
          ))}
        </TabsContent>
        
        <TabsContent value="add-new">
          <Card>
            <CardHeader>
              <CardTitle>Add New Standard</CardTitle>
              <CardDescription>
                Define a new architecture requirement for this engagement
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="requirement-type">Requirement Type</Label>
                  <Select
                    value={newStandard.requirement_type}
                    onValueChange={(value) => setNewStandard({ ...newStandard, requirement_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {REQUIREMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="verification-status">Verification Status</Label>
                  <Select
                    value={newStandard.verification_status}
                    onValueChange={(value) => setNewStandard({ ...newStandard, verification_status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      {VERIFICATION_STATUSES.map((status) => (
                        <SelectItem key={status.value} value={status.value}>
                          {status.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the architecture requirement..."
                  value={newStandard.description}
                  onChange={(e) => setNewStandard({ ...newStandard, description: e.target.value })}
                  rows={3}
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="mandatory"
                  checked={newStandard.mandatory}
                  onCheckedChange={(checked) => setNewStandard({ ...newStandard, mandatory: checked })}
                />
                <Label htmlFor="mandatory">Mandatory requirement</Label>
              </div>
              
              <Button 
                onClick={addNewStandard}
                disabled={!newStandard.requirement_type || !newStandard.description}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Standard
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      {standards.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No architecture standards defined yet.</p>
          <p className="text-sm mt-1">Start by selecting a template or adding custom standards.</p>
        </div>
      )}
    </div>
  );
};

interface StandardCardProps {
  standard: ArchitectureStandard;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (updates: Partial<ArchitectureStandard>) => void;
  onCancel: () => void;
  onRemove: () => void;
}

const StandardCard: React.FC<StandardCardProps> = ({
  standard,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onRemove
}) => {
  const [editData, setEditData] = useState<Partial<ArchitectureStandard>>(standard);
  
  const getRequirementTypeColor = (type: string) => {
    const reqType = REQUIREMENT_TYPES.find(rt => rt.value === type);
    return reqType?.color || 'bg-gray-100 text-gray-700';
  };
  
  if (isEditing) {
    return (
      <Card className="border-blue-200">
        <CardContent className="pt-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Requirement Type</Label>
              <Select
                value={editData.requirement_type}
                onValueChange={(value) => setEditData({ ...editData, requirement_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REQUIREMENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Verification Status</Label>
              <Select
                value={editData.verification_status}
                onValueChange={(value) => setEditData({ ...editData, verification_status: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VERIFICATION_STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
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
          
          <div className="flex items-center space-x-2">
            <Switch
              checked={editData.mandatory}
              onCheckedChange={(checked) => setEditData({ ...editData, mandatory: checked })}
            />
            <Label>Mandatory requirement</Label>
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
          <div className="space-y-2 flex-1">
            <div className="flex items-center space-x-2">
              <Badge className={getRequirementTypeColor(standard.requirement_type)}>
                {REQUIREMENT_TYPES.find(rt => rt.value === standard.requirement_type)?.label || standard.requirement_type}
              </Badge>
              {standard.mandatory && (
                <Badge variant="outline" className="text-xs">
                  Mandatory
                </Badge>
              )}
              <Badge variant="secondary" className="text-xs">
                {standard.verification_status?.replace('_', ' ') || 'pending'}
              </Badge>
            </div>
            <p className="text-sm text-gray-700">{standard.description}</p>
            {standard.modified_by && (
              <p className="text-xs text-gray-500">
                Modified by: {standard.modified_by}
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