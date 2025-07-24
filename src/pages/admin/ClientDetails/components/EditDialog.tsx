/**
 * EditDialog component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { Client, ClientFormData} from '../types';
import { INDUSTRIES } from '../types'
import { COMPANY_SIZES, SUBSCRIPTION_TIERS } from '../types'

interface EditDialogProps {
  client: Client | null;
  showEditDialog: boolean;
  setShowEditDialog: (show: boolean) => void;
  formData: ClientFormData;
  setFormData: React.Dispatch<React.SetStateAction<ClientFormData>>;
  handleUpdate: () => Promise<void>;
}

export const EditDialog: React.FC<EditDialogProps> = ({
  client,
  showEditDialog,
  setShowEditDialog,
  formData,
  setFormData,
  handleUpdate
}) => {
  return (
    <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Client: {client?.account_name}</DialogTitle>
          <DialogDescription>
            Update client account information and business context.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="account_name">Account Name *</Label>
              <Input
                id="account_name"
                value={formData.account_name}
                onChange={(e) => setFormData(prev => ({ ...prev, account_name: e.target.value }))}
                placeholder="Enter company name"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="industry">Industry *</Label>
              <Select value={formData.industry} onValueChange={(value) => setFormData(prev => ({ ...prev, industry: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map(industry => (
                    <SelectItem key={industry} value={industry}>{industry}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="company_size">Company Size *</Label>
              <Select value={formData.company_size} onValueChange={(value) => setFormData(prev => ({ ...prev, company_size: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select company size" />
                </SelectTrigger>
                <SelectContent>
                  {COMPANY_SIZES.map(size => (
                    <SelectItem key={size} value={size}>{size}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="headquarters_location">Headquarters Location</Label>
              <Input
                id="headquarters_location"
                value={formData.headquarters_location}
                onChange={(e) => setFormData(prev => ({ ...prev, headquarters_location: e.target.value }))}
                placeholder="City, State/Country"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="primary_contact_name">Primary Contact Name</Label>
              <Input
                id="primary_contact_name"
                value={formData.primary_contact_name}
                onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_name: e.target.value }))}
                placeholder="Full name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="primary_contact_email">Primary Contact Email</Label>
              <Input
                id="primary_contact_email"
                type="email"
                value={formData.primary_contact_email}
                onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_email: e.target.value }))}
                placeholder="email@company.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="primary_contact_phone">Primary Contact Phone</Label>
              <Input
                id="primary_contact_phone"
                value={formData.primary_contact_phone}
                onChange={(e) => setFormData(prev => ({ ...prev, primary_contact_phone: e.target.value }))}
                placeholder="+1-555-0123"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="billing_contact_email">Billing Contact Email</Label>
              <Input
                id="billing_contact_email"
                type="email"
                value={formData.billing_contact_email}
                onChange={(e) => setFormData(prev => ({ ...prev, billing_contact_email: e.target.value }))}
                placeholder="billing@company.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="subscription_tier">Subscription Tier</Label>
              <Select value={formData.subscription_tier} onValueChange={(value) => setFormData(prev => ({ ...prev, subscription_tier: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select subscription tier" />
                </SelectTrigger>
                <SelectContent>
                  {SUBSCRIPTION_TIERS.map(tier => (
                    <SelectItem key={tier} value={tier} className="capitalize">{tier}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Brief description of the client and their business"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdate}>
              Update Client
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};