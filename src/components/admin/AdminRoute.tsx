import React from 'react'
import { ReactNode } from 'react'
import { useEffect, useState, useRef } from 'react'
import { Navigate, useLocation } from 'react-router-dom';
import { Shield, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

interface AdminRouteProps {
  children: ReactNode;
}

const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { isAuthenticated, isAdmin, isLoading, user } = useAuth();
  const location = useLocation();
  const [stateStabilized, setStateStabilized] = useState(false);
  const lastLoggedStateRef = useRef<string>('');

  // Reduced debug logging - only log when state actually changes
  const currentState = JSON.stringify({
    isAuthenticated,
    isAdmin,
    isLoading,
    stateStabilized,
    userId: user?.id,
    userRole: user?.role,
    location: location.pathname
  });

  if (currentState !== lastLoggedStateRef.current) {
    console.log('🛡️ AdminRoute State Change:', {
      isAuthenticated,
      isAdmin,
      isLoading,
      stateStabilized,
      user: user ? { id: user.id, role: user.role, full_name: user.full_name } : null,
      location: location.pathname
    });
    lastLoggedStateRef.current = currentState;
  }

  // Wait for authentication state to stabilize
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      // Add a small delay to ensure state is fully updated
      const timer = setTimeout(() => {
        setStateStabilized(true);
        console.log('🛡️ AdminRoute State Stabilized:', {
          isAdmin,
          userRole: user?.role,
          finalDecision: isAdmin || user?.role === 'admin' || user?.role === 'platform_admin'
        });
      }, 100);
      return () => clearTimeout(timer);
    } else if (!isLoading && !isAuthenticated) {
      setStateStabilized(true);
    }
  }, [isLoading, isAuthenticated, isAdmin, user?.role]);

  // Show loading state while checking authentication or waiting for state to stabilize
  if (isLoading || (isAuthenticated && !stateStabilized)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">
            {isLoading ? 'Loading...' : 'Verifying admin access...'}
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page with return location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check admin access using both isAdmin computed property and direct user role check
  const hasAdminAccess = isAdmin || user?.role === 'admin' || user?.role === 'platform_admin';
  
  // Only log access check if it's a new decision
  const accessDecision = `${hasAdminAccess}-${user?.role}`;
  if (accessDecision !== lastLoggedStateRef.current + '-access') {
    console.log('🛡️ AdminRoute Access Check:', {
      isAdmin,
      userRole: user?.role,
      hasAdminAccess,
      finalDecision: hasAdminAccess
    });
    lastLoggedStateRef.current += '-access';
  }

  if (!hasAdminAccess) {
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
            <div className="text-sm text-gray-600 space-y-2">
              <p>Current user: <strong>{user?.full_name}</strong> ({user?.role})</p>
              <p>If you believe you should have access to this area, please contact your system administrator.</p>
            </div>
            <div className="flex flex-col gap-2">
              <Button 
                onClick={() => window.history.back()} 
                variant="outline" 
                className="w-full"
              >
                Go Back
              </Button>
              <Button 
                onClick={() => window.location.href = '/'}
                className="w-full"
              >
                Return to Platform
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // User has admin access, render the protected content
  return <>{children}</>;
};

export default AdminRoute; 