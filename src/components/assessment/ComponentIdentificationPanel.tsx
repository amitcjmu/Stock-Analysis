import React from 'react'
import type { useState } from 'react'
import { Button } from '@/components/ui/button';
import type { Input } from '@/components/ui/input';
import type { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ApplicationComponent } from '@/hooks/useAssessmentFlow';
import type { Database, Globe, Cpu } from 'lucide-react'
import { Plus, Edit3, Trash2, Server } from 'lucide-react'
import { cn } from '@/lib/utils';

interface ComponentIdentificationPanelProps {
  components: ApplicationComponent[];
  onComponentsChange: (components: ApplicationComponent[]) => void;
  editingComponent: string | null;
  onEditComponent: (componentName: string | null) => void;
}

const COMPONENT_TYPES = [
  { value: 'web_frontend', label: 'Web Frontend', icon: Globe, color: 'bg-blue-100 text-blue-700' },
  { value: 'api_service', label: 'API Service', icon: Server, color: 'bg-green-100 text-green-700' },
  { value: 'database', label: 'Database', icon: Database, color: 'bg-purple-100 text-purple-700' },
  { value: 'message_queue', label: 'Message Queue', icon: Cpu, color: 'bg-orange-100 text-orange-700' },
  { value: 'batch_job', label: 'Batch Job', icon: Cpu, color: 'bg-gray-100 text-gray-700' },
  { value: 'microservice', label: 'Microservice', icon: Server, color: 'bg-indigo-100 text-indigo-700' },
  { value: 'monolith', label: 'Monolithic Application', icon: Server, color: 'bg-red-100 text-red-700' },
  { value: 'integration', label: 'Integration Layer', icon: Cpu, color: 'bg-teal-100 text-teal-700' }
];

export const ComponentIdentificationPanel: React.FC<ComponentIdentificationPanelProps> = ({
  components,
  onComponentsChange,
  editingComponent,
  onEditComponent
}) => {
  const [newComponent, setNewComponent] = useState<Partial<ApplicationComponent>>({
    component_name: '',
    component_type: '',
    technology_stack: {},
    dependencies: []
  });

  const addComponent = () => {
    if (!newComponent.component_name || !newComponent.component_type) return;

    const component: ApplicationComponent = {
      component_name: newComponent.component_name,
      component_type: newComponent.component_type,
      technology_stack: newComponent.technology_stack || {},
      dependencies: newComponent.dependencies || []
    };

    onComponentsChange([...components, component]);
    setNewComponent({
      component_name: '',
      component_type: '',
      technology_stack: {},
      dependencies: []
    });
  };

  const updateComponent = (oldName: string, updatedComponent: ApplicationComponent) => {
    const updatedComponents = components.map(comp =>
      comp.component_name === oldName ? updatedComponent : comp
    );
    onComponentsChange(updatedComponents);
  };

  const removeComponent = (componentName: string) => {
    onComponentsChange(components.filter(comp => comp.component_name !== componentName));
  };

  const getComponentTypeInfo = (type: string) => {
    return COMPONENT_TYPES.find(ct => ct.value === type) || {
      value: type,
      label: type,
      icon: Server,
      color: 'bg-gray-100 text-gray-700'
    };
  };

  return (
    <div className="space-y-6">
      {/* Add New Component */}
      <Card>
        <CardHeader>
          <CardTitle>Add Component</CardTitle>
          <CardDescription>
            Identify a new component within this application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="component-name">Component Name</Label>
              <Input
                id="component-name"
                placeholder="e.g., User Service API"
                value={newComponent.component_name}
                onChange={(e) => setNewComponent({ ...newComponent, component_name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="component-type">Component Type</Label>
              <Select
                value={newComponent.component_type}
                onValueChange={(value) => setNewComponent({ ...newComponent, component_type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select component type" />
                </SelectTrigger>
                <SelectContent>
                  {COMPONENT_TYPES.map((type) => {
                    const Icon = type.icon;
                    return (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4" />
                          <span>{type.label}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button 
            onClick={addComponent}
            disabled={!newComponent.component_name || !newComponent.component_type}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Component
          </Button>
        </CardContent>
      </Card>

      {/* Components List */}
      {components.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <Server className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Components Identified</h3>
            <p className="text-gray-600">
              Start by adding the first component of this application above.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {components.map((component) => (
            <ComponentCard
              key={component.component_name}
              component={component}
              isEditing={editingComponent === component.component_name}
              onEdit={() => onEditComponent(component.component_name)}
              onSave={(updated) => {
                updateComponent(component.component_name, updated);
                onEditComponent(null);
              }}
              onCancel={() => onEditComponent(null)}
              onRemove={() => removeComponent(component.component_name)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface ComponentCardProps {
  component: ApplicationComponent;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (component: ApplicationComponent) => void;
  onCancel: () => void;
  onRemove: () => void;
}

const ComponentCard: React.FC<ComponentCardProps> = ({
  component,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onRemove
}) => {
  const [editData, setEditData] = useState<ApplicationComponent>(component);

  const getComponentTypeInfo = (type: string) => {
    return COMPONENT_TYPES.find(ct => ct.value === type) || {
      value: type,
      label: type,
      icon: Server,
      color: 'bg-gray-100 text-gray-700'
    };
  };

  const typeInfo = getComponentTypeInfo(component.component_type);
  const Icon = typeInfo.icon;

  if (isEditing) {
    return (
      <Card className="border-blue-200">
        <CardContent className="pt-4 space-y-4">
          <div className="space-y-2">
            <Label>Component Name</Label>
            <Input
              value={editData.component_name}
              onChange={(e) => setEditData({ ...editData, component_name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Component Type</Label>
            <Select
              value={editData.component_type}
              onValueChange={(value) => setEditData({ ...editData, component_type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {COMPONENT_TYPES.map((type) => {
                  const TypeIcon = type.icon;
                  return (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center space-x-2">
                        <TypeIcon className="h-4 w-4" />
                        <span>{type.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Dependencies (comma-separated)</Label>
            <Input
              placeholder="e.g., Database, External API"
              value={editData.dependencies?.join(', ') || ''}
              onChange={(e) => setEditData({ 
                ...editData, 
                dependencies: e.target.value.split(',').map(d => d.trim()).filter(Boolean)
              })}
            />
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
            <div className="flex items-center space-x-3">
              <div className={cn("p-2 rounded-lg", typeInfo.color)}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{component.component_name}</h3>
                <Badge className={typeInfo.color} variant="outline">
                  {typeInfo.label}
                </Badge>
              </div>
            </div>

            {component.dependencies && component.dependencies.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-700">Dependencies:</p>
                <div className="flex flex-wrap gap-1">
                  {component.dependencies.map((dep, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {dep}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {component.technology_stack && Object.keys(component.technology_stack).length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-700">Technology Stack:</p>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(component.technology_stack).map(([key, value]) => (
                    <Badge key={key} variant="outline" className="text-xs">
                      {key}: {value}
                    </Badge>
                  ))}
                </div>
              </div>
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