import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '../../config/api';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Loader2, Search, TrendingUp, TrendingDown, DollarSign, BarChart3, AlertTriangle, CheckCircle, Star, StarOff, Plus, X, GitCompare } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { PriceChart } from '../../components/stock/PriceChart';
import { ModelSelector, ModelType } from '../../components/stock/ModelSelector';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

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
  metadata?: {
    currency?: string;
    country?: string;
    pe_ratio?: number;
    dividend_yield?: number;
    '52_week_high'?: number;
    '52_week_low'?: number;
    beta?: number;
    rsi?: number;
    earnings_date?: string;
    ex_dividend_date?: string;
    revenue?: number;
    net_income?: number;
    shares_outstanding?: number;
    eps?: number;
    forward_pe?: number;
    average_volume?: number;
    day_high?: number;
    day_low?: number;
  };
}

interface StockAnalysis {
  id?: string;
  stock_id?: string;
  summary: string;
  key_insights: string[];
  technical_analysis?: {
    trend?: string;
    support_levels?: number[];
    resistance_levels?: number[];
    indicators?: Record<string, any>;
  };
  fundamental_analysis?: {
    valuation?: string;
    financial_health?: string;
    growth_prospects?: string;
    competitive_position?: string;
  };
  risk_assessment?: {
    overall_risk?: string;
    key_risks?: string[];
    volatility?: string;
  };
  recommendations?: {
    action?: string;
    confidence?: number;
    reasoning?: string;
  };
  price_targets?: {
    short_term_1m?: number;
    medium_term_3m?: number;
    long_term_12m?: number;
    target_basis?: string;
  };
  confidence_score?: number;
}

interface HistoricalPrice {
  date: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface WatchlistItem {
  id: string;
  stock_symbol: string;
  stock_data?: Stock;
  notes?: string;
  alert_price?: string;
}

const DiscoveryDashboard: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New state for enhanced features
  const [historicalPrices, setHistoricalPrices] = useState<HistoricalPrice[]>([]);
  const [pricePeriod, setPricePeriod] = useState('1mo');
  const [isLoadingPrices, setIsLoadingPrices] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [comparisonStocks, setComparisonStocks] = useState<Stock[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Separate analysis state for each tab
  const [financialsAnalysis, setFinancialsAnalysis] = useState<StockAnalysis | null>(null);
  const [statisticsAnalysis, setStatisticsAnalysis] = useState<StockAnalysis | null>(null);
  const [historyAnalysis, setHistoryAnalysis] = useState<StockAnalysis | null>(null);
  const [newsAnalysis, setNewsAnalysis] = useState<StockAnalysis | null>(null);
  const [stockNews, setStockNews] = useState<any[]>([]);
  const [isLoadingNews, setIsLoadingNews] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelType>('auto');

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<Stock[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch suggestions for autocomplete
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoadingSuggestions(true);
    try {
      const response = await apiCall(
        `/stock/stocks/search?q=${encodeURIComponent(query)}&limit=5`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.stocks) {
        setSuggestions(response.stocks);
        setShowSuggestions(true);
        setSelectedSuggestionIndex(-1);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err: any) {
      console.error('Error fetching suggestions:', err);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [getAuthHeaders]);

  // Handle input change with debounced suggestions
  const handleInputChange = useCallback((value: string) => {
    setSearchQuery(value);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounce suggestion fetching
    if (value.trim().length >= 2) {
      debounceTimerRef.current = setTimeout(() => {
        fetchSuggestions(value);
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [fetchSuggestions]);

  // Handle keyboard navigation in suggestions
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < suggestions.length) {
          const selectedStock = suggestions[selectedSuggestionIndex];
          setSearchQuery(selectedStock.symbol);
          setShowSuggestions(false);
          setSelectedSuggestionIndex(-1);
          setSuggestions([]);
          handleAnalyzeStock(selectedStock);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // Handle suggestion selection
  const handleSelectSuggestion = (stock: Stock) => {
    setSearchQuery(stock.symbol);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setSuggestions([]);
    handleAnalyzeStock(stock);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setError(null);
    setSearchResults([]);
    setSelectedStock(null);
    setAnalysis(null);

    try {
      const response = await apiCall(
        `/stock/stocks/search?q=${encodeURIComponent(searchQuery)}&limit=10`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.stocks) {
        setSearchResults(response.stocks);
      } else {
        setError('No stocks found');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to search stocks');
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  // Load watchlist on mount
  useEffect(() => {
    loadWatchlist();
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchInputRef.current && !searchInputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    if (showSuggestions) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showSuggestions]);

  // Reset active tab when stock changes
  useEffect(() => {
    if (selectedStock) {
      setActiveTab('overview');
    }
  }, [selectedStock]);

  // Check if stock is in watchlist when selected stock changes
  useEffect(() => {
    if (selectedStock) {
      const inWatchlist = watchlist.some(
        (item) => item.stock_symbol === selectedStock.symbol
      );
      setIsInWatchlist(inWatchlist);
      loadHistoricalPrices(selectedStock.symbol);
      loadStockNews(selectedStock.symbol);
    }
  }, [selectedStock, watchlist]);

  // Load news when news tab is clicked
  useEffect(() => {
    if (activeTab === 'news' && selectedStock && stockNews.length === 0 && !isLoadingNews) {
      loadStockNews(selectedStock.symbol);
    }
  }, [activeTab, selectedStock]);

  // Reset analysis states when stock changes
  useEffect(() => {
    if (selectedStock) {
      setFinancialsAnalysis(null);
      setStatisticsAnalysis(null);
      setHistoryAnalysis(null);
      setNewsAnalysis(null);
      setStockNews([]);
    }
  }, [selectedStock]);

  const loadWatchlist = async () => {
    try {
      const response = await apiCall('/stock/stocks/watchlist', {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.success && response.watchlist) {
        setWatchlist(response.watchlist);
      }
    } catch (err) {
      console.error('Error loading watchlist:', err);
    }
  };

  const loadHistoricalPrices = async (symbol: string, period: string = pricePeriod) => {
    setIsLoadingPrices(true);
    try {
      const response = await apiCall(
        `/stock/stocks/${symbol}/historical?period=${period}&interval=1d`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.prices) {
        setHistoricalPrices(response.prices);
      }
    } catch (err) {
      console.error('Error loading historical prices:', err);
    } finally {
      setIsLoadingPrices(false);
    }
  };

  const handleAddToWatchlist = async (stock: Stock) => {
    try {
      const response = await apiCall(
        `/stock/stocks/watchlist?symbol=${stock.symbol}`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
        }
      );

      if (response.success) {
        setIsInWatchlist(true);
        await loadWatchlist();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add to watchlist');
    }
  };

  const handleRemoveFromWatchlist = async (symbol: string) => {
    try {
      const response = await apiCall(
        `/stock/stocks/watchlist/${symbol}`,
        {
          method: 'DELETE',
          headers: getAuthHeaders(),
        }
      );

      if (response.success) {
        setIsInWatchlist(false);
        await loadWatchlist();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to remove from watchlist');
    }
  };

  const handleAddToComparison = (stock: Stock) => {
    if (comparisonStocks.length >= 5) {
      setError('Maximum 5 stocks allowed for comparison');
      return;
    }
    if (!comparisonStocks.find((s) => s.symbol === stock.symbol)) {
      setComparisonStocks([...comparisonStocks, stock]);
    }
  };

  const handleCompareStocks = async () => {
    if (comparisonStocks.length < 2) {
      setError('Select at least 2 stocks to compare');
      return;
    }

    try {
      const symbols = comparisonStocks.map((s) => s.symbol).join(',');
      const response = await apiCall(
        `/stock/stocks/compare?symbols=${symbols}`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success) {
        setShowComparison(true);
        setComparisonStocks(response.stocks || comparisonStocks);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to compare stocks');
    }
  };

  const handleAnalyzeStock = async (stock: Stock) => {
    console.log('handleAnalyzeStock called with:', stock);
    setSelectedStock(stock);
    setAnalysis(null);
    setError(null);
    setActiveTab('overview'); // Always open to overview tab
    setIsAnalyzing(false); // Don't auto-analyze

    try {
      // Fetch full stock details from API to ensure we have all data
      const response = await apiCall(
        `/stock/stocks/${encodeURIComponent(stock.symbol)}`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.stock) {
        console.log('Fetched full stock details:', response.stock);
        setSelectedStock(response.stock);
      } else {
        console.warn('API response did not contain stock data, using provided stock');
      }
    } catch (err: any) {
      console.error('Error fetching stock details:', err);
      // Continue with the stock data we have if API call fails
    }

    // Load historical prices for the chart
    try {
      await loadHistoricalPrices(stock.symbol, pricePeriod);
    } catch (err) {
      console.error('Error loading historical prices:', err);
    }

    // Check if stock is in watchlist
    const inWatchlist = watchlist.some(
      (item) => item.stock_symbol.toUpperCase() === stock.symbol.toUpperCase()
    );
    setIsInWatchlist(inWatchlist);
  };

  const handleAnalyzeStockWithAI = async () => {
    if (!selectedStock) return;

    setError(null);
    setIsAnalyzing(true);

    try {
      console.log('🚀 Starting comprehensive analysis for', selectedStock.symbol, 'with model:', selectedModel);

      // Prepare request body with model parameter (only include if not 'auto')
      const requestBody: { symbol: string; model?: string } = {
        symbol: selectedStock.symbol,
      };
      if (selectedModel !== 'auto') {
        requestBody.model = selectedModel;
      }

      // Call the analyze/all endpoint that runs all agents
      const response = await apiCall(
        '/stock/stocks/analyze/all',
        {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        }
      );

      console.log('🚀 Analysis response received:', response);
      console.log('🚀 Response keys:', Object.keys(response));
      console.log('🚀 Financials:', response.financials ? 'Present' : 'Missing');
      console.log('🚀 Statistics:', response.statistics ? 'Present' : 'Missing');
      console.log('🚀 History:', response.history ? 'Present' : 'Missing');
      console.log('🚀 News:', response.news ? 'Present' : 'Missing');

      if (response && response.success !== false) {
        // Set overview analysis (use financials as overview if available)
        if (response.financials) {
          console.log('✅ Setting overview analysis from financials');
          setAnalysis(response.financials);
        }

        // Set individual tab analyses
        if (response.financials) {
          console.log('✅ Setting financials analysis');
          setFinancialsAnalysis(response.financials);
        }

        if (response.statistics) {
          console.log('✅ Setting statistics analysis');
          setStatisticsAnalysis(response.statistics);
        }

        if (response.history) {
          console.log('✅ Setting history analysis');
          setHistoryAnalysis(response.history);
        }

        if (response.news) {
          console.log('✅ Setting news analysis');
          setNewsAnalysis(response.news);
        }

        if (response.stock) {
          console.log('✅ Updating stock data');
          setSelectedStock(response.stock);
        }

        if (response.errors && response.errors.length > 0) {
          console.warn('⚠️ Some agents had errors:', response.errors);
          setError(`Some analyses failed: ${response.errors.join(', ')}`);
        }

        console.log('✅ All analysis states updated');
      } else {
        console.error('❌ Analysis failed:', response);
        setError('Failed to generate analysis');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze stock');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadStockNews = async (symbol: string) => {
    setIsLoadingNews(true);
    try {
      const response = await apiCall(
        `/stock/stocks/${symbol}/news?limit=20`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success) {
        setStockNews(response.news || []);
      } else {
        console.warn('News API returned unsuccessful response:', response);
        setStockNews([]);
      }
    } catch (err) {
      console.error('Error loading stock news:', err);
      setStockNews([]);
    } finally {
      setIsLoadingNews(false);
    }
  };

  const handlePeriodChange = (period: string) => {
    setPricePeriod(period);
    if (selectedStock) {
      loadHistoricalPrices(selectedStock.symbol, period);
    }
  };

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return value.toLocaleString();
  };

  const getPriceChangeColor = (change?: number | null) => {
    if (change === undefined || change === null) return 'text-gray-500';
    return change >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getRecommendationColor = (action?: string) => {
    if (!action) return 'default';
    const actionLower = action.toLowerCase();
    if (actionLower === 'buy') return 'default';
    if (actionLower === 'hold') return 'secondary';
    if (actionLower === 'sell') return 'destructive';
    return 'default';
  };

  return (
    <div className="flex-1 flex flex-col">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        <ContextBreadcrumbs />
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Show search interface when no stock is selected */}
          {!selectedStock && (
            <>
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Stock Analysis Overview</h1>
                  <p className="text-muted-foreground">
                    Search for stocks and view detailed analysis
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowComparison(!showComparison)}
                  >
                    <GitCompare className="w-4 h-4 mr-2" />
                    {showComparison ? 'Hide' : 'Show'} Comparison
                  </Button>
                </div>
              </div>

              {/* Watchlist Sidebar */}
              {watchlist.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                      Watchlist
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {watchlist.map((item) => (
                        <div
                          key={item.id}
                          className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                          onClick={() => item.stock_data && handleAnalyzeStock(item.stock_data)}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-bold">{item.stock_symbol}</div>
                              {item.stock_data?.company_name && (
                                <div className="text-sm text-muted-foreground">
                                  {item.stock_data.company_name}
                                </div>
                              )}
                              {item.stock_data?.current_price && (
                                <div className="font-semibold mt-1">
                                  {formatCurrency(item.stock_data.current_price)}
                                </div>
                              )}
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemoveFromWatchlist(item.stock_symbol);
                              }}
                            >
                              <StarOff className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Search Section */}
              <Card>
                <CardHeader>
                  <CardTitle>Search Stocks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Model Selector */}
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">AI Model:</span>
                      <ModelSelector
                        value={selectedModel}
                        onChange={setSelectedModel}
                      />
                    </div>

                    {/* Search Input */}
                    <div className="flex gap-2 relative">
                      <div className="flex-1 relative" ref={searchInputRef}>
                        <Input
                          placeholder="Enter stock symbol or company name (e.g., HCLTECH, RELIANCE, AAPL, Apple)"
                          value={searchQuery}
                          onChange={(e) => handleInputChange(e.target.value)}
                          onKeyDown={handleKeyDown}
                          onFocus={() => {
                            if (suggestions.length > 0) {
                              setShowSuggestions(true);
                            }
                          }}
                          className="w-full"
                        />
                        {showSuggestions && suggestions.length > 0 && (
                          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
                            {isLoadingSuggestions ? (
                              <div className="p-4 text-center">
                                <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                              </div>
                            ) : (
                              <ul className="py-1">
                                {suggestions.map((stock, index) => (
                                  <li
                                    key={stock.symbol}
                                    className={`px-4 py-2 cursor-pointer hover:bg-gray-100 ${
                                      index === selectedSuggestionIndex ? 'bg-gray-100' : ''
                                    }`}
                                    onClick={() => handleSelectSuggestion(stock)}
                                    onMouseEnter={() => setSelectedSuggestionIndex(index)}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div>
                                        <div className="font-semibold text-sm">{stock.symbol}</div>
                                        <div className="text-xs text-gray-500">{stock.company_name}</div>
                                      </div>
                                      {stock.exchange && (
                                        <Badge variant="outline" className="text-xs">
                                          {stock.exchange}
                                        </Badge>
                                      )}
                                    </div>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                      </div>
                      <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
                        {isSearching ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Searching...
                          </>
                        ) : (
                          <>
                            <Search className="w-4 h-4 mr-2" />
                            Search
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Error Display */}
              {error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Search Results */}
              {searchResults.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Search Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {searchResults.map((stock) => (
                        <div
                          key={stock.symbol}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                          onClick={() => handleAnalyzeStock(stock)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-lg">{stock.symbol}</span>
                              <span className="text-muted-foreground">{stock.company_name}</span>
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                              {stock.exchange && <span>{stock.exchange}</span>}
                              {stock.sector && <span>{stock.sector}</span>}
                              {stock.current_price && (
                                <span className="font-semibold text-gray-900">
                                  {formatCurrency(stock.current_price)}
                                </span>
                              )}
                              {stock.price_change_percent !== undefined && stock.price_change_percent !== null && (
                                <span className={getPriceChangeColor(stock.price_change_percent)}>
                                  {stock.price_change_percent >= 0 ? '+' : ''}
                                  {stock.price_change_percent.toFixed(2)}%
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAddToComparison(stock);
                              }}
                            >
                              <Plus className="w-4 h-4 mr-1" />
                              Compare
                            </Button>
                            <Button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAnalyzeStock(stock);
                              }}
                            >
                              View
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* Selected Stock Overview Page */}
          {selectedStock && (
            <div className="space-y-6">
              {/* Compact Search Bar at top when stock is selected */}
              <div className="flex gap-2 items-center">
                <div className="flex-1 relative" ref={searchInputRef}>
                  <Input
                    placeholder="Search for another stock..."
                    value={searchQuery}
                    onChange={(e) => handleInputChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => {
                      if (suggestions.length > 0) {
                        setShowSuggestions(true);
                      }
                    }}
                    className="w-full"
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
                      {isLoadingSuggestions ? (
                        <div className="p-4 text-center">
                          <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                        </div>
                      ) : (
                        <ul className="py-1">
                          {suggestions.map((stock, index) => (
                            <li
                              key={stock.symbol}
                              className={`px-4 py-2 cursor-pointer hover:bg-gray-100 ${
                                index === selectedSuggestionIndex ? 'bg-gray-100' : ''
                              }`}
                              onClick={() => handleSelectSuggestion(stock)}
                              onMouseEnter={() => setSelectedSuggestionIndex(index)}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="font-semibold text-sm">{stock.symbol}</div>
                                  <div className="text-xs text-gray-500">{stock.company_name}</div>
                                </div>
                                {stock.exchange && (
                                  <Badge variant="outline" className="text-xs">
                                    {stock.exchange}
                                  </Badge>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
                <ModelSelector
                  value={selectedModel}
                  onChange={setSelectedModel}
                />
                <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()} variant="outline" size="sm">
                  {isSearching ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedStock(null);
                    setSearchResults([]);
                    setAnalysis(null);
                    setSearchQuery('');
                    setActiveTab('overview');
                  }}
                >
                  <X className="w-4 h-4 mr-2" />
                  Back to Search
                </Button>
              </div>

              {/* Professional Stock Header */}
              <Card>
                <CardContent className="pt-6">
                  {/* Company Header */}
                  <div className="mb-4">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {selectedStock.company_name} ({selectedStock.exchange || 'N/A'}:{selectedStock.symbol})
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedStock.metadata?.country || 'United States'} {selectedStock.metadata?.country === 'India' ? 'Delayed Price' : ''} - Currency is {selectedStock.currency || selectedStock.metadata?.currency || 'USD'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date().toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        timeZoneName: selectedStock.metadata?.country === 'India' ? 'short' : undefined
                      })}
                      {selectedStock.metadata?.country === 'India' ? ' IST' : ''}
                    </p>
                  </div>

                  {/* Price and Actions */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-baseline gap-4">
                      {selectedStock.current_price && (
                        <div>
                          <div className="text-4xl font-bold text-gray-900">
                            {formatCurrency(selectedStock.current_price)}
                          </div>
                          {selectedStock.price_change !== undefined && selectedStock.price_change !== null && (
                            <div className={`flex items-center gap-2 mt-1 ${getPriceChangeColor(selectedStock.price_change_percent || 0)}`}>
                              <span className="text-lg font-semibold">
                                {selectedStock.price_change >= 0 ? '+' : ''}
                                {selectedStock.price_change.toFixed(2)} ({selectedStock.price_change_percent !== undefined && selectedStock.price_change_percent !== null ? `${selectedStock.price_change_percent >= 0 ? '+' : ''}${selectedStock.price_change_percent.toFixed(2)}%` : '0.00%'})
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {isInWatchlist ? (
                        <Button
                          variant="default"
                          onClick={() => handleRemoveFromWatchlist(selectedStock.symbol)}
                        >
                          <StarOff className="w-4 h-4 mr-2" />
                          Watchlist
                        </Button>
                      ) : (
                        <Button
                          variant="default"
                          onClick={() => handleAddToWatchlist(selectedStock)}
                        >
                          <Star className="w-4 h-4 mr-2" />
                          Watchlist
                        </Button>
                      )}
                      <Button
                        variant="default"
                        onClick={() => handleAddToComparison(selectedStock)}
                      >
                        <GitCompare className="w-4 h-4 mr-2" />
                        Compare
                      </Button>
                    </div>
                  </div>

                  {/* Sub-navigation Tabs */}
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <div className="w-full overflow-x-auto mb-4">
                      <TabsList className="inline-flex h-10 items-center justify-start rounded-md bg-muted p-1 text-muted-foreground">
                        <TabsTrigger value="overview" className="whitespace-nowrap">Overview</TabsTrigger>
                        <TabsTrigger value="financials" className="whitespace-nowrap">Financials</TabsTrigger>
                        <TabsTrigger value="statistics" className="whitespace-nowrap">Statistics</TabsTrigger>
                        <TabsTrigger value="dividends" className="whitespace-nowrap">Dividends</TabsTrigger>
                        <TabsTrigger value="history" className="whitespace-nowrap">History</TabsTrigger>
                        <TabsTrigger value="news" className="whitespace-nowrap">News</TabsTrigger>
                        <TabsTrigger value="profile" className="whitespace-nowrap">Profile</TabsTrigger>
                        <TabsTrigger value="chart" className="whitespace-nowrap">Chart</TabsTrigger>
                      </TabsList>
                    </div>

                    {/* Overview Tab */}
                    <TabsContent value="overview" className="mt-6 space-y-6">
                      {/* AI Analysis Button */}
                      {!analysis && (
                        <div className="flex justify-between items-center">
                          <ModelSelector
                            value={selectedModel}
                            onChange={setSelectedModel}
                          />
                          <Button
                            onClick={handleAnalyzeStockWithAI}
                            disabled={isAnalyzing}
                            size="lg"
                          >
                            {isAnalyzing ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <BarChart3 className="w-4 h-4 mr-2" />
                                Generate AI Analysis
                              </>
                            )}
                          </Button>
                        </div>
                      )}

                      {/* Loading AI Analysis */}
                      {isAnalyzing && (
                        <Card>
                          <CardContent className="py-8 text-center">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                            <p className="text-muted-foreground">Generating AI analysis...</p>
                          </CardContent>
                        </Card>
                      )}

                      {/* AI Analysis Results */}
                      {analysis && (
                        <Card>
                          <CardHeader>
                            <CardTitle>AI-Powered Analysis</CardTitle>
                            {analysis.confidence_score !== undefined && analysis.confidence_score !== null && !isNaN(analysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(analysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent>
                            <Tabs defaultValue="summary" className="w-full">
                              <TabsList>
                                <TabsTrigger value="summary">Summary</TabsTrigger>
                                <TabsTrigger value="technical">Technical</TabsTrigger>
                                <TabsTrigger value="fundamental">Fundamental</TabsTrigger>
                                <TabsTrigger value="risks">Risks</TabsTrigger>
                                <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                              </TabsList>

                              <TabsContent value="summary" className="space-y-4 mt-4">
                                {analysis.summary && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Executive Summary</h3>
                                    <p className="text-muted-foreground">{analysis.summary}</p>
                                  </div>
                                )}
                                {analysis.key_insights && analysis.key_insights.length > 0 && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Key Insights</h3>
                                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                      {analysis.key_insights.map((insight, idx) => (
                                        <li key={idx}>{insight}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </TabsContent>

                              <TabsContent value="technical" className="space-y-4 mt-4">
                                {analysis.technical_analysis && (
                                  <div className="space-y-4">
                                    {analysis.technical_analysis.trend && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Trend</h3>
                                        <Badge variant="outline">{analysis.technical_analysis.trend}</Badge>
                                      </div>
                                    )}
                                    {analysis.technical_analysis.support_levels && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Support Levels</h3>
                                        <div className="flex gap-2">
                                          {analysis.technical_analysis.support_levels.map((level, idx) => (
                                            <Badge key={idx} variant="secondary">
                                              {formatCurrency(level)}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    {analysis.technical_analysis.resistance_levels && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Resistance Levels</h3>
                                        <div className="flex gap-2">
                                          {analysis.technical_analysis.resistance_levels.map((level, idx) => (
                                            <Badge key={idx} variant="secondary">
                                              {formatCurrency(level)}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </TabsContent>

                              <TabsContent value="fundamental" className="space-y-4 mt-4">
                                {analysis.fundamental_analysis && (
                                  <div className="space-y-4">
                                    {Object.entries(analysis.fundamental_analysis).map(([key, value]) => (
                                      <div key={key}>
                                        <h3 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                                        {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                          <div className="space-y-2">
                                            {Object.entries(value as any).map(([subKey, subValue]) => {
                                              if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
                                                return (
                                                  <div key={subKey} className="space-y-1">
                                                    <span className="text-sm font-medium text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                    <div className="ml-4 space-y-1">
                                                      {Object.entries(subValue as any).map(([nestedKey, nestedValue]) => (
                                                        <div key={nestedKey} className="flex items-center gap-2">
                                                          <span className="text-xs text-muted-foreground capitalize">{nestedKey.replace(/_/g, ' ')}:</span>
                                                          <Badge variant="outline" className="text-xs">
                                                            {Array.isArray(nestedValue)
                                                              ? nestedValue.join(', ')
                                                              : typeof nestedValue === 'object' && nestedValue !== null
                                                              ? JSON.stringify(nestedValue)
                                                              : String(nestedValue)}
                                                          </Badge>
                                                        </div>
                                                      ))}
                                                    </div>
                                                  </div>
                                                );
                                              }
                                              if (Array.isArray(subValue)) {
                                                return (
                                                  <div key={subKey} className="flex items-center gap-2">
                                                    <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                    <div className="flex flex-wrap gap-2">
                                                      {subValue.map((item: any, idx: number) => (
                                                        <Badge key={idx} variant="outline">{String(item)}</Badge>
                                                      ))}
                                                    </div>
                                                  </div>
                                                );
                                              }
                                              return (
                                                <div key={subKey} className="flex items-center gap-2">
                                                  <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                  <Badge variant="outline">{String(subValue)}</Badge>
                                                </div>
                                              );
                                            })}
                                          </div>
                                        ) : Array.isArray(value) ? (
                                          <div className="flex flex-wrap gap-2">
                                            {value.map((item: any, idx: number) => (
                                              <Badge key={idx} variant="outline">{String(item)}</Badge>
                                            ))}
                                          </div>
                                        ) : (
                                          <Badge variant="outline">{String(value)}</Badge>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </TabsContent>

                              <TabsContent value="risks" className="space-y-4 mt-4">
                                {analysis.risk_assessment && (
                                  <div className="space-y-4">
                                    {analysis.risk_assessment.overall_risk && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Overall Risk</h3>
                                        <Badge variant="outline">{analysis.risk_assessment.overall_risk}</Badge>
                                      </div>
                                    )}
                                    {analysis.risk_assessment.key_risks && analysis.risk_assessment.key_risks.length > 0 && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Key Risks</h3>
                                        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                          {analysis.risk_assessment.key_risks.map((risk, idx) => (
                                            <li key={idx}>{risk}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </TabsContent>

                              <TabsContent value="recommendations" className="space-y-4 mt-4">
                                {analysis.recommendations && (
                                  <div className="space-y-4">
                                    {analysis.recommendations.action && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Recommendation</h3>
                                        <Badge variant={getRecommendationColor(analysis.recommendations.action)}>
                                          {analysis.recommendations.action.toUpperCase()}
                                        </Badge>
                                      </div>
                                    )}
                                    {analysis.recommendations.reasoning && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Reasoning</h3>
                                        <p className="text-muted-foreground">{analysis.recommendations.reasoning}</p>
                                      </div>
                                    )}
                                    {analysis.price_targets && (
                                      <div>
                                        <h3 className="font-semibold mb-2">Price Targets</h3>
                                        <div className="grid grid-cols-3 gap-4">
                                          {analysis.price_targets.short_term_1m && (
                                            <div>
                                              <div className="text-sm text-muted-foreground">1 Month</div>
                                              <div className="font-semibold">
                                                {formatCurrency(analysis.price_targets.short_term_1m)}
                                              </div>
                                            </div>
                                          )}
                                          {analysis.price_targets.medium_term_3m && (
                                            <div>
                                              <div className="text-sm text-muted-foreground">3 Months</div>
                                              <div className="font-semibold">
                                                {formatCurrency(analysis.price_targets.medium_term_3m)}
                                              </div>
                                            </div>
                                          )}
                                          {analysis.price_targets.long_term_12m && (
                                            <div>
                                              <div className="text-sm text-muted-foreground">12 Months</div>
                                              <div className="font-semibold">
                                                {formatCurrency(analysis.price_targets.long_term_12m)}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                        {analysis.price_targets.target_basis && (
                                          <p className="text-sm text-muted-foreground mt-2">
                                            {analysis.price_targets.target_basis}
                                          </p>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </TabsContent>
                            </Tabs>
                          </CardContent>
                        </Card>
                      )}

                      {/* Historical Price Chart */}
                      <Card>
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle>Price History</CardTitle>
                            <div className="flex gap-2 flex-wrap">
                              {['1d', '5d', '1mo', 'ytd', '1y', '5y', 'max'].map((period) => (
                                <Button
                                  key={period}
                                  variant={pricePeriod === period ? 'default' : 'outline'}
                                  size="sm"
                                  onClick={() => handlePeriodChange(period)}
                                >
                                  {period === '1d' ? '1 Day' :
                                   period === '5d' ? '5 Days' :
                                   period === '1mo' ? '1 Month' :
                                   period === 'ytd' ? 'YTD' :
                                   period === '1y' ? '1 Year' :
                                   period === '5y' ? '5 Years' : 'Max'}
                                </Button>
                              ))}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          {isLoadingPrices ? (
                            <div className="flex items-center justify-center h-96">
                              <Loader2 className="w-8 h-8 animate-spin" />
                            </div>
                          ) : (
                            <div className="h-96">
                              <PriceChart
                                data={historicalPrices}
                                symbol={selectedStock.symbol}
                                period={pricePeriod}
                              />
                            </div>
                          )}
                        </CardContent>
                      </Card>

                      {/* Stock Metrics */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Left Column */}
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            {selectedStock.market_cap && (
                              <div>
                                <div className="text-sm text-muted-foreground">Market Cap</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.market_cap)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.revenue && (
                              <div>
                                <div className="text-sm text-muted-foreground">Revenue (ttm)</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.metadata.revenue)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.net_income && (
                              <div>
                                <div className="text-sm text-muted-foreground">Net Income (ttm)</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.metadata.net_income)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.shares_outstanding && (
                              <div>
                                <div className="text-sm text-muted-foreground">Shares Out</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.metadata.shares_outstanding)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.eps && (
                              <div>
                                <div className="text-sm text-muted-foreground">EPS (ttm)</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.eps.toFixed(2)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.pe_ratio && (
                              <div>
                                <div className="text-sm text-muted-foreground">PE Ratio</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.pe_ratio.toFixed(2)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.forward_pe && (
                              <div>
                                <div className="text-sm text-muted-foreground">Forward PE</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.forward_pe.toFixed(2)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.dividend_yield && (
                              <div>
                                <div className="text-sm text-muted-foreground">Dividend</div>
                                <div className="font-semibold text-lg">
                                  {(selectedStock.current_price && selectedStock.metadata.dividend_yield)
                                    ? `${(selectedStock.current_price * selectedStock.metadata.dividend_yield).toFixed(2)} (${(selectedStock.metadata.dividend_yield * 100).toFixed(2)}%)`
                                    : 'N/A'}
                                </div>
                              </div>
                            )}
                            {selectedStock.metadata?.ex_dividend_date && (
                              <div>
                                <div className="text-sm text-muted-foreground">Ex-Dividend Date</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.ex_dividend_date}</div>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Right Column */}
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            {selectedStock.volume && (
                              <div>
                                <div className="text-sm text-muted-foreground">Volume</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.volume)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.average_volume && (
                              <div>
                                <div className="text-sm text-muted-foreground">Average Volume</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.metadata.average_volume)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.day_high && (
                              <div>
                                <div className="text-sm text-muted-foreground">Open</div>
                                <div className="font-semibold text-lg">{formatCurrency(selectedStock.metadata.day_high)}</div>
                              </div>
                            )}
                            {selectedStock.previous_close && (
                              <div>
                                <div className="text-sm text-muted-foreground">Previous Close</div>
                                <div className="font-semibold text-lg">{formatCurrency(selectedStock.previous_close)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.day_high && selectedStock.metadata?.day_low && (
                              <div>
                                <div className="text-sm text-muted-foreground">Day's Range</div>
                                <div className="font-semibold text-lg">
                                  {formatCurrency(selectedStock.metadata.day_low)} - {formatCurrency(selectedStock.metadata.day_high)}
                                </div>
                              </div>
                            )}
                            {selectedStock.metadata?.['52_week_high'] && selectedStock.metadata?.['52_week_low'] && (
                              <div>
                                <div className="text-sm text-muted-foreground">52-Week Range</div>
                                <div className="font-semibold text-lg">
                                  {formatCurrency(selectedStock.metadata['52_week_low'])} - {formatCurrency(selectedStock.metadata['52_week_high'])}
                                </div>
                              </div>
                            )}
                            {selectedStock.metadata?.beta && (
                              <div>
                                <div className="text-sm text-muted-foreground">Beta</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.beta.toFixed(2)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.rsi && (
                              <div>
                                <div className="text-sm text-muted-foreground">RSI</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.rsi.toFixed(2)}</div>
                              </div>
                            )}
                            {selectedStock.metadata?.earnings_date && (
                              <div>
                                <div className="text-sm text-muted-foreground">Earnings Date</div>
                                <div className="font-semibold text-lg">{selectedStock.metadata.earnings_date}</div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    {/* Chart Tab */}
                    <TabsContent value="chart" className="mt-6">
                      <div className="space-y-4">
                        {/* Chart Timeframe Buttons */}
                        <div className="flex gap-2 flex-wrap">
                          {['1d', '5d', '1mo', 'ytd', '1y', '5y', 'max'].map((period) => (
                            <Button
                              key={period}
                              variant={pricePeriod === period ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => handlePeriodChange(period)}
                            >
                              {period === '1d' ? '1 Day' :
                               period === '5d' ? '5 Days' :
                               period === '1mo' ? '1 Month' :
                               period === 'ytd' ? 'YTD' :
                               period === '1y' ? '1 Year' :
                               period === '5y' ? '5 Years' : 'Max'}
                            </Button>
                          ))}
                        </div>

                        {/* Chart */}
                        {isLoadingPrices ? (
                          <div className="flex items-center justify-center h-96">
                            <Loader2 className="w-8 h-8 animate-spin" />
                          </div>
                        ) : (
                          <div className="h-96">
                            <PriceChart
                              data={historicalPrices}
                              symbol={selectedStock.symbol}
                              period={pricePeriod}
                            />
                          </div>
                        )}
                      </div>
                    </TabsContent>

                    {/* Financials Tab */}
                    <TabsContent value="financials" className="mt-6 space-y-6">
                      {selectedStock && (
                        <Card>
                          <CardHeader>
                            <CardTitle>Financial Metrics</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {/* Left Column */}
                              <div className="space-y-4">
                                <h3 className="font-semibold text-lg mb-4">Revenue & Income</h3>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <div className="text-sm text-muted-foreground">Market Cap</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.market_cap ? formatNumber(selectedStock.market_cap) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Revenue (ttm)</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.revenue ? formatNumber(selectedStock.metadata.revenue) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Net Income (ttm)</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.net_income ? formatNumber(selectedStock.metadata.net_income) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Shares Outstanding</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.shares_outstanding ? formatNumber(selectedStock.metadata.shares_outstanding) : 'N/A'}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Right Column */}
                              <div className="space-y-4">
                                <h3 className="font-semibold text-lg mb-4">Valuation Metrics</h3>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <div className="text-sm text-muted-foreground">EPS (ttm)</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.eps ? selectedStock.metadata.eps.toFixed(2) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">P/E Ratio</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.pe_ratio ? selectedStock.metadata.pe_ratio.toFixed(2) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Forward P/E</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.forward_pe ? selectedStock.metadata.forward_pe.toFixed(2) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Dividend Yield</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.dividend_yield
                                        ? `${(selectedStock.metadata.dividend_yield * 100).toFixed(2)}%`
                                        : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Ex-Dividend Date</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.ex_dividend_date || 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Earnings Date</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.earnings_date || 'N/A'}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {financialsAnalysis && (
                        <Card>
                          <CardHeader>
                            <CardTitle>AI-Powered Financials Analysis</CardTitle>
                            {financialsAnalysis.confidence_score !== undefined && financialsAnalysis.confidence_score !== null && !isNaN(financialsAnalysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(financialsAnalysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {financialsAnalysis.summary && (
                              <div>
                                <h3 className="font-semibold mb-2">Summary</h3>
                                <p className="text-muted-foreground">{financialsAnalysis.summary}</p>
                              </div>
                            )}
                            {financialsAnalysis.key_insights && financialsAnalysis.key_insights.length > 0 && (
                              <div>
                                <h3 className="font-semibold mb-2">Key Insights</h3>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                  {financialsAnalysis.key_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {financialsAnalysis.fundamental_analysis && (
                              <div className="space-y-4">
                                {Object.entries(financialsAnalysis.fundamental_analysis).map(([key, value]) => (
                                  <div key={key}>
                                    <h3 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                                    {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                      <div className="space-y-2">
                                        {Object.entries(value as any).map(([subKey, subValue]) => {
                                          // Handle nested objects
                                          if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="space-y-1">
                                                <span className="text-sm font-medium text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="ml-4 space-y-1">
                                                  {Object.entries(subValue as any).map(([nestedKey, nestedValue]) => (
                                                    <div key={nestedKey} className="flex items-center gap-2">
                                                      <span className="text-xs text-muted-foreground capitalize">{nestedKey.replace(/_/g, ' ')}:</span>
                                                      <Badge variant="outline" className="text-xs">
                                                        {Array.isArray(nestedValue)
                                                          ? nestedValue.join(', ')
                                                          : typeof nestedValue === 'object' && nestedValue !== null
                                                          ? JSON.stringify(nestedValue)
                                                          : String(nestedValue)}
                                                      </Badge>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          // Handle arrays
                                          if (Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="flex items-center gap-2">
                                                <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="flex flex-wrap gap-2">
                                                  {subValue.map((item: any, idx: number) => (
                                                    <Badge key={idx} variant="outline">{String(item)}</Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          // Handle primitive values
                                          return (
                                            <div key={subKey} className="flex items-center gap-2">
                                              <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                              <Badge variant="outline">{String(subValue)}</Badge>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : Array.isArray(value) ? (
                                      <div className="flex flex-wrap gap-2">
                                        {value.map((item: any, idx: number) => (
                                          <Badge key={idx} variant="outline">{String(item)}</Badge>
                                        ))}
                                      </div>
                                    ) : (
                                      <Badge variant="outline">{String(value)}</Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            {financialsAnalysis.recommendations && (
                              <div>
                                <h3 className="font-semibold mb-2">Recommendation</h3>
                                <Badge variant={getRecommendationColor(financialsAnalysis.recommendations.action)}>
                                  {financialsAnalysis.recommendations.action?.toUpperCase()}
                                </Badge>
                                {financialsAnalysis.recommendations.reasoning && (
                                  <p className="text-muted-foreground mt-2">{financialsAnalysis.recommendations.reasoning}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>

                    {/* Statistics Tab */}
                    <TabsContent value="statistics" className="mt-6 space-y-6">
                      {selectedStock && (
                        <Card>
                          <CardHeader>
                            <CardTitle>Statistical Metrics</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {/* Left Column */}
                              <div className="space-y-4">
                                <h3 className="font-semibold text-lg mb-4">Trading Statistics</h3>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <div className="text-sm text-muted-foreground">Volume</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.volume ? formatNumber(selectedStock.volume) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Average Volume</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.average_volume ? formatNumber(selectedStock.metadata.average_volume) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Day's Range</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.day_high && selectedStock.metadata?.day_low
                                        ? `${formatCurrency(selectedStock.metadata.day_low)} - ${formatCurrency(selectedStock.metadata.day_high)}`
                                        : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Previous Close</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.previous_close ? formatCurrency(selectedStock.previous_close) : 'N/A'}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Right Column */}
                              <div className="space-y-4">
                                <h3 className="font-semibold text-lg mb-4">Volatility & Momentum</h3>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <div className="text-sm text-muted-foreground">52-Week Range</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.['52_week_high'] && selectedStock.metadata?.['52_week_low']
                                        ? `${formatCurrency(selectedStock.metadata['52_week_low'])} - ${formatCurrency(selectedStock.metadata['52_week_high'])}`
                                        : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Beta</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.beta ? selectedStock.metadata.beta.toFixed(2) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">RSI</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.metadata?.rsi ? selectedStock.metadata.rsi.toFixed(2) : 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-sm text-muted-foreground">Price vs 52W High</div>
                                    <div className="font-semibold text-lg">
                                      {selectedStock.current_price && selectedStock.metadata?.['52_week_high']
                                        ? `${((selectedStock.current_price / selectedStock.metadata['52_week_high']) * 100).toFixed(2)}%`
                                        : 'N/A'}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {statisticsAnalysis && (
                        <Card>
                          <CardHeader>
                            <CardTitle>AI-Powered Statistics Analysis</CardTitle>
                            {statisticsAnalysis.confidence_score !== undefined && statisticsAnalysis.confidence_score !== null && !isNaN(statisticsAnalysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(statisticsAnalysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {statisticsAnalysis.summary && (
                              <div>
                                <h3 className="font-semibold mb-2">Summary</h3>
                                <p className="text-muted-foreground">{statisticsAnalysis.summary}</p>
                              </div>
                            )}
                            {statisticsAnalysis.key_insights && statisticsAnalysis.key_insights.length > 0 && (
                              <div>
                                <h3 className="font-semibold mb-2">Key Insights</h3>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                  {statisticsAnalysis.key_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {statisticsAnalysis.technical_analysis && (
                              <div className="space-y-4">
                                {Object.entries(statisticsAnalysis.technical_analysis).map(([key, value]) => (
                                  <div key={key}>
                                    <h3 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                                    {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                      <div className="space-y-2">
                                        {Object.entries(value as any).map(([subKey, subValue]) => {
                                          if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="space-y-1">
                                                <span className="text-sm font-medium text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="ml-4 space-y-1">
                                                  {Object.entries(subValue as any).map(([nestedKey, nestedValue]) => (
                                                    <div key={nestedKey} className="flex items-center gap-2">
                                                      <span className="text-xs text-muted-foreground capitalize">{nestedKey.replace(/_/g, ' ')}:</span>
                                                      <Badge variant="outline" className="text-xs">
                                                        {Array.isArray(nestedValue)
                                                          ? nestedValue.join(', ')
                                                          : typeof nestedValue === 'object' && nestedValue !== null
                                                          ? JSON.stringify(nestedValue)
                                                          : String(nestedValue)}
                                                      </Badge>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          if (Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="flex items-center gap-2">
                                                <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="flex flex-wrap gap-2">
                                                  {subValue.map((item: any, idx: number) => (
                                                    <Badge key={idx} variant="outline">{String(item)}</Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          return (
                                            <div key={subKey} className="flex items-center gap-2">
                                              <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                              <Badge variant="outline">{String(subValue)}</Badge>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : Array.isArray(value) ? (
                                      <div className="flex flex-wrap gap-2">
                                        {value.map((item: any, idx: number) => (
                                          <Badge key={idx} variant="outline">{String(item)}</Badge>
                                        ))}
                                      </div>
                                    ) : (
                                      <Badge variant="outline">{String(value)}</Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            {statisticsAnalysis.recommendations && (
                              <div>
                                <h3 className="font-semibold mb-2">Recommendation</h3>
                                <Badge variant={getRecommendationColor(statisticsAnalysis.recommendations.action)}>
                                  {statisticsAnalysis.recommendations.action?.toUpperCase()}
                                </Badge>
                                {statisticsAnalysis.recommendations.reasoning && (
                                  <p className="text-muted-foreground mt-2">{statisticsAnalysis.recommendations.reasoning}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>

                    <TabsContent value="dividends" className="mt-6">
                      <p className="text-muted-foreground">Dividends data coming soon...</p>
                    </TabsContent>

                    {/* History Tab */}
                    <TabsContent value="history" className="mt-6 space-y-6">
                      {/* Historical Price Chart */}
                      {selectedStock && (
                        <Card>
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <CardTitle>Price History</CardTitle>
                              <div className="flex gap-2 flex-wrap">
                                {['1d', '5d', '1mo', 'ytd', '1y', '5y', 'max'].map((period) => (
                                  <Button
                                    key={period}
                                    variant={pricePeriod === period ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setPricePeriod(period)}
                                  >
                                    {period === '1d' ? '1 Day' :
                                     period === '5d' ? '5 Days' :
                                     period === '1mo' ? '1 Month' :
                                     period === 'ytd' ? 'YTD' :
                                     period === '1y' ? '1 Year' :
                                     period === '5y' ? '5 Years' : 'Max'}
                                  </Button>
                                ))}
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            {isLoadingPrices ? (
                              <div className="flex items-center justify-center h-96">
                                <Loader2 className="w-8 h-8 animate-spin" />
                              </div>
                            ) : (
                              <div className="h-96">
                                <PriceChart
                                  data={historicalPrices}
                                  symbol={selectedStock.symbol}
                                  period={pricePeriod}
                                />
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}

                      {/* Historical Price Data Table */}
                      {historicalPrices.length > 0 && (
                        <Card>
                          <CardHeader>
                            <CardTitle>Historical Price Data</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b">
                                    <th className="text-left p-2">Date</th>
                                    <th className="text-right p-2">Open</th>
                                    <th className="text-right p-2">High</th>
                                    <th className="text-right p-2">Low</th>
                                    <th className="text-right p-2">Close</th>
                                    <th className="text-right p-2">Volume</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {historicalPrices.slice(-20).reverse().map((price, idx) => (
                                    <tr key={idx} className="border-b hover:bg-gray-50">
                                      <td className="p-2">{price.date}</td>
                                      <td className="p-2 text-right">{formatCurrency(price.open)}</td>
                                      <td className="p-2 text-right">{formatCurrency(price.high)}</td>
                                      <td className="p-2 text-right">{formatCurrency(price.low)}</td>
                                      <td className="p-2 text-right font-semibold">{formatCurrency(price.close)}</td>
                                      <td className="p-2 text-right">{price.volume ? formatNumber(price.volume) : 'N/A'}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {historyAnalysis && (
                        <Card>
                          <CardHeader>
                            <CardTitle>AI-Powered History Analysis</CardTitle>
                            {historyAnalysis.confidence_score !== undefined && historyAnalysis.confidence_score !== null && !isNaN(historyAnalysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(historyAnalysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {historyAnalysis.summary && (
                              <div>
                                <h3 className="font-semibold mb-2">Summary</h3>
                                <p className="text-muted-foreground">{historyAnalysis.summary}</p>
                              </div>
                            )}
                            {historyAnalysis.key_insights && historyAnalysis.key_insights.length > 0 && (
                              <div>
                                <h3 className="font-semibold mb-2">Key Insights</h3>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                  {historyAnalysis.key_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {historyAnalysis.technical_analysis && (
                              <div className="space-y-4">
                                {Object.entries(historyAnalysis.technical_analysis).map(([key, value]) => (
                                  <div key={key}>
                                    <h3 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                                    {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                                      <div className="space-y-2">
                                        {Object.entries(value as any).map(([subKey, subValue]) => {
                                          if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="space-y-1">
                                                <span className="text-sm font-medium text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="ml-4 space-y-1">
                                                  {Object.entries(subValue as any).map(([nestedKey, nestedValue]) => (
                                                    <div key={nestedKey} className="flex items-center gap-2">
                                                      <span className="text-xs text-muted-foreground capitalize">{nestedKey.replace(/_/g, ' ')}:</span>
                                                      <Badge variant="outline" className="text-xs">
                                                        {Array.isArray(nestedValue)
                                                          ? nestedValue.join(', ')
                                                          : typeof nestedValue === 'object' && nestedValue !== null
                                                          ? JSON.stringify(nestedValue)
                                                          : String(nestedValue)}
                                                      </Badge>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          if (Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="flex items-center gap-2">
                                                <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="flex flex-wrap gap-2">
                                                  {subValue.map((item: any, idx: number) => (
                                                    <Badge key={idx} variant="outline">{String(item)}</Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          return (
                                            <div key={subKey} className="flex items-center gap-2">
                                              <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                              <Badge variant="outline">{String(subValue)}</Badge>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : Array.isArray(value) ? (
                                      <div className="flex flex-wrap gap-2">
                                        {value.map((item: any, idx: number) => (
                                          <Badge key={idx} variant="outline">{String(item)}</Badge>
                                        ))}
                                      </div>
                                    ) : (
                                      <Badge variant="outline">{String(value)}</Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            {historyAnalysis.price_targets && (
                              <div>
                                <h3 className="font-semibold mb-2">Price Targets</h3>
                                <div className="grid grid-cols-3 gap-4">
                                  {historyAnalysis.price_targets.short_term_1m && (
                                    <div>
                                      <div className="text-sm text-muted-foreground">1 Month</div>
                                      <div className="font-semibold">
                                        {typeof historyAnalysis.price_targets.short_term_1m === 'number'
                                          ? formatCurrency(historyAnalysis.price_targets.short_term_1m)
                                          : historyAnalysis.price_targets.short_term_1m}
                                      </div>
                                    </div>
                                  )}
                                  {historyAnalysis.price_targets.medium_term_3m && (
                                    <div>
                                      <div className="text-sm text-muted-foreground">3 Months</div>
                                      <div className="font-semibold">
                                        {typeof historyAnalysis.price_targets.medium_term_3m === 'number'
                                          ? formatCurrency(historyAnalysis.price_targets.medium_term_3m)
                                          : historyAnalysis.price_targets.medium_term_3m}
                                      </div>
                                    </div>
                                  )}
                                  {historyAnalysis.price_targets.long_term_12m && (
                                    <div>
                                      <div className="text-sm text-muted-foreground">12 Months</div>
                                      <div className="font-semibold">
                                        {typeof historyAnalysis.price_targets.long_term_12m === 'number'
                                          ? formatCurrency(historyAnalysis.price_targets.long_term_12m)
                                          : historyAnalysis.price_targets.long_term_12m}
                                      </div>
                                    </div>
                                  )}
                                </div>
                                {historyAnalysis.price_targets.target_basis && (
                                  <p className="text-sm text-muted-foreground mt-2">
                                    {historyAnalysis.price_targets.target_basis}
                                  </p>
                                )}
                              </div>
                            )}
                            {historyAnalysis.recommendations && (
                              <div>
                                <h3 className="font-semibold mb-2">Recommendation</h3>
                                <Badge variant={getRecommendationColor(historyAnalysis.recommendations.action)}>
                                  {historyAnalysis.recommendations.action?.toUpperCase()}
                                </Badge>
                                {historyAnalysis.recommendations.reasoning && (
                                  <p className="text-muted-foreground mt-2">{historyAnalysis.recommendations.reasoning}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>

                    {/* Stock News Tab */}
                    <TabsContent value="news" className="mt-6 space-y-6">
                      {/* News Articles List */}
                      <Card>
                        <CardHeader>
                          <CardTitle>Recent News Articles</CardTitle>
                        </CardHeader>
                        <CardContent>
                          {isLoadingNews ? (
                            <div className="flex items-center justify-center py-8">
                              <Loader2 className="w-8 h-8 animate-spin" />
                            </div>
                          ) : stockNews.length > 0 ? (
                            <div className="space-y-4">
                              {stockNews.map((article, idx) => (
                                <div key={idx} className="border-b pb-4 last:border-0">
                                  <h4 className="font-semibold mb-1">{article.title}</h4>
                                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                    <span>{article.publisher}</span>
                                    {article.published_date && (
                                      <span>
                                        {new Date(article.published_date * 1000).toLocaleDateString()}
                                      </span>
                                    )}
                                  </div>
                                  {article.link && (
                                    <a
                                      href={article.link}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm text-blue-600 hover:underline mt-2 inline-block"
                                    >
                                      Read more →
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-muted-foreground text-center py-8">No news articles available</p>
                          )}
                        </CardContent>
                      </Card>

                      {newsAnalysis && (
                        <Card>
                          <CardHeader>
                            <CardTitle>AI-Powered News Analysis</CardTitle>
                            {newsAnalysis.confidence_score !== undefined && newsAnalysis.confidence_score !== null && !isNaN(newsAnalysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(newsAnalysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {newsAnalysis.summary && (
                              <div>
                                <h3 className="font-semibold mb-2">Summary</h3>
                                <p className="text-muted-foreground">{newsAnalysis.summary}</p>
                              </div>
                            )}
                            {newsAnalysis.key_insights && newsAnalysis.key_insights.length > 0 && (
                              <div>
                                <h3 className="font-semibold mb-2">Key Insights</h3>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                  {newsAnalysis.key_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {newsAnalysis.risk_assessment && (
                              <div className="space-y-4">
                                {Object.entries(newsAnalysis.risk_assessment).map(([key, value]) => (
                                  <div key={key}>
                                    <h3 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                                    {Array.isArray(value) ? (
                                      <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                        {value.map((item, idx) => (
                                          <li key={idx}>{String(item)}</li>
                                        ))}
                                      </ul>
                                    ) : typeof value === 'object' && value !== null ? (
                                      <div className="space-y-2">
                                        {Object.entries(value as any).map(([subKey, subValue]) => {
                                          if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="space-y-1">
                                                <span className="text-sm font-medium text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="ml-4 space-y-1">
                                                  {Object.entries(subValue as any).map(([nestedKey, nestedValue]) => (
                                                    <div key={nestedKey} className="flex items-center gap-2">
                                                      <span className="text-xs text-muted-foreground capitalize">{nestedKey.replace(/_/g, ' ')}:</span>
                                                      <Badge variant="outline" className="text-xs">
                                                        {Array.isArray(nestedValue)
                                                          ? nestedValue.join(', ')
                                                          : typeof nestedValue === 'object' && nestedValue !== null
                                                          ? JSON.stringify(nestedValue)
                                                          : String(nestedValue)}
                                                      </Badge>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          if (Array.isArray(subValue)) {
                                            return (
                                              <div key={subKey} className="flex items-center gap-2">
                                                <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                                <div className="flex flex-wrap gap-2">
                                                  {subValue.map((item: any, idx: number) => (
                                                    <Badge key={idx} variant="outline">{String(item)}</Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          }
                                          return (
                                            <div key={subKey} className="flex items-center gap-2">
                                              <span className="text-sm text-muted-foreground capitalize">{subKey.replace(/_/g, ' ')}:</span>
                                              <Badge variant="outline">{String(subValue)}</Badge>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : (
                                      <Badge variant="outline">{String(value)}</Badge>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                            {newsAnalysis.recommendations && (
                              <div>
                                <h3 className="font-semibold mb-2">Recommendation</h3>
                                <Badge variant={getRecommendationColor(newsAnalysis.recommendations.action)}>
                                  {newsAnalysis.recommendations.action?.toUpperCase()}
                                </Badge>
                                {newsAnalysis.recommendations.reasoning && (
                                  <p className="text-muted-foreground mt-2">{newsAnalysis.recommendations.reasoning}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </TabsContent>
                    <TabsContent value="profile" className="mt-6">
                      <div className="space-y-4">
                        {selectedStock.sector && (
                          <div>
                            <div className="text-sm text-muted-foreground">Sector</div>
                            <div className="font-semibold">{selectedStock.sector}</div>
                          </div>
                        )}
                        {selectedStock.industry && (
                          <div>
                            <div className="text-sm text-muted-foreground">Industry</div>
                            <div className="font-semibold">{selectedStock.industry}</div>
                          </div>
                        )}
                        {selectedStock.metadata?.description && (
                          <div>
                            <div className="text-sm text-muted-foreground">Description</div>
                            <div className="text-sm">{selectedStock.metadata.description}</div>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

            </div>
          )}

          {/* Comparison View */}
          {showComparison && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Stock Comparison</CardTitle>
                  <div className="flex gap-2">
                    {comparisonStocks.length > 0 && (
                      <Button onClick={handleCompareStocks} disabled={comparisonStocks.length < 2}>
                        <GitCompare className="w-4 h-4 mr-2" />
                        Compare {comparisonStocks.length} Stocks
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      onClick={() => {
                        setComparisonStocks([]);
                        setShowComparison(false);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Clear
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {comparisonStocks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Add stocks to comparison from search results
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Symbol</th>
                          <th className="text-left p-2">Company</th>
                          <th className="text-right p-2">Price</th>
                          <th className="text-right p-2">Change %</th>
                          <th className="text-right p-2">Market Cap</th>
                          <th className="text-right p-2">Volume</th>
                          <th className="text-left p-2">Sector</th>
                          <th className="text-center p-2">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonStocks.map((stock) => (
                          <tr key={stock.symbol} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-bold">{stock.symbol}</td>
                            <td className="p-2">{stock.company_name}</td>
                            <td className="p-2 text-right">
                              {stock.current_price ? formatCurrency(stock.current_price) : 'N/A'}
                            </td>
                            <td className={`p-2 text-right ${getPriceChangeColor(stock.price_change_percent)}`}>
                              {stock.price_change_percent !== undefined && stock.price_change_percent !== null
                                ? `${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent.toFixed(2)}%`
                                : 'N/A'}
                            </td>
                            <td className="p-2 text-right">
                              {stock.market_cap ? formatNumber(stock.market_cap) : 'N/A'}
                            </td>
                            <td className="p-2 text-right">
                              {stock.volume ? formatNumber(stock.volume) : 'N/A'}
                            </td>
                            <td className="p-2">{stock.sector || 'N/A'}</td>
                            <td className="p-2 text-center">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setComparisonStocks(
                                    comparisonStocks.filter((s) => s.symbol !== stock.symbol)
                                  );
                                }}
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default React.memo(DiscoveryDashboard);
