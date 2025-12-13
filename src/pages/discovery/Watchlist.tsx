import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Edit, X, TrendingUp, TrendingDown, BarChart3, Search, Plus } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
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

interface Stock {
  id?: string;
  symbol: string;
  company_name: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  current_price?: number;
  previous_close?: number;
  market_cap?: number;
  volume?: number;
  price_change?: number;
  price_change_percent?: number;
  currency?: string;
  metadata?: any;
}

interface WatchlistItem {
  id: string;
  stock_symbol: string;
  stock_id?: string;
  notes?: string;
  alert_price?: string;
  created_at?: string;
  stock_data?: Stock;
}

interface StockAnalysis {
  price_targets?: {
    short_term_1m?: number;
    medium_term_3m?: number;
    long_term_12m?: number;
  };
  recommendations?: {
    action?: string;
    confidence?: number;
  };
  fundamental_analysis?: {
    growth_prospects?: string;
  };
}

const WatchlistPage: React.FC = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [stocksData, setStocksData] = useState<Map<string, Stock>>(new Map());
  const [analysesData, setAnalysesData] = useState<Map<string, StockAnalysis>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('forecasts');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async () => {
    setIsLoading(true);
    try {
      const response = await apiCall('/stock/stocks/watchlist', {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.success && response.watchlist) {
        setWatchlist(response.watchlist);
        // Load stock data for each watchlist item
        await loadStocksData(response.watchlist);
      }
    } catch (err) {
      console.error('Error loading watchlist:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStocksData = async (items: WatchlistItem[]) => {
    const stocksMap = new Map<string, Stock>();
    const analysesMap = new Map<string, StockAnalysis>();

    for (const item of items) {
      try {
        // Fetch stock data
        const stockResponse = await apiCall(`/stock/stocks/${item.stock_symbol}`, {
          method: 'GET',
          headers: getAuthHeaders(),
        });

        if (stockResponse.success && stockResponse.stock) {
          stocksMap.set(item.stock_symbol, stockResponse.stock);

          // Fetch analysis if available
          if (stockResponse.stock.id) {
            try {
              const analysisResponse = await apiCall(
                `/stock/stocks/${stockResponse.stock.id}/analysis`,
                {
                  method: 'GET',
                  headers: getAuthHeaders(),
                }
              );

              if (analysisResponse.success && analysisResponse.analysis) {
                analysesMap.set(item.stock_symbol, analysisResponse.analysis);
              }
            } catch (err) {
              // Analysis not available, continue silently
              console.debug(`Analysis not available for ${item.stock_symbol}`);
            }
          }
        }
      } catch (err) {
        console.error(`Error loading stock data for ${item.stock_symbol}:`, err);
      }
    }

    setStocksData(stocksMap);
    setAnalysesData(analysesMap);
  };

  const handleRemoveFromWatchlist = async (symbol: string) => {
    try {
      const response = await apiCall(`/stock/stocks/watchlist/${symbol}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.success) {
        await loadWatchlist();
      }
    } catch (err: any) {
      console.error('Error removing from watchlist:', err);
    }
  };

  const handleStockClick = (stock: Stock) => {
    navigate('/discovery/overview', {
      state: { stock },
    });
  };

  const formatCurrency = (value?: number | null, currency: string = 'USD') => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    const currencyCode = currency === 'INR' ? 'INR' : 'USD';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getPriceChangeColor = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'text-gray-500';
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getPriceChangeIcon = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return null;
    return value >= 0 ? (
      <TrendingUp className="h-4 w-4 text-green-600" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-600" />
    );
  };

  const getAnalystRating = (recommendation?: { action?: string; confidence?: number }) => {
    if (!recommendation || !recommendation.action) return 'N/A';
    const action = recommendation.action.toLowerCase();
    const confidence = recommendation.confidence || 0.5;

    if (action === 'buy' && confidence > 0.7) return 'Strong Buy';
    if (action === 'buy') return 'Buy';
    if (action === 'hold') return 'Hold';
    if (action === 'sell' && confidence > 0.7) return 'Strong Sell';
    if (action === 'sell') return 'Sell';
    return 'N/A';
  };

  const getPriceTarget = (analysis?: StockAnalysis) => {
    if (!analysis?.price_targets) return null;
    return (
      analysis.price_targets.long_term_12m ||
      analysis.price_targets.medium_term_3m ||
      analysis.price_targets.short_term_1m
    );
  };

  const getPriceTargetUpside = (currentPrice?: number, targetPrice?: number) => {
    if (!currentPrice || !targetPrice) return null;
    return ((targetPrice - currentPrice) / currentPrice) * 100;
  };

  const filteredWatchlist = watchlist.filter((item) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const stock = stocksData.get(item.stock_symbol);
    return (
      item.stock_symbol.toLowerCase().includes(query) ||
      stock?.company_name.toLowerCase().includes(query)
    );
  });

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col">
        <Sidebar />
        <main className="flex-1 ml-64 p-6">
          <ContextBreadcrumbs />
          <div className="max-w-7xl mx-auto">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading watchlist...</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        <ContextBreadcrumbs />
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Watchlist</h1>
              <p className="text-gray-600 mt-1">Track your favorite stocks</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => navigate('/discovery/overview')}
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Stocks
              </Button>
            </div>
          </div>

          {/* Watchlist Controls */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="My Watchlist"
                      className="w-64"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <Search className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    Chart View →
                  </Button>
                  <Button variant="outline" size="sm">
                    Options
                  </Button>
                  <Button variant="outline" size="sm">
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Tabs */}
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-8">
                  <TabsTrigger value="general">General</TabsTrigger>
                  <TabsTrigger value="holdings">Holdings</TabsTrigger>
                  <TabsTrigger value="dividends">Dividends</TabsTrigger>
                  <TabsTrigger value="performance">Performance</TabsTrigger>
                  <TabsTrigger value="forecasts">Forecasts</TabsTrigger>
                  <TabsTrigger value="earnings">Earnings</TabsTrigger>
                  <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
                  <TabsTrigger value="add-view">+ Add View</TabsTrigger>
                </TabsList>

                {/* Forecasts Tab Content */}
                <TabsContent value="forecasts" className="mt-6">
                  {filteredWatchlist.length === 0 ? (
                    <div className="text-center py-12">
                      <Star className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-600 mb-2">Your watchlist is empty</p>
                      <Button
                        variant="outline"
                        onClick={() => navigate('/discovery/overview')}
                        className="mt-4"
                      >
                        Add Stocks to Watchlist
                      </Button>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Symbol</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>Chg %</TableHead>
                            <TableHead>Price Target</TableHead>
                            <TableHead>Price Target Upside (%)</TableHead>
                            <TableHead>Analyst Rating</TableHead>
                            <TableHead>Rev Growth Next Year</TableHead>
                            <TableHead>EPS Growth Next Year</TableHead>
                            <TableHead className="w-[100px]">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredWatchlist.map((item) => {
                            const stock = stocksData.get(item.stock_symbol);
                            const analysis = analysesData.get(item.stock_symbol);
                            const priceTarget = getPriceTarget(analysis);
                            const priceTargetUpside = getPriceTargetUpside(
                              stock?.current_price,
                              priceTarget || undefined
                            );

                            return (
                              <TableRow
                                key={item.id}
                                className="cursor-pointer hover:bg-gray-50"
                                onClick={() => stock && handleStockClick(stock)}
                              >
                                <TableCell className="font-medium">
                                  <div>
                                    <div className="font-semibold">
                                      {stock?.exchange ? `${stock.exchange}:` : ''}
                                      {item.stock_symbol}
                                    </div>
                                    <div className="text-sm text-gray-500">
                                      {stock?.company_name || 'N/A'}
                                    </div>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  {formatCurrency(
                                    stock?.current_price,
                                    stock?.currency || 'USD'
                                  )}
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-1">
                                    {getPriceChangeIcon(stock?.price_change_percent)}
                                    <span
                                      className={getPriceChangeColor(stock?.price_change_percent)}
                                    >
                                      {formatPercent(stock?.price_change_percent)}
                                    </span>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  {priceTarget
                                    ? formatCurrency(priceTarget, stock?.currency || 'USD')
                                    : 'N/A'}
                                </TableCell>
                                <TableCell>
                                  {priceTargetUpside !== null ? (
                                    <span
                                      className={
                                        priceTargetUpside >= 0
                                          ? 'text-green-600'
                                          : 'text-red-600'
                                      }
                                    >
                                      {formatPercent(priceTargetUpside)}
                                    </span>
                                  ) : (
                                    'N/A'
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Badge
                                    variant={
                                      analysis?.recommendations?.action === 'buy'
                                        ? 'default'
                                        : analysis?.recommendations?.action === 'sell'
                                          ? 'destructive'
                                          : 'secondary'
                                    }
                                  >
                                    {getAnalystRating(analysis?.recommendations)}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  {analysis?.fundamental_analysis?.growth_prospects || 'N/A'}
                                </TableCell>
                                <TableCell>N/A</TableCell>
                                <TableCell>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleRemoveFromWatchlist(item.stock_symbol);
                                    }}
                                  >
                                    <X className="h-4 w-4 text-red-500" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </TabsContent>

                {/* Other Tabs - Placeholder */}
                <TabsContent value="general" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    General view coming soon
                  </div>
                </TabsContent>
                <TabsContent value="holdings" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    Holdings view coming soon
                  </div>
                </TabsContent>
                <TabsContent value="dividends" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    Dividends view coming soon
                  </div>
                </TabsContent>
                <TabsContent value="performance" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    Performance view coming soon
                  </div>
                </TabsContent>
                <TabsContent value="earnings" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    Earnings view coming soon
                  </div>
                </TabsContent>
                <TabsContent value="fundamentals" className="mt-6">
                  <div className="text-center py-12 text-gray-500">
                    Fundamentals view coming soon
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default WatchlistPage;

