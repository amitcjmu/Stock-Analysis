import type React from 'react';
import { Archive, Database, HardDrive } from 'lucide-react'
import { CheckCircle, AlertTriangle, Clock, X } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext';
import { useArchival, useStartArchival, useVerifyArchival } from '@/hooks/decommission/useArchival';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import Sidebar from '../../components/Sidebar';

const Archival = () => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();

  const {
    data: archivalData,
    isLoading,
    error
  } = useArchival();

  const { mutate: startArchival, isPending: isStarting } = useStartArchival();
  const { mutate: verifyArchival, isPending: isVerifying } = useVerifyArchival();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Authentication Required</AlertTitle>
        <AlertDescription>
          Please log in to access the archival management.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner className="w-8 h-8" />
        <span className="ml-2">Loading archival information...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load archival information'}
        </AlertDescription>
      </Alert>
    );
  }

  const { metrics, systems, tasks } = archivalData || {
    metrics: [],
    systems: [],
    tasks: []
  };

  const handleStartArchival = (systemId: string) => {
    startArchival(systemId, {
      onSuccess: () => {
        toast({
          title: 'Archival Started',
          description: 'The archival process has been initiated.',
        });
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to start archival',
          variant: 'destructive',
        });
      },
    });
  };

  const handleVerifyArchival = (systemId: string) => {
    verifyArchival(systemId, {
      onSuccess: () => {
        toast({
          title: 'Verification Started',
          description: 'The archival verification process has been initiated.',
        });
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to start verification',
          variant: 'destructive',
        });
      },
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <X className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">System Archival</h1>
              <p className="text-lg text-gray-600">
                Manage and monitor system archival processes
              </p>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {metrics.map((metric, index) => {
                const Icon = metric.icon === 'Database' ? Database :
                           metric.icon === 'Archive' ? Archive :
                           HardDrive;
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

            {/* Systems */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Systems</h2>
              <div className="grid gap-6">
                {systems.map((system) => (
                  <Card key={system.id}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0">
                      <div>
                        <CardTitle>{system.name}</CardTitle>
                        <p className="text-sm text-gray-500">
                          {system.dataSize} • {system.retentionPolicy}
                        </p>
                      </div>
                      <Badge className={getStatusColor(system.status)}>
                        {system.status.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-500">Archive Location</p>
                            <p className="font-medium">{system.archiveLocation}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Last Backup</p>
                            <p className="font-medium">
                              {new Date(system.lastBackup).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        {/* Active Tasks */}
                        {tasks
                          .filter(task => task.systemId === system.id && task.status === 'running')
                          .map(task => (
                            <div key={task.id} className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-500">
                                  {task.type.charAt(0).toUpperCase() + task.type.slice(1)}
                                </span>
                                <span>{task.progress}%</span>
                              </div>
                              <Progress value={task.progress} />
                            </div>
                          ))
                        }

                        <div className="flex justify-end space-x-2">
                          {system.status === 'pending' && (
                            <Button
                              variant="default"
                              onClick={() => handleStartArchival(system.id)}
                              disabled={isStarting}
                            >
                              Start Archival
                            </Button>
                          )}
                          {system.status === 'completed' && (
                            <Button
                              variant="secondary"
                              onClick={() => handleVerifyArchival(system.id)}
                              disabled={isVerifying}
                            >
                              Verify Archive
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Archival;
