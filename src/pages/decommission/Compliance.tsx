import type React from 'react';
import { Shield, FileText, RefreshCw } from 'lucide-react'
import { CheckCircle, AlertTriangle, Clock, X } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext';
import { useCompliance, useStartAudit, useUpdateRequirement } from '@/hooks/decommission/useCompliance';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import Sidebar from '../../components/Sidebar';

const Compliance = (): JSX.Element => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();

  const {
    data: complianceData,
    isLoading,
    error
  } = useCompliance();

  const { mutate: startAudit, isPending: isStartingAudit } = useStartAudit();
  const { mutate: updateRequirement, isPending: isUpdating } = useUpdateRequirement();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Authentication Required</AlertTitle>
        <AlertDescription>
          Please log in to access the compliance management.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner className="w-8 h-8" />
        <span className="ml-2">Loading compliance information...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load compliance information'}
        </AlertDescription>
      </Alert>
    );
  }

  const { metrics, requirements, frameworks, audits } = complianceData || {
    metrics: [],
    requirements: [],
    frameworks: [],
    audits: []
  };

  const handleStartAudit = (requirementId: string): void => {
    startAudit(requirementId, {
      onSuccess: () => {
        toast({
          title: 'Audit Started',
          description: 'The compliance audit has been initiated.',
        });
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to start audit',
          variant: 'destructive',
        });
      },
    });
  };

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'non_compliant':
        return <X className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string): unknown => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'non_compliant':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Compliance Management</h1>
              <p className="text-lg text-gray-600">
                Monitor and manage compliance requirements for decommissioned systems
              </p>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {metrics.map((metric, index) => {
                const Icon = metric.icon === 'Shield' ? Shield :
                           metric.icon === 'FileText' ? FileText :
                           RefreshCw;
                return (
                  <Card key={index}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">
                        {metric.label}
                      </CardTitle>
                      <Icon className={`h-4 w-4 ${metric.color}`} />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{metric.value}</div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Frameworks */}
            <div className="space-y-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900">Compliance Frameworks</h2>
              <div className="grid gap-6 md:grid-cols-2">
                {frameworks.map((framework) => (
                  <Card key={framework.id}>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <CardTitle>{framework.name}</CardTitle>
                        <Badge variant={framework.status === 'active' ? 'default' : 'secondary'}>
                          {framework.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 mb-4">{framework.description}</p>
                      <div className="text-sm text-gray-500">
                        Last Updated: {new Date(framework.lastUpdated).toLocaleDateString()}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Requirements */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Compliance Requirements</h2>
              <div className="grid gap-6">
                {requirements.map((requirement) => {
                  const activeAudit = audits.find(
                    audit => audit.requirementId === requirement.id && audit.status === 'in_progress'
                  );

                  return (
                    <Card key={requirement.id}>
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <div>
                            <CardTitle>{requirement.name}</CardTitle>
                            <p className="text-sm text-gray-500">{requirement.framework}</p>
                          </div>
                          <Badge className={getStatusColor(requirement.status)}>
                            {requirement.status.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-600 mb-4">{requirement.description}</p>

                        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                          <div>
                            <p className="text-gray-500">Last Checked</p>
                            <p className="font-medium">
                              {new Date(requirement.lastChecked).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Next Check</p>
                            <p className="font-medium">
                              {new Date(requirement.nextCheck).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        {requirement.evidence && requirement.evidence.length > 0 && (
                          <div className="mb-4">
                            <p className="text-sm font-medium text-gray-900 mb-2">Evidence</p>
                            <div className="space-y-1">
                              {requirement.evidence.map((item, index) => (
                                <p key={index} className="text-sm text-gray-600">{item}</p>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex justify-end space-x-2">
                          {!activeAudit && (
                            <Button
                              variant="default"
                              onClick={() => handleStartAudit(requirement.id)}
                              disabled={isStartingAudit}
                            >
                              Start Audit
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Compliance;
