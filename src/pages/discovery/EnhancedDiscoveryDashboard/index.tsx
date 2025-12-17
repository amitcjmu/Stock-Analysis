import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Loader2, AlertTriangle, Plus, GitCompare, X, Star, StarOff, BarChart3, CheckCircle } from 'lucide-react';

// Components
import Sidebar from '../../../components/Sidebar';
import { ContextBreadcrumbs } from '../../../components/context/ContextBreadcrumbs';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Alert, AlertDescription } from '../../../components/ui/alert';
import { Badge } from '../../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Popover, PopoverContent, PopoverTrigger } from '../../../components/ui/popover';
import { PriceChart } from '../../../components/stock/PriceChart';
import { ModelSelector, ModelType } from '../../../components/stock/ModelSelector';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';

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

interface HistoricalPrice {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface StockAnalysis {
  summary?: string;
  key_insights?: string[];
  recommendations?: {
    action?: string;
    reasoning?: string;
  };
  technical_analysis?: any;
  fundamental_analysis?: any;
  risk_assessment?: any;
  price_targets?: any;
  confidence_score?: number;
}

interface WatchlistItem {
  id: string;
  stock_symbol: string;
  stock_data?: Stock;
}

/**
 * Stock Overview Page - Shows stock search results and details
 */
const EnhancedDiscoveryDashboardContainer: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [comparisonStocks, setComparisonStocks] = useState<Stock[]>([]);
  const [historicalPrices, setHistoricalPrices] = useState<HistoricalPrice[]>([]);
  const [pricePeriod, setPricePeriod] = useState('1mo');
  const [isLoadingPrices, setIsLoadingPrices] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedModel, setSelectedModel] = useState<ModelType>('auto');

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<Stock[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

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
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
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
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  }, [showSuggestions, suggestions, selectedSuggestionIndex]);

  // Handle suggestion selection
  const handleSelectSuggestion = (stock: Stock) => {
    setSearchQuery(stock.symbol);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setSuggestions([]);
    // Call handleAnalyzeStock directly - it's defined later in the component
    handleAnalyzeStock(stock);
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchInputRef.current && !searchInputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

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

  const handleAnalyzeStock = async (stock: Stock) => {
    setSelectedStock(stock);
    setAnalysis(null);
    setError(null);
    setActiveTab('overview');
    setIsAnalyzing(false);

    try {
      // Fetch full stock details from API
      const response = await apiCall(
        `/stock/stocks/${encodeURIComponent(stock.symbol)}`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (response.success && response.stock) {
        setSelectedStock(response.stock);
      }
    } catch (err: any) {
      console.error('Error fetching stock details:', err);
    }

    // Load historical prices
    await loadHistoricalPrices(stock.symbol, pricePeriod);

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
      // Prepare request body with model parameter (only include if not 'auto')
      const requestBody: { symbol: string; model?: string } = {
        symbol: selectedStock.symbol,
      };
      if (selectedModel !== 'auto') {
        requestBody.model = selectedModel;
      }

      const response = await apiCall(
        '/stock/stocks/analyze',
        {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        }
      );

      if (response.success && response.analysis) {
        setAnalysis(response.analysis);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze stock');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddToWatchlist = async (stock: Stock) => {
    try {
      setError(null);
      const response = await apiCall(
        `/stock/stocks/watchlist?symbol=${encodeURIComponent(stock.symbol)}`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
        }
      );

      if (response.success) {
        setIsInWatchlist(true);
        await loadWatchlist();
        // Clear any previous errors and show success message
        setError(null);
        setSuccessMessage(`Successfully added ${stock.symbol} to watchlist`);
        // Clear success message after 3 seconds
        setTimeout(() => setSuccessMessage(null), 3000);
        console.log(`✅ Successfully added ${stock.symbol} to watchlist`);
      } else {
        setError(response.message || 'Failed to add to watchlist');
        setSuccessMessage(null);
      }
    } catch (err: any) {
      const errorMessage = err.message || err.detail || err.response?.data?.detail || 'Failed to add to watchlist';
      setError(errorMessage);
      setSuccessMessage(null);
      console.error('Error adding to watchlist:', err);
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
    if (!comparisonStocks.find(s => s.symbol === stock.symbol)) {
      setComparisonStocks([...comparisonStocks, stock]);
    }
  };

  const handlePeriodChange = (period: string) => {
    setPricePeriod(period);
    if (selectedStock) {
      loadHistoricalPrices(selectedStock.symbol, period);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, []);

  useEffect(() => {
    if (selectedStock) {
      const inWatchlist = watchlist.some(
        (item) => item.stock_symbol.toUpperCase() === selectedStock.symbol.toUpperCase()
      );
      setIsInWatchlist(inWatchlist);
    }
  }, [selectedStock, watchlist]);

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
                {comparisonStocks.length >= 2 && (
                  <Button onClick={() => setComparisonStocks([])}>
                    <GitCompare className="w-4 h-4 mr-2" />
                    Compare {comparisonStocks.length} Stocks
                  </Button>
                )}
          </div>

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

          {/* Success Message */}
          {successMessage && (
                <Alert variant="default" className="bg-green-50 border-green-200">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">{successMessage}</AlertDescription>
                </Alert>
              )}

              {/* Search Results */}
              {searchResults.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Search Results ({searchResults.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {searchResults.map((stock) => {
                        const isInComparison = comparisonStocks.some(s => s.symbol === stock.symbol);
                        return (
                          <div
                            key={stock.symbol}
                            className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
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
                              {watchlist.some((item) => item.stock_symbol.toUpperCase() === stock.symbol.toUpperCase()) ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleRemoveFromWatchlist(stock.symbol);
                                  }}
                                >
                                  <StarOff className="w-4 h-4 mr-1" />
                                  In Watchlist
                                </Button>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleAddToWatchlist(stock);
                                  }}
                                >
                                  <Star className="w-4 h-4 mr-1" />
                                  Add to Watchlist
                                </Button>
                              )}
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAddToComparison(stock);
                                }}
                                disabled={isInComparison}
                              >
                                <Plus className="w-4 h-4 mr-1" />
                                {isInComparison ? 'Added' : 'Compare'}
                              </Button>
                              <Button
                                onClick={() => handleAnalyzeStock(stock)}
                                size="sm"
                              >
                                View Details
                              </Button>
                            </div>
                          </div>
                        );
                      })}
            </div>
                  </CardContent>
                </Card>
              )}

              {/* Empty State */}
              {!isSearching && searchResults.length === 0 && !error && (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Search className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Search for Stocks</h3>
                    <p className="text-muted-foreground">
                      Enter a stock symbol or company name to get started
                    </p>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* Selected Stock Details */}
          {selectedStock && (
            <div className="space-y-6">
              {/* Compact Search Bar */}
              <div className="flex gap-2 items-center">
                <Input
                  placeholder="Search for another stock..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1"
                />
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

              {/* Error and Success Messages */}
              {error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {successMessage && (
                <Alert variant="default" className="bg-green-50 border-green-200">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">{successMessage}</AlertDescription>
                </Alert>
              )}

              {/* Stock Header */}
              <Card>
                <CardContent className="pt-6">
                  <div className="mb-4">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {selectedStock.company_name} ({selectedStock.exchange || 'N/A'}:{selectedStock.symbol})
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedStock.metadata?.country || 'United States'} {selectedStock.metadata?.country === 'India' ? 'Delayed Price' : ''} - Currency is {selectedStock.currency || selectedStock.metadata?.currency || 'USD'}
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
                        <Button variant="default" onClick={() => handleRemoveFromWatchlist(selectedStock.symbol)}>
                          <StarOff className="w-4 h-4 mr-2" /> Watchlist
                        </Button>
                      ) : (
                        <Button variant="default" onClick={() => handleAddToWatchlist(selectedStock)}>
                          <Star className="w-4 h-4 mr-2" /> Watchlist
                        </Button>
                      )}
                      <Button variant="default" onClick={() => handleAddToComparison(selectedStock)}>
                        <GitCompare className="w-4 h-4 mr-2" /> Compare
                      </Button>
                    </div>
                  </div>

                  {/* Tabs */}
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-7">
              <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="financials">Financials</TabsTrigger>
                      <TabsTrigger value="statistics">Statistics</TabsTrigger>
                      <TabsTrigger value="dividends">Dividends</TabsTrigger>
                      <TabsTrigger value="history">History</TabsTrigger>
                      <TabsTrigger value="profile">Profile</TabsTrigger>
                      <TabsTrigger value="chart">Chart</TabsTrigger>
            </TabsList>

                    {/* Overview Tab */}
                    <TabsContent value="overview" className="mt-6 space-y-6">
                      {/* AI Analysis Button */}
                      {!analysis && (
                        <div className="flex justify-between items-center">
                          <ModelSelector
                            value={selectedModel}
                            onChange={setSelectedModel}
                          />
                          <Button onClick={handleAnalyzeStockWithAI} disabled={isAnalyzing} size="lg">
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

                      {/* AI Analysis Results */}
                      {analysis && (
                        <Card className="mb-6">
                          <CardHeader>
                            <CardTitle>AI-Powered Analysis</CardTitle>
                            {analysis.confidence_score !== undefined && analysis.confidence_score !== null && !isNaN(analysis.confidence_score) && (
                              <p className="text-sm text-muted-foreground">
                                Confidence: {(analysis.confidence_score * 100).toFixed(0)}%
                              </p>
                            )}
                          </CardHeader>
                          <CardContent>
                            {analysis.summary && (
                              <div className="mb-4">
                                <h3 className="font-semibold mb-2">Executive Summary</h3>
                                <p className="text-muted-foreground">{analysis.summary}</p>
                              </div>
                            )}
                            {analysis.key_insights && analysis.key_insights.length > 0 && (
                              <div className="mb-4">
                                <h3 className="font-semibold mb-2">Key Insights</h3>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                  {analysis.key_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {analysis.recommendations && (
                              <div>
                                <h3 className="font-semibold mb-2">Recommendation</h3>
                                <Badge variant={getRecommendationColor(analysis.recommendations.action)} className="text-lg px-3 py-1">
                                  {analysis.recommendations.action?.toUpperCase() || 'HOLD'}
                                </Badge>
                                {analysis.recommendations.reasoning && (
                                  <p className="text-muted-foreground mt-2">{analysis.recommendations.reasoning}</p>
                                )}
                              </div>
                            )}
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
                            {selectedStock.volume && (
                              <div>
                                <div className="text-sm text-muted-foreground">Volume</div>
                                <div className="font-semibold text-lg">{formatNumber(selectedStock.volume)}</div>
                              </div>
                            )}
                            {selectedStock.previous_close && (
                              <div>
                                <div className="text-sm text-muted-foreground">Previous Close</div>
                                <div className="font-semibold text-lg">{formatCurrency(selectedStock.previous_close)}</div>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            {selectedStock.sector && (
                              <div>
                                <div className="text-sm text-muted-foreground">Sector</div>
                                <div className="font-semibold text-lg">{selectedStock.sector}</div>
                              </div>
                            )}
                            {selectedStock.industry && (
                              <div>
                                <div className="text-sm text-muted-foreground">Industry</div>
                                <div className="font-semibold text-lg">{selectedStock.industry}</div>
                              </div>
                            )}
                          </div>
                </div>
              </div>
            </TabsContent>

                    {/* Chart Tab */}
                    <TabsContent value="chart" className="mt-6">
                      <div className="space-y-4">
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

                    {/* Profile Tab */}
                    <TabsContent value="profile" className="mt-6">
                      <div className="space-y-4">
                        {selectedStock.sector && (
                          <div>
                            <h3 className="font-semibold text-lg">Sector</h3>
                            <p className="text-muted-foreground">{selectedStock.sector}</p>
                          </div>
                        )}
                        {selectedStock.industry && (
                          <div>
                            <h3 className="font-semibold text-lg">Industry</h3>
                            <p className="text-muted-foreground">{selectedStock.industry}</p>
                          </div>
                        )}
                        {selectedStock.metadata?.description && (
                          <div>
                            <h3 className="font-semibold text-lg">Company Description</h3>
                            <p className="text-muted-foreground">{selectedStock.metadata.description}</p>
                          </div>
                        )}
                      </div>
            </TabsContent>

                    {/* Other tabs - placeholder */}
                    <TabsContent value="financials" className="mt-6">
                      <p className="text-muted-foreground">Financials data coming soon...</p>
                    </TabsContent>
                    <TabsContent value="statistics" className="mt-6">
                      <p className="text-muted-foreground">Statistics data coming soon...</p>
                    </TabsContent>
                    <TabsContent value="dividends" className="mt-6">
                      <p className="text-muted-foreground">Dividends data coming soon...</p>
                    </TabsContent>
                    <TabsContent value="history" className="mt-6">
                      <p className="text-muted-foreground">History data coming soon...</p>
            </TabsContent>
          </Tabs>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default EnhancedDiscoveryDashboardContainer;
