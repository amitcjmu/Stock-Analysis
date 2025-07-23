import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Shield, AlertTriangle } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { useAuth } from '../../contexts/AuthContext';
import type AgentDetailPage from './AgentDetailPage';

/**
 * Integrated Agent Detail Page with Navigation, Auth, and RBAC
 * This component wraps the AgentDetailPage with proper app integration
 */
const IntegratedAgentDetailPage: React.FC = () => {
  const { agentName } = useParams<{ agentName: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, user, isLoading } = useAuth();
  const [decodedAgentName, setDecodedAgentName] = useState<string>('');

  useEffect(() => {
    if (agentName) {
      try {
        // Decode the agent name from URL encoding
        const decoded = decodeURIComponent(agentName);
        setDecodedAgentName(decoded);
      } catch (error) {
        console.error('Failed to decode agent name:', error);
        setDecodedAgentName(agentName);
      }
    }
  }, [agentName]);

  // Show loading while auth is initializing
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  // Show access denied for non-admin users
  if (!isAdmin) {
    return (
      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumb Navigation */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/observability')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Observability
          </Button>
          <span>/</span>
          <span className="text-gray-400">Agent Details</span>
        </nav>

        {/* Access Denied Message */}
        <Card className="max-w-2xl mx-auto">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <Shield className="h-8 w-8 text-red-600" />
            </div>
            <CardTitle className="text-xl text-red-800">Access Denied</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-gray-600">
              Agent observability details are restricted to administrators only.
            </p>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-left">
                  <p className="font-medium text-yellow-800">Administrative Access Required</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    This page contains sensitive agent performance data and system insights 
                    that require administrative privileges to access.
                  </p>
                </div>
              </div>
            </div>

            <div className="text-sm text-gray-500 space-y-1">
              <p><strong>Current User:</strong> {user?.email || 'Unknown'}</p>
              <p><strong>Role:</strong> <Badge variant="secondary">{isAdmin ? 'Administrator' : 'User'}</Badge></p>
            </div>

            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={() => navigate('/observability')}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Observability
              </Button>
              <Button
                onClick={() => navigate('/')}
              >
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render the integrated agent detail page for admin users
  return (
    <div className="container mx-auto px-4 py-6">
      {/* Breadcrumb Navigation */}
      <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="text-gray-600 hover:text-gray-900"
        >
          Dashboard
        </Button>
        <span>/</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/observability')}
          className="text-gray-600 hover:text-gray-900"
        >
          Observability
        </Button>
        <span>/</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/observability/enhanced')}
          className="text-gray-600 hover:text-gray-900"
        >
          Enhanced Dashboard
        </Button>
        <span>/</span>
        <span className="text-gray-900 font-medium">
          {decodedAgentName || 'Agent Details'}
        </span>
      </nav>

      {/* Admin Badge */}
      <div className="flex items-center gap-3 mb-6">
        <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
          <Shield className="h-3 w-3 mr-1" />
          Administrator Access
        </Badge>
        <Badge variant="outline">
          Agent Observability Dashboard
        </Badge>
      </div>

      {/* Agent Detail Page Content */}
      {decodedAgentName && (
        <AgentDetailPage agentName={decodedAgentName} />
      )}

      {!decodedAgentName && (
        <Card>
          <CardContent className="py-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Invalid Agent Name</h3>
            <p className="text-gray-600 mb-4">
              The agent name in the URL could not be processed.
            </p>
            <Button
              onClick={() => navigate('/observability/enhanced')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Agent List
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IntegratedAgentDetailPage;