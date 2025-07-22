import { useState, useCallback } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { useDialog } from '@/hooks/useDialog';
import { apiCall } from '@/config/api';
import { Client, ClientFormData } from '../types';

export const useClientOperations = () => {
  const { toast } = useToast();
  const dialog = useDialog();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const createClient = useCallback(async (formData: ClientFormData): Promise<Client | null> => {
    try {
      setActionLoading('create');
      
      const cleanedFormData = {
        ...formData,
        primary_contact_phone: formData.primary_contact_phone?.trim() || null,
        billing_contact_email: formData.billing_contact_email?.trim() || null,
        description: formData.description?.trim() || null,
      };
      
      const response = await apiCall('/admin/clients/', {
        method: 'POST',
        body: JSON.stringify(cleanedFormData)
      });

      if (response.status === 'success') {
        const newClient: Client = {
          id: response.data.id,
          ...formData,
          created_at: response.data.created_at,
          updated_at: response.data.updated_at,
          is_active: true,
          total_engagements: 0,
          active_engagements: 0
        };

        toast({ 
          title: "Success", 
          description: `Client "${formData.account_name}" created successfully` 
        });
        
        return newClient;
      } else {
        throw new Error(response.message || 'Failed to create client');
      }
    } catch (error: unknown) {
      console.error('Error creating client:', error);
      
      const err = error as { message?: string; response?: { detail?: unknown } };
      let errorMessage = err.message || "Failed to create client. Please try again.";
      if (err.response && err.response.detail) {
        if (Array.isArray(err.response.detail)) {
          const validationErrors = err.response.detail.map((d: Record<string, unknown>) => {
            if (d.loc && d.msg) {
              const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : d.loc;
              return `${field}: ${d.msg}`;
            }
            return d.msg || d.message || JSON.stringify(d);
          });
          errorMessage = validationErrors.join(', ');
        } else {
          errorMessage = String(err.response.detail);
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      
      return null;
    } finally {
      setActionLoading(null);
    }
  }, [toast]);

  const updateClient = useCallback(async (client: Client, formData: ClientFormData): Promise<Client | null> => {
    try {
      setActionLoading(client.id);
      
      const cleanedFormData = {
        ...formData,
        primary_contact_phone: formData.primary_contact_phone?.trim() || null,
        billing_contact_email: formData.billing_contact_email?.trim() || null,
        description: formData.description?.trim() || null,
      };
      
      const response = await apiCall(`/admin/clients/${client.id}`, {
        method: 'PUT',
        body: JSON.stringify(cleanedFormData)
      });

      if (response.status === 'success') {
        const updatedClient: Client = {
          ...client,
          ...formData,
          updated_at: response.data.updated_at || new Date().toISOString()
        };

        toast({ 
          title: "Success", 
          description: `Client "${formData.account_name}" updated successfully` 
        });
        
        return updatedClient;
      } else {
        throw new Error(response.message || 'Failed to update client');
      }
    } catch (error: unknown) {
      console.error('Error updating client:', error);
      
      const err = error as { message?: string; response?: { detail?: unknown } };
      let errorMessage = err.message || "Failed to update client. Please try again.";
      if (err.response && err.response.detail) {
        if (Array.isArray(err.response.detail)) {
          errorMessage = err.response.detail.map((d: Record<string, unknown>) => d.msg || d.message || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = String(err.response.detail);
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      
      return null;
    } finally {
      setActionLoading(null);
    }
  }, [toast]);

  const deleteClient = useCallback(async (clientId: string, clientName: string): Promise<boolean> => {
    const confirmed = await dialog.confirm({
      title: 'Delete Client',
      description: `Delete client "${clientName}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      variant: 'destructive',
      icon: 'warning'
    });

    if (!confirmed) return false;

    try {
      setActionLoading(clientId);
      
      const response = await apiCall(`/admin/clients/${clientId}`, {
        method: 'DELETE'
      });

      if (response.status === 'success') {
        toast({ 
          title: "Success", 
          description: `Client "${clientName}" deleted successfully` 
        });
        return true;
      } else {
        throw new Error(response.message || 'Failed to delete client');
      }
    } catch (error: unknown) {
      console.error('Error deleting client:', error);
      
      const err = error as { message?: string; response?: { detail?: unknown } };
      let errorMessage = err.message || "Failed to delete client. Please try again.";
      if (err.response && err.response.detail) {
        errorMessage = String(err.response.detail);
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      
      return false;
    } finally {
      setActionLoading(null);
    }
  }, [toast, dialog]);

  return {
    actionLoading,
    createClient,
    updateClient,
    deleteClient
  };
};