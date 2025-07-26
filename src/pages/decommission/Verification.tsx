import type React from 'react';
import { CheckCircle, AlertTriangle, Clock, X, FileText, Download, RefreshCw, Database } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useVerification, useRunVerification, useGenerateReport } from '@/hooks/decommission/useVerification';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import Sidebar from '../../components/Sidebar';

const Verification = (): JSX.Element => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();

  const {
    data: verificationData,
    isLoading,
    error
  } = useVerification();

  const { mutate: runVerification, isPending: isRunning } = useRunVerification();
  const { mutate: generateReport, isPending: isGenerating } = useGenerateReport();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Authentication Required</AlertTitle>
        <AlertDescription>
          Please log in to access the verification management.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner className="w-8 h-8" />
        <span className="ml-2">Loading verification information...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load verification information'}
        </AlertDescription>
      </Alert>
    );
  }

  const { metrics, checks, reports } = verificationData || {
    metrics: [],
    checks: [],
    reports: []
  };

  const handleRunVerification = (checkId: string): void => {
    runVerification(checkId, {
      onSuccess: () => {
        toast({
          title: 'Verification Started',
          description: 'The verification check has been initiated.',
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

  const handleGenerateReport = (checkId: string): void => {
    generateReport(checkId, {
      onSuccess: () => {
        toast({
          title: 'Report Generated',
          description: 'The verification report has been generated.',
        });
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to generate report',
          variant: 'destructive',
        });
      },
    });
  };

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <X className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string): unknown => {
    switch (status) {
      case 'passed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getTypeIcon = (type: string): JSX.Element => {
    switch (type) {
      case 'data_integrity':
        return <Database className="h-4 w-4" />;
      case 'compliance':
        return <FileText className="h-4 w-4" />;
      case 'security':
        return <AlertTriangle className="h-4 w-4" />;
      case 'accessibility':
        return <RefreshCw className="h-4 w-4" />;
      default:
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Verification Management</h1>
              <p className="text-lg text-gray-600">
                Verify and validate decommissioned systems
              </p>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {metrics.map((metric, index) => {
                const Icon = metric.icon === 'Database' ? Database :
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

            {/* Verification Checks */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Verification Checks</h2>
              <div className="grid gap-6">
                {checks.map((check) => {
                  const latestReport = reports.find(report => report.checkId === check.id);

                  return (
                    <Card key={check.id}>
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <div className="flex items-center space-x-2">
                            {getTypeIcon(check.type)}
                            <div>
                              <CardTitle>{check.name}</CardTitle>
                              <p className="text-sm text-gray-500">
                                {check.type.replace('_', ' ').toUpperCase()}
                              </p>
                            </div>
                          </div>
                          <Badge className={getStatusColor(check.status)}>
                            {check.status.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-600 mb-4">{check.description}</p>

                        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                          {check.lastRun && (
                            <div>
                              <p className="text-gray-500">Last Run</p>
                              <p className="font-medium">
                                {new Date(check.lastRun).toLocaleDateString()}
                              </p>
                            </div>
                          )}
                          {check.nextRun && (
                            <div>
                              <p className="text-gray-500">Next Run</p>
                              <p className="font-medium">
                                {new Date(check.nextRun).toLocaleDateString()}
                              </p>
                            </div>
                          )}
                        </div>

                        {check.findings && check.findings.length > 0 && (
                          <div className="mb-4">
                            <p className="text-sm font-medium text-gray-900 mb-2">Findings</p>
                            <div className="space-y-1">
                              {check.findings.map((finding, index) => (
                                <p key={index} className="text-sm text-gray-600">{finding}</p>
                              ))}
                            </div>
                          </div>
                        )}

                        {check.recommendations && check.recommendations.length > 0 && (
                          <div className="mb-4">
                            <p className="text-sm font-medium text-gray-900 mb-2">Recommendations</p>
                            <div className="space-y-1">
                              {check.recommendations.map((recommendation, index) => (
                                <p key={index} className="text-sm text-gray-600">{recommendation}</p>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex justify-end space-x-2">
                          {check.status !== 'in_progress' && (
                            <Button
                              variant="default"
                              onClick={() => handleRunVerification(check.id)}
                              disabled={isRunning}
                            >
                              Run Verification
                            </Button>
                          )}
                          {latestReport && (
                            <Button
                              variant="secondary"
                              onClick={() => handleGenerateReport(check.id)}
                              disabled={isGenerating}
                            >
                              <Download className="h-4 w-4 mr-2" />
                              Download Report
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

export default Verification;
