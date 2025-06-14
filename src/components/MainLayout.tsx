import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '@/components/Sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import Header from './Header'; // This component needs to be created or path fixed
import { useClient } from '@/contexts/ClientContext';

const MainLayout: React.FC = () => {
  const { user } = useAuth();
  const { currentClient, availableClients, switchClient } = useClient();

  const handleClientSwitch = (clientId: string) => {
    if (switchClient) {
      switchClient(clientId);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="ml-64 flex flex-1 flex-col overflow-hidden">
        {user && (
          <Header
            user={user}
            currentClient={currentClient}
            availableClients={availableClients || []}
            onClientSwitch={handleClientSwitch}
          />
        )}
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <Toaster />
      <Sonner />
    </div>
  );
};

export default MainLayout; 