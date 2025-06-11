// Core React and state management
import React, { useState } from 'react';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';

// Icons
import { 
  AlertTriangle, 
  ArrowRight, 
  Check, 
  ChevronDown, 
  ChevronRight, 
  Filter as FilterIcon, 
  Search as SearchIcon, 
  X as XIcon,
  AlertCircle, 
  CheckCircle, 
  Clock,
  Code,
  BarChart3,
  Bug,
  MoreVertical, 
  ExternalLink, 
  Download, 
  Trash2,
  Filter,
  X,
  FolderX
} from 'lucide-react';

// UI Components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';

// Custom Hooks and Types
import { useAuth } from '@/contexts/AuthContext';
import { 
  useTechDebtData, 
  useSupportTimelines, 
  useUpdateTechDebtItem,
  useDeleteTechDebtItem,
  type TechDebtCategory,
  type TechDebtItem,
  type SupportTimeline
} from '@/hooks/discovery/useTechDebtQueries';

// Components
import NavigationSidebar from '@/components/navigation/NavigationSidebar';
import { ContextBreadcrumbs } from '@/components/context/ContextBreadcrumbs';
import { TechDebtSummaryCards, TechDebtFilters, TechDebtItemCard } from '@/components/tech-debt';

// Error boundary fallback component
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center bg-red-50 rounded-lg">
    <div className="flex items-center">
      <AlertCircle className="h-12 w-12 text-red-500 mr-4" />
      <div className="text-left">
        <h3 className="text-lg font-medium text-red-800">
          Something went wrong
        </h3>
        <p className="text-red-700 mt-2">{error.message}</p>
        <Button
          variant="outline"
          onClick={resetErrorBoundary}
          className="mt-4 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          <ArrowRight className="mr-2 h-4 w-4" />
          Try again
        </Button>
      </div>
    </div>
  </div>
);

// Loading skeleton component
const LoadingSkeleton = () => (
  <div className="space-y-4">
    <div className="flex justify-between items-center">
      <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="flex space-x-2">
        <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    </div>
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
      ))}
    </div>
    <div className="h-64 w-full bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
  </div>
);

const TechDebtAnalysis: React.FC = () => {
  // Auth and context
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const { reset } = useQueryErrorResetBoundary();

  // State for filters and selection
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<TechDebtCategory>('all');
  const [selectedRisk, setSelectedRisk] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  // Queries
  const { 
    data: techDebtData,
    isLoading: isLoadingTechDebt,
    error: techDebtError
  } = useTechDebtData({
    category: selectedCategory,
    risk: selectedRisk,
    status: selectedStatus,
    search: searchQuery
  });

  const {
    data: supportTimelines,
    isLoading: isLoadingTimelines
  } = useSupportTimelines();

  // Mutations
  const { mutate: updateTechDebtItem } = useUpdateTechDebtItem();
  const { mutate: deleteTechDebtItem } = useDeleteTechDebtItem();

  // Helper functions
  const getComponentIcon = (component: string) => {
    switch (component.toLowerCase()) {
      case 'code':
        return <Code className="h-4 w-4" />;
      case 'performance':
        return <BarChart3 className="h-4 w-4" />;
      case 'security':
        return <AlertTriangle className="h-4 w-4" />;
      case 'bugs':
        return <Bug className="h-4 w-4" />;
      default:
        return <Code className="h-4 w-4" />;
    }
  };

  const getSupportStatusColor = (status: string) => {
    const colors = {
      'active': 'bg-green-100 text-green-800',
      'maintenance': 'bg-yellow-100 text-yellow-800',
      'security': 'bg-orange-100 text-orange-800',
      'end_of_life': 'bg-red-100 text-red-800',
      'end_of_support': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getRiskColor = (risk: string) => {
    const colors = {
      'critical': 'bg-red-100 text-red-800',
      'high': 'bg-orange-100 text-orange-800',
      'medium': 'bg-yellow-100 text-yellow-800',
      'low': 'bg-green-100 text-green-800'
    };
    return colors[risk] || 'bg-gray-100 text-gray-800';
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'medium':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'low':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const calculateDaysUntilEOL = (endDate: string): number => {
    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end.getTime() - now.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const renderSupportTimeline = (timeline: SupportTimeline) => {
    const daysUntilEOL = calculateDaysUntilEOL(timeline.endOfLife);
    const statusColor = getSupportStatusColor(timeline.status);
    
    return (
      <div key={timeline.id} className="p-4 border rounded-lg mb-4">
        <div className="flex justify-between items-start mb-2">
          <div>
            <h4 className="font-medium">{timeline.name}</h4>
            <p className="text-sm text-gray-600">{timeline.description}</p>
          </div>
          <Badge className={statusColor}>
            {timeline.status}
          </Badge>
        </div>
        <div className="mt-4">
          <div className="flex justify-between text-sm">
            <span>Days until EOL:</span>
            <span className={daysUntilEOL < 90 ? 'text-red-600' : 'text-gray-600'}>
              {daysUntilEOL} days
            </span>
          </div>
          <Progress 
            value={Math.max(0, Math.min(100, (daysUntilEOL / 365) * 100))} 
            className="mt-2"
          />
        </div>
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Authentication Required</AlertTitle>
        <AlertDescription>
          Please log in to access the technical debt analysis.
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoadingTechDebt || isLoadingTimelines) {
    return <LoadingSkeleton />;
  }

  if (techDebtError) {
    return (
      <ErrorBoundary FallbackComponent={ErrorFallback} onReset={reset}>
        <div>Error: {techDebtError.message}</div>
      </ErrorBoundary>
    );
  }

  const { items: techDebtItems, summary } = techDebtData || { items: [], summary: null };

  return (
    <div className="flex h-screen">
      <NavigationSidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <ContextBreadcrumbs />
          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">Technical Debt Analysis</h1>
            <p className="text-gray-600">
              Analyze and track technical debt across your applications
            </p>
          </div>

          {summary && <TechDebtSummaryCards summary={summary} />}

          <div className="mb-6">
            <TechDebtFilters
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
              selectedRisk={selectedRisk}
              setSelectedRisk={setSelectedRisk}
              selectedStatus={selectedStatus}
              setSelectedStatus={setSelectedStatus}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {techDebtItems.map((item) => (
              <TechDebtItemCard
                key={item.id}
                item={item}
                onUpdate={updateTechDebtItem}
                onDelete={deleteTechDebtItem}
                selected={selectedItems.has(item.id)}
                onSelect={(selected) => {
                  const newSelected = new Set(selectedItems);
                  if (selected) {
                    newSelected.add(item.id);
                  } else {
                    newSelected.delete(item.id);
                  }
                  setSelectedItems(newSelected);
                }}
              />
            ))}
          </div>

          {supportTimelines && supportTimelines.length > 0 && (
            <div className="mt-8">
              <h2 className="text-xl font-semibold mb-4">Support Timelines</h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {supportTimelines.map(renderSupportTimeline)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TechDebtAnalysis;

  return (
    <div className="flex h-screen">
      <NavigationSidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <ContextBreadcrumbs />
          <div className="mb-8">
            <h1 className="text-2xl font-bold mb-2">Technical Debt Analysis</h1>
            <p className="text-gray-600">
              Analyze and track technical debt across your applications
            </p>
          </div>

          {summary && <TechDebtSummaryCards summary={summary} />}

          <div className="mb-6">
            <TechDebtFilters
              selectedCategory={selectedCategory}
              setSelectedCategory={setSelectedCategory}
              selectedRisk={selectedRisk}
              setSelectedRisk={setSelectedRisk}
              selectedStatus={selectedStatus}
              setSelectedStatus={setSelectedStatus}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {techDebtItems.map((item) => (
              <TechDebtItemCard
                key={item.id}
                item={item}
                onUpdate={updateTechDebtItem}
                onDelete={deleteTechDebtItem}
                selected={selectedItems.has(item.id)}
                onSelect={(selected) => {
                  const newSelected = new Set(selectedItems);
                  if (selected) {
                    newSelected.add(item.id);
                  } else {
                    newSelected.delete(item.id);
                  }
                  setSelectedItems(newSelected);
                }}
              />
            ))}
          </div>

          {supportTimelines && supportTimelines.length > 0 && (
            <div className="mt-8">
              <h2 className="text-xl font-semibold mb-4">Support Timelines</h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {supportTimelines.map(renderSupportTimeline)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TechDebtAnalysis;