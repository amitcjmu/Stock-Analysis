import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle } from 'lucide-react'
import { AlertTriangle, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { TechDebtSummary } from '@/types/tech-debt';

interface TechDebtSummaryCardsProps {
  summary: TechDebtSummary;
  onFilter: (filter: string, value: string) => void;
}

export function TechDebtSummaryCards({ summary, onFilter }: TechDebtSummaryCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card className="border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-900/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-red-600 dark:text-red-400">
            Critical Issues
          </CardTitle>
          <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">
            {summary.critical}
          </div>
          <button
            onClick={() => onFilter('risk', 'critical')}
            className="text-xs text-red-500 hover:underline dark:text-red-400"
          >
            View all
          </button>
        </CardContent>
      </Card>

      <Card className="border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-900/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-amber-600 dark:text-amber-400">
            High Risk
          </CardTitle>
          <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {summary.high}
          </div>
          <button
            onClick={() => onFilter('risk', 'high')}
            className="text-xs text-amber-500 hover:underline dark:text-amber-400"
          >
            View all
          </button>
        </CardContent>
      </Card>

      <Card className="border-blue-200 bg-blue-50 dark:border-blue-900/50 dark:bg-blue-900/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-blue-600 dark:text-blue-400">
            End of Life
          </CardTitle>
          <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {summary.endOfLife}
          </div>
          <button
            onClick={() => onFilter('status', 'end_of_life')}
            className="text-xs text-blue-500 hover:underline dark:text-blue-400"
          >
            View all
          </button>
        </CardContent>
      </Card>

      <Card className="border-green-200 bg-green-50 dark:border-green-900/50 dark:bg-green-900/20">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-green-600 dark:text-green-400">
            Total Items
          </CardTitle>
          <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {summary.totalItems}
          </div>
          <button
            onClick={() => {
              onFilter('risk', 'all');
              onFilter('status', 'all');
            }}
            className="text-xs text-green-500 hover:underline dark:text-green-400"
          >
            View all
          </button>
        </CardContent>
      </Card>
    </div>
  );
}
