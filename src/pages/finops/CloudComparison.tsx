import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useCostMetrics } from '@/hooks/finops/useFinOpsQueries';
import { NavigationSidebar } from '@/components/navigation/NavigationSidebar';
import { Cloud, BarChart, LineChart, Download, Filter, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { Progress } from '@/components/ui/progress';

const CloudComparison = () => {
  const { isAuthenticated } = useAuth();

  // Queries
  const {
    data: metricsData,
    isLoading: isLoadingMetrics,
    error: metricsError
  } = useCostMetrics();

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Please log in to access cloud cost comparisons.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingMetrics) {
    return <LoadingSkeleton />;
  }

  if (metricsError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load cost metrics.
        </AlertDescription>
      </Alert>
    );
  }

  const metrics = metricsData || {};
  const comparisonMetrics = [
    {
      label: 'Total Cloud Spend',
      value: metrics.totalCost || 0,
      icon: <Cloud className="h-5 w-5" />
    },
    {
      label: 'Projected Annual',
      value: metrics.projectedAnnual || 0,
      icon: <BarChart className="h-5 w-5" />
    },
    {
      label: 'Savings Identified',
      value: metrics.savingsIdentified || 0,
      icon: <LineChart className="h-5 w-5" />
    },
    {
      label: 'Optimization Score',
      value: metrics.optimizationScore || 0,
      icon: <Filter className="h-5 w-5" />
    }
  ];

  return (
    <main className="flex min-h-screen">
      <NavigationSidebar />
      <div className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Cloud Cost Comparison</h1>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {comparisonMetrics.map(({ label, value, icon }) => (
            <Card key={label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
                {icon}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{value}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
};

export default CloudComparison;
