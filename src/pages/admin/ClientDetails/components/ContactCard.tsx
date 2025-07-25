/**
 * ContactCard component for ClientDetails
 * Generated with CC for UI modularization
 */

import React from 'react';
import { Mail, Phone, MapPin } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { Client } from '../types';

interface ContactCardProps {
  client: Client;
}

export const ContactCard: React.FC<ContactCardProps> = ({ client }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Contact Information</CardTitle>
        <CardDescription>Primary contact details for this client</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Mail className="w-5 h-5 text-muted-foreground" />
          <div>
            <p className="font-medium">{client.primary_contact_name}</p>
            <p className="text-sm text-muted-foreground">{client.primary_contact_email}</p>
          </div>
        </div>
        {client.primary_contact_phone && (
          <div className="flex items-center gap-3">
            <Phone className="w-5 h-5 text-muted-foreground" />
            <p className="text-sm">{client.primary_contact_phone}</p>
          </div>
        )}
        <div className="flex items-center gap-3">
          <MapPin className="w-5 h-5 text-muted-foreground" />
          <p className="text-sm">{client.headquarters_location}</p>
        </div>
        {client.billing_contact_email && (
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Billing Contact</p>
              <p className="text-sm">{client.billing_contact_email}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
