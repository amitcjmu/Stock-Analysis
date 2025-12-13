import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader2, AlertTriangle, Plus, GitCompare } from 'lucide-react';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { useAuth } from '../../contexts/AuthContext';
import { apiCall } from '../../config/api';

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

/**
 * Stock Overview Page - Shows stock search results
 */
const DiscoveryDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonStocks, setComparisonStocks] = useState<Stock[]>([]);

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const getPriceChangeColor = (change?: number | null) => {
    if (change === undefined || change === null) return 'text-gray-500';
    return change >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setError(null);
    setSearchResults([]);

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

  const handleViewStock = (stock: Stock) => {
    // Navigate to stock analysis page with the selected stock
    navigate('/discovery/stock-analysis', { state: { stock } });
  };

  const handleAddToComparison = (stock: Stock) => {
    if (!comparisonStocks.find(s => s.symbol === stock.symbol)) {
      setComparisonStocks([...comparisonStocks, stock]);
    }
  };

  const handleCompareStocks = () => {
    if (comparisonStocks.length < 2) {
      setError('Select at least 2 stocks to compare');
      return;
    }
    // Navigate to comparison view
    navigate('/discovery/stock-analysis', { 
      state: { comparisonStocks } 
    });
  };

  return (
    <div className="flex-1 flex flex-col">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        <ContextBreadcrumbs />
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Stock Analysis Overview</h1>
              <p className="text-muted-foreground">
                Search for stocks and view detailed analysis
              </p>
            </div>
            {comparisonStocks.length >= 2 && (
              <Button onClick={handleCompareStocks}>
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
              <div className="flex gap-2">
                <Input
                  placeholder="Enter stock symbol or company name (e.g., HCLTECH, RELIANCE, AAPL, Apple)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1"
                />
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
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddToComparison(stock)}
                            disabled={isInComparison}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            {isInComparison ? 'Added' : 'Compare'}
                          </Button>
                          <Button
                            onClick={() => handleViewStock(stock)}
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
        </div>
      </main>
    </div>
  );
};

export default React.memo(DiscoveryDashboard);
