import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { Shield, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AdminRouteProps {
  children: ReactNode;
}

const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  // TODO: Replace with actual authentication check
  // For now, we'll assume admin access is available
  const isAdmin = true; // This would come from auth context
  const isAuthenticated = true; // This would come from auth context

  if (!isAuthenticated) {
    // Redirect to login page (when implemented)
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    // Show access denied message
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <Card className="max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-red-600" />
            </div>
            <CardTitle className="text-red-900">Access Denied</CardTitle>
            <CardDescription>
              You don't have permission to access the admin console.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <div className="flex items-center justify-center gap-2 text-sm text-red-700 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="w-4 h-4" />
              <span>Administrator privileges required</span>
            </div>
            <div className="text-sm text-gray-600">
              <p>If you believe you should have access to this area, please contact your system administrator.</p>
            </div>
            <Button 
              onClick={() => window.history.back()} 
              variant="outline" 
              className="w-full"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // User has admin access, render the protected content
  return <>{children}</>;
};

export default AdminRoute; 