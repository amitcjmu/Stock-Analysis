import React from 'react';
import { Outlet } from 'react-router-dom';
import { Shield, Settings } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface AdminLayoutProps {
  children?: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-blue-600" />
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Administration</h1>
              <p className="text-sm text-gray-600">AI Force Migration Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Settings className="h-4 w-4" />
            <span>Admin Console</span>
          </div>
        </div>
      </div>

      {/* Admin Content */}
      <div className="container mx-auto">
        {children || <Outlet />}
      </div>
    </div>
  );
};

export default AdminLayout; 