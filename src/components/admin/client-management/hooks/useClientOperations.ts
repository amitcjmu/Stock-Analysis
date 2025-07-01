import { useState, useCallback } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { apiCall } from '@/config/api';
import { Client, ClientFormData } from '../types';

export const useClientOperations = () => {
  const { toast } = useToast();
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
    } catch (error: any) {
      console.error('Error creating client:', error);
      
      let errorMessage = error.message || "Failed to create client. Please try again.";
      if (error.response && error.response.detail) {
        if (Array.isArray(error.response.detail)) {
          const validationErrors = error.response.detail.map((d: any) => {
            if (d.loc && d.msg) {
              const field = d.loc[d.loc.length - 1];
              return `${field}: ${d.msg}`;
            }
            return d.msg || d.message || JSON.stringify(d);
          });
          errorMessage = validationErrors.join(', ');
        } else {
          errorMessage = error.response.detail;
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
    } catch (error: any) {
      console.error('Error updating client:', error);
      
      let errorMessage = error.message || "Failed to update client. Please try again.";
      if (error.response && error.response.detail) {
        if (Array.isArray(error.response.detail)) {
          errorMessage = error.response.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = error.response.detail;
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
    if (!confirm(`Delete client "${clientName}"? This action cannot be undone.`)) return false;

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
    } catch (error: any) {
      console.error('Error deleting client:', error);
      
      let errorMessage = error.message || "Failed to delete client. Please try again.";
      if (error.response && error.response.detail) {
        errorMessage = error.response.detail;
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
  }, [toast]);

  return {
    actionLoading,
    createClient,
    updateClient,
    deleteClient
  };
};