import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, Edit, Trash2, MoreHorizontal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import type { Client } from '../types';

interface ClientTableProps {
  clients: Client[];
  loading: boolean;
  actionLoading: string | null;
  onEditClient: (client: Client) => void;
  onDeleteClient: (clientId: string, clientName: string) => void;
}

export const ClientTable: React.FC<ClientTableProps> = ({
  clients,
  loading,
  actionLoading,
  onEditClient,
  onDeleteClient
}) => {
  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge className="bg-green-100 text-green-800">Active</Badge>
    ) : (
      <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
    );
  };

  const getTierBadge = (tier: string) => {
    const tierStyles: Record<string, string> = {
      'Enterprise': 'bg-purple-100 text-purple-800',
      'Professional': 'bg-blue-100 text-blue-800',
      'Standard': 'bg-gray-100 text-gray-800',
      'Free Trial': 'bg-yellow-100 text-yellow-800'
    };
    return <Badge className={tierStyles[tier] || 'bg-gray-100 text-gray-800'}>{tier}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading clients...</div>
      </div>
    );
  }

  if (clients.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <p>No clients found</p>
        <p className="text-sm mt-1">Create your first client to get started</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Account Name</TableHead>
            <TableHead>Industry</TableHead>
            <TableHead>Primary Contact</TableHead>
            <TableHead>Engagements</TableHead>
            <TableHead>Subscription</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clients.map((client) => (
            <TableRow key={client.id}>
              <TableCell className="font-medium">
                <Link 
                  to={`/admin/clients/${client.id}`} 
                  className="hover:underline"
                >
                  {client.account_name}
                </Link>
              </TableCell>
              <TableCell>{client.industry}</TableCell>
              <TableCell>
                <div className="text-sm">
                  <div>{client.primary_contact_name}</div>
                  <div className="text-gray-500">{client.primary_contact_email}</div>
                </div>
              </TableCell>
              <TableCell>
                <div className="text-sm">
                  <span className="font-medium">{client.active_engagements || 0}</span>
                  <span className="text-gray-500">/{client.total_engagements || 0}</span>
                </div>
              </TableCell>
              <TableCell>{getTierBadge(client.subscription_tier)}</TableCell>
              <TableCell>{getStatusBadge(client.is_active)}</TableCell>
              <TableCell className="text-sm text-gray-500">
                {new Date(client.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      disabled={actionLoading === client.id}
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link to={`/admin/clients/${client.id}`}>
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEditClient(client)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => onDeleteClient(client.id, client.account_name)}
                      className="text-red-600"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};