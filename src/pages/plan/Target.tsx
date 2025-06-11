import React from 'react';
import { Cloud, Loader2, AlertTriangle, Plus, DollarSign, Shield, Server } from 'lucide-react';
import { useTarget } from '@/hooks/useTarget';
import { Sidebar } from '@/components/ui/sidebar';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';

const Target = () => {
  const { data, isLoading, isError, error } = useTarget();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-gray-600">Loading target environment data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <div className="flex-1 ml-64 p-8">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <p>Error loading target environment data: {error?.message}</p>
          </Alert>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors = {
      'Planning': 'bg-blue-100 text-blue-800',
      'In Progress': 'bg-yellow-100 text-yellow-800',
      'Ready': 'bg-green-100 text-green-800',
      'Active': 'bg-purple-100 text-purple-800',
      'Complete': 'bg-green-100 text-green-800',
      'Not Started': 'bg-gray-100 text-gray-800',
      'Compliant': 'bg-green-100 text-green-800',
      'Non-Compliant': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">Target Environment Planning</h1>
                  <p className="text-lg text-gray-600">
                    Design and prepare target environments for migration
                  </p>
                </div>
                <Button variant="primary">
                  <Plus className="h-5 w-5 mr-2" />
                  New Environment
                </Button>
              </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Environments</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.environments_count}</h3>
                  </div>
                  <Cloud className="h-8 w-8 text-blue-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg. Readiness</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.average_readiness}%</h3>
                  </div>
                  <Server className="h-8 w-8 text-green-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Compliance Rate</p>
                    <h3 className="text-2xl font-bold text-gray-900">{data.metrics.compliance_rate}%</h3>
                  </div>
                  <Shield className="h-8 w-8 text-purple-600" />
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Monthly Cost</p>
                    <h3 className="text-2xl font-bold text-gray-900">{formatCurrency(data.metrics.total_monthly_cost)}</h3>
                  </div>
                  <DollarSign className="h-8 w-8 text-yellow-600" />
                </div>
              </Card>
            </div>

            {/* Recommendations */}
            <Card className="mb-8">
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Environment Recommendations</h2>
                <div className="space-y-4">
                  {data.recommendations.map((rec, index) => (
                    <Alert key={index} variant="info">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">{rec.category}:</span>
                          <span className="ml-2">{rec.description}</span>
                        </div>
                        <Badge className={`${rec.priority === 'High' ? 'bg-red-100 text-red-800' : rec.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                          {rec.priority}
                        </Badge>
                      </div>
                    </Alert>
                  ))}
                </div>
              </div>
            </Card>

            {/* Environments Table */}
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Target Environments</h2>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Environment</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Readiness</TableHead>
                      <TableHead>Compliance</TableHead>
                      <TableHead>Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.environments.map((env) => (
                      <TableRow key={env.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{env.name}</div>
                            <div className="text-sm text-gray-500">{env.id}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{env.type}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(env.status)}`}>
                            {env.status}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="w-32">
                            <div className="flex justify-between text-sm mb-1">
                              <span>{env.readiness}%</span>
                            </div>
                            <Progress value={env.readiness} />
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-2">
                            {env.compliance.map((item, index) => (
                              <div key={index} className="flex items-center justify-between">
                                <span className="text-sm">{item.framework}</span>
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(item.status)}`}>
                                  {item.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="text-sm">
                              <span className="text-gray-600">Est. Monthly:</span>
                              <span className="ml-2 font-medium">{formatCurrency(env.costs.estimated_monthly)}</span>
                            </div>
                            {env.costs.actual_monthly && (
                              <div className="text-sm">
                                <span className="text-gray-600">Actual:</span>
                                <span className="ml-2 font-medium">{formatCurrency(env.costs.actual_monthly)}</span>
                              </div>
                            )}
                            <div className="text-sm text-green-600">
                              Potential Savings: {formatCurrency(env.costs.savings_potential)}
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>

            {/* Components Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              {data.environments.map((env) => (
                <Card key={env.id} className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">{env.name} Components</h3>
                  <div className="space-y-4">
                    {env.components.map((component, index) => (
                      <div key={index} className="border-b border-gray-200 pb-4 last:border-0 last:pb-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{component.name}</span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(component.status)}`}>
                            {component.status}
                          </span>
                        </div>
                        {component.dependencies.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {component.dependencies.map((dep, i) => (
                              <Badge key={i} variant="outline">{dep}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Target;
