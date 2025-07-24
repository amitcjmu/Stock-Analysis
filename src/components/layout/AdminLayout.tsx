import React from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';
import { useClient } from '@/contexts/ClientContext';
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const { user } = useAuth();
  const { currentClient, availableClients, switchClient } = useClient();

  if (!user) {
    return null; 
  }

  const handleClientSwitch = (clientId: string) => {
    if(switchClient) switchClient(clientId);
  };
  
  return (
    <div className="flex h-screen bg-gray-50/50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header 
          user={user} 
          currentClient={currentClient}
          availableClients={availableClients || []}
          onClientSwitch={handleClientSwitch}
        />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50/50 p-6">
          {children}
        </main>
      </div>
      <Toaster />
      <Sonner />
    </div>
  );
};

export default AdminLayout; 