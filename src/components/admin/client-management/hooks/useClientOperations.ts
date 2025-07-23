import { useState } from 'react'
import { useCallback } from 'react'
import { useToast } from '@/components/ui/use-toast';
import { useDialog } from '@/hooks/useDialog';
import { apiCall } from '@/config/api';
import type { ClientFormData } from '../types'
import type { Client } from '../types'

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
    } catch (error) {
      console.error('Error creating client:', error);
      
      const errorObj = error as { message?: string; response?: { detail?: string | Array<{ loc?: string[]; msg?: string; message?: string }> } };
      let errorMessage = errorObj.message || "Failed to create client. Please try again.";
      if (errorObj.response && errorObj.response.detail) {
        if (Array.isArray(errorObj.response.detail)) {
          const validationErrors = errorObj.response.detail.map((d: { loc?: string[]; msg?: string; message?: string }) => {
            if (d.loc && d.msg) {
              const field = d.loc[d.loc.length - 1];
              return `${field}: ${d.msg}`;
            }
            return d.msg || d.message || JSON.stringify(d);
          });
          errorMessage = validationErrors.join(', ');
        } else {
          errorMessage = String(errorObj.response.detail);
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
    } catch (error) {
      console.error('Error updating client:', error);
      
      const errorObj = error as { message?: string; response?: { detail?: string | Array<{ msg?: string; message?: string }> } };
      let errorMessage = errorObj.message || "Failed to update client. Please try again.";
      if (errorObj.response && errorObj.response.detail) {
        if (Array.isArray(errorObj.response.detail)) {
          errorMessage = errorObj.response.detail.map((d: { msg?: string; message?: string }) => d.msg || d.message || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = String(errorObj.response.detail);
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
    } catch (error) {
      console.error('Error deleting client:', error);
      
      const errorObj = error as { message?: string; response?: { detail?: string | Array<{ msg?: string; message?: string }> } };
      let errorMessage = errorObj.message || "Failed to delete client. Please try again.";
      if (errorObj.response && errorObj.response.detail) {
        errorMessage = String(errorObj.response.detail);
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