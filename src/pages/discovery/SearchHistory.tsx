import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Search, Database, Zap, Filter, RefreshCw, TrendingUp } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '../../config/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Alert, AlertDescription } from '../../components/ui/alert';

interface SearchHistoryItem {
  search_id: string;
  search_query: string;
  search_type: string;
  results_count: number;
  execution_time_ms: number;
  source: string;
  timestamp: string;
}

interface SearchHistoryResponse {
  success: boolean;
  history: SearchHistoryItem[];
  count: number;
  days: number;
}

const SearchHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);
  const [limit, setLimit] = useState(100);
  const [filterQuery, setFilterQuery] = useState('');
  const [filterSource, setFilterSource] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    loadSearchHistory();
  }, [days, limit]);

  const loadSearchHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiCall<SearchHistoryResponse>(
        `/stock/stocks/search/history?days=${days}&limit=${limit}`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.history) {
        setSearchHistory(response.history);
      } else {
        setError('Failed to load search history');
      }
    } catch (err: any) {
      console.error('Error loading search history:', err);
      setError(err.message || 'Failed to load search history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchClick = (query: string) => {
    // Navigate to discovery page with the search query
    navigate('/discovery', {
      state: { searchQuery: query },
    });
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  const formatExecutionTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getSourceBadgeVariant = (source: string) => {
    switch (source.toLowerCase()) {
      case 'cache':
        return 'default';
      case 'database':
        return 'secondary';
      case 'api':
        return 'outline';
      default:
        return 'default';
    }
  };

  const getTypeBadgeVariant = (type: string) => {
    switch (type.toLowerCase()) {
      case 'symbol':
        return 'default';
      case 'company_name':
        return 'secondary';
      case 'fuzzy':
        return 'outline';
      default:
        return 'default';
    }
  };

  // Filter search history
  const filteredHistory = searchHistory.filter((item) => {
    const matchesQuery =
      filterQuery === '' ||
      item.search_query.toLowerCase().includes(filterQuery.toLowerCase());
    const matchesSource = filterSource === 'all' || item.source === filterSource;
    const matchesType = filterType === 'all' || item.search_type === filterType;
    return matchesQuery && matchesSource && matchesType;
  });

  // Calculate statistics
  const stats = {
    total: filteredHistory.length,
    avgExecutionTime: filteredHistory.length > 0
      ? Math.round(
          filteredHistory.reduce((sum, item) => sum + item.execution_time_ms, 0) /
            filteredHistory.length
        )
      : 0,
    cacheHits: filteredHistory.filter((item) => item.source === 'cache').length,
    apiCalls: filteredHistory.filter((item) => item.source === 'api').length,
    dbQueries: filteredHistory.filter((item) => item.source === 'database').length,
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <ContextBreadcrumbs />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                  <Clock className="h-8 w-8 text-blue-600" />
                  Search History
                </h1>
                <p className="text-gray-600 mt-1">
                  Track your stock search history stored in Cassandra
                </p>
              </div>
              <Button onClick={loadSearchHistory} disabled={isLoading} variant="outline">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Total Searches
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.total}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Avg Execution Time
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatExecutionTime(stats.avgExecutionTime)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Cache Hits
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.cacheHits}</div>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.total > 0
                      ? `${Math.round((stats.cacheHits / stats.total) * 100)}% hit rate`
                      : '0%'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    API Calls
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-600">{stats.apiCalls}</div>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.dbQueries > 0 && `${stats.dbQueries} DB queries`}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Filters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Search Query
                    </label>
                    <Input
                      placeholder="Filter by query..."
                      value={filterQuery}
                      onChange={(e) => setFilterQuery(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Data Source
                    </label>
                    <Select value={filterSource} onValueChange={setFilterSource}>
                      <SelectTrigger>
                        <SelectValue placeholder="All sources" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Sources</SelectItem>
                        <SelectItem value="cache">Cache</SelectItem>
                        <SelectItem value="database">Database</SelectItem>
                        <SelectItem value="api">API</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Search Type
                    </label>
                    <Select value={filterType} onValueChange={setFilterType}>
                      <SelectTrigger>
                        <SelectValue placeholder="All types" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="symbol">Symbol</SelectItem>
                        <SelectItem value="company_name">Company Name</SelectItem>
                        <SelectItem value="fuzzy">Fuzzy</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Time Range (Days)
                    </label>
                    <Select
                      value={days.toString()}
                      onValueChange={(value) => setDays(parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="7">Last 7 days</SelectItem>
                        <SelectItem value="30">Last 30 days</SelectItem>
                        <SelectItem value="60">Last 60 days</SelectItem>
                        <SelectItem value="90">Last 90 days</SelectItem>
                        <SelectItem value="180">Last 6 months</SelectItem>
                        <SelectItem value="365">Last year</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Search History Table */}
            <Card>
              <CardHeader>
                <CardTitle>Search History</CardTitle>
                <CardDescription>
                  Showing {filteredHistory.length} of {searchHistory.length} searches
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                    <span className="ml-2 text-gray-600">Loading search history...</span>
                  </div>
                ) : filteredHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">
                      {searchHistory.length === 0
                        ? 'No search history found. Start searching for stocks to see your history here.'
                        : 'No searches match your filters.'}
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Timestamp</TableHead>
                          <TableHead>Search Query</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Results</TableHead>
                          <TableHead>Execution Time</TableHead>
                          <TableHead>Source</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredHistory.map((item) => (
                          <TableRow key={item.search_id}>
                            <TableCell className="font-mono text-sm">
                              {formatTimestamp(item.timestamp)}
                            </TableCell>
                            <TableCell>
                              <button
                                onClick={() => handleSearchClick(item.search_query)}
                                className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                              >
                                {item.search_query}
                              </button>
                            </TableCell>
                            <TableCell>
                              <Badge variant={getTypeBadgeVariant(item.search_type)}>
                                {item.search_type}
                              </Badge>
                            </TableCell>
                            <TableCell>{item.results_count}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Zap className="h-3 w-3 text-gray-400" />
                                <span className="font-mono text-sm">
                                  {formatExecutionTime(item.execution_time_ms)}
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant={getSourceBadgeVariant(item.source)}>
                                {item.source === 'cache' && (
                                  <Database className="h-3 w-3 mr-1" />
                                )}
                                {item.source === 'api' && (
                                  <TrendingUp className="h-3 w-3 mr-1" />
                                )}
                                {item.source}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleSearchClick(item.search_query)}
                              >
                                <Search className="h-4 w-4 mr-1" />
                                Search Again
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default SearchHistoryPage;
