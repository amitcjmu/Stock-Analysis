/**
 * ClientDetails main component - modularized
 * Generated with CC for UI modularization
 */

import React from 'react';
import type { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { 
  Building2, 
  ArrowLeft,
  Edit,
  Archive,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useClient, useClientForm } from './hooks';
import {
  ContactCard,
  BusinessContextCard,
  AccountInfoCard,
  EngagementSummaryCard,
  AccountDetailsCard,
  EditDialog
} from './components';

const ClientDetails: React.FC = () => {
  const { clientId } = useParams<{ clientId: string }>();
  const navigate = useNavigate();
  
  const { client, isLoading, isError } = useClient(clientId);
  const {
    showEditDialog,
    setShowEditDialog,
    formData,
    setFormData,
    handleEdit,
    handleUpdate
  } = useClientForm(client, clientId);

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">
          <h2 className="text-2xl font-bold mb-4">Client Not Found</h2>
          <p className="text-muted-foreground mb-4">The requested client could not be found.</p>
          <Button onClick={() => navigate('/admin/clients')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Clients
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            onClick={() => navigate('/admin/clients')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Clients
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Building2 className="w-8 h-8" />
              {client.account_name}
              {client.is_active ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
            </h1>
            <p className="text-muted-foreground">
              {client.industry} • {client.company_size}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleEdit}>
            <Edit className="w-4 h-4 mr-2" />
            Edit Client
          </Button>
          <Button variant="outline">
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Information */}
        <div className="lg:col-span-2 space-y-6">
          <ContactCard client={client} />
          <BusinessContextCard client={client} />
          <AccountInfoCard client={client} />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <EngagementSummaryCard client={client} />
          <AccountDetailsCard client={client} />
        </div>
      </div>

      <EditDialog
        client={client}
        showEditDialog={showEditDialog}
        setShowEditDialog={setShowEditDialog}
        formData={formData}
        setFormData={setFormData}
        handleUpdate={handleUpdate}
      />
    </div>
  );
};

export default ClientDetails;