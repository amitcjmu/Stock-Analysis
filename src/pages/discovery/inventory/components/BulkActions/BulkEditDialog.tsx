import React, { useState } from 'react';
import { X, Save } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BulkEditDialogProps } from '../../types';

export const BulkEditDialog: React.FC<BulkEditDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  selectedCount
}) => {
  const [updates, setUpdates] = useState({
    environment: '',
    department: '',
    criticality: '',
    asset_type: ''
  });

  const handleChange = (field: string, value: string) => {
    setUpdates(prev => ({
      ...prev,
      [field]: value === 'none' ? '' : value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Filter out empty fields
    const nonEmptyUpdates = Object.fromEntries(
      Object.entries(updates).filter(([_, value]) => value !== '')
    );
    
    if (Object.keys(nonEmptyUpdates).length > 0) {
      onSave(nonEmptyUpdates);
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Bulk Update {selectedCount} Assets</DialogTitle>
          <DialogDescription>
            Update common fields for {selectedCount} selected assets. Leave fields blank to keep current values.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 py-4">
            {/* Environment */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="environment" className="text-right">
                Environment
              </Label>
              <Select
                value={updates.environment}
                onValueChange={(value) => handleChange('environment', value)}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="No change" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No change</SelectItem>
                  <SelectItem value="production">Production</SelectItem>
                  <SelectItem value="staging">Staging</SelectItem>
                  <SelectItem value="development">Development</SelectItem>
                  <SelectItem value="qa">QA</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Department */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="department" className="text-right">
                Department
              </Label>
              <Select
                value={updates.department}
                onValueChange={(value) => handleChange('department', value)}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="No change" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No change</SelectItem>
                  <SelectItem value="engineering">Engineering</SelectItem>
                  <SelectItem value="marketing">Marketing</SelectItem>
                  <SelectItem value="sales">Sales</SelectItem>
                  <SelectItem value="support">Support</SelectItem>
                  <SelectItem value="operations">Operations</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Criticality */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="criticality" className="text-right">
                Criticality
              </Label>
              <Select
                value={updates.criticality}
                onValueChange={(value) => handleChange('criticality', value)}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="No change" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No change</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Asset Type */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="asset_type" className="text-right">
                Asset Type
              </Label>
              <Select
                value={updates.asset_type}
                onValueChange={(value) => handleChange('asset_type', value)}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="No change" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No change</SelectItem>
                  <SelectItem value="server">Server</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                  <SelectItem value="network">Network Device</SelectItem>
                  <SelectItem value="storage">Storage</SelectItem>
                  <SelectItem value="application">Application</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              Save Changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
