import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, RefreshCw, TrendingUp } from 'lucide-react';

import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
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

interface SectorView {
  id: string;
  name: string;
  one_day_change_percent: number;
  gainers: number;
  losers: number;
}

interface Stock {
  symbol: string;
  company_name?: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  current_price?: number;
  price_change_percent?: number;
  currency?: string;
}

const TrendingSectorsPage: React.FC = () => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();

  const [sectors, setSectors] = useState<SectorView[]>([]);
  const [selectedSector, setSelectedSector] = useState<SectorView | null>(null);
  const [sectorStocks, setSectorStocks] = useState<Stock[]>([]);
  const [isLoadingSectors, setIsLoadingSectors] = useState(false);
  const [isLoadingStocks, setIsLoadingStocks] = useState(false);
  const [isAddingAll, setIsAddingAll] = useState(false);
  const [isAddingSelected, setIsAddingSelected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('change_desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);

  const totalGainersLosers = useMemo(
    () => sectors.reduce((sum, sector) => sum + sector.gainers + sector.losers, 0),
    [sectors]
  );

  useEffect(() => {
    const loadSectors = async () => {
      setIsLoadingSectors(true);
      setError(null);
      try {
        const response = await apiCall<{ success: boolean; sectors?: SectorView[] }>(
          '/stock/stocks/sectors/trending',
          {
            method: 'GET',
            headers: getAuthHeaders(),
          }
        );
        if (response.success && response.sectors) {
          setSectors(response.sectors);
        } else {
          setError('Failed to load sectors.');
        }
      } catch {
        setError('Failed to load sectors.');
      } finally {
        setIsLoadingSectors(false);
      }
    };

    loadSectors();
  }, [getAuthHeaders]);

  const formatCurrency = (value?: number, currency: string = 'INR') => {
    if (value === undefined || value === null || Number.isNaN(value)) return 'N/A';
    const safeCurrency = currency === 'INR' ? 'INR' : 'USD';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: safeCurrency,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null || Number.isNaN(value)) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const loadSectorStocks = async (sector: SectorView) => {
    setSelectedSector(sector);
    setError(null);
    setActionMessage(null);
    setIsLoadingStocks(true);
    setSectorStocks([]);
    setSearchQuery('');
    setCurrentPage(1);
    setSelectedSymbols([]);

    try {
      const response = await apiCall<{ success: boolean; stocks?: Stock[] }>(
        `/stock/stocks/sectors/${sector.id}/stocks?refresh=true`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );
      if (response.success && response.stocks) {
        setSectorStocks(response.stocks);
      } else {
        setError('Failed to load stocks for the selected sector.');
      }
    } catch (err) {
      setError('Failed to load stocks for the selected sector.');
    } finally {
      setIsLoadingStocks(false);
    }
  };

  const filteredSortedStocks = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    let rows = sectorStocks.filter((stock) => {
      if (!query) return true;
      return (
        stock.symbol.toLowerCase().includes(query) ||
        (stock.company_name || '').toLowerCase().includes(query)
      );
    });

    rows = [...rows].sort((a, b) => {
      switch (sortBy) {
        case 'symbol_asc':
          return a.symbol.localeCompare(b.symbol);
        case 'symbol_desc':
          return b.symbol.localeCompare(a.symbol);
        case 'price_asc':
          return (a.current_price || 0) - (b.current_price || 0);
        case 'price_desc':
          return (b.current_price || 0) - (a.current_price || 0);
        case 'change_asc':
          return (a.price_change_percent || 0) - (b.price_change_percent || 0);
        case 'change_desc':
        default:
          return (b.price_change_percent || 0) - (a.price_change_percent || 0);
      }
    });

    return rows;
  }, [sectorStocks, searchQuery, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filteredSortedStocks.length / pageSize));
  const paginatedStocks = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredSortedStocks.slice(start, start + pageSize);
  }, [filteredSortedStocks, currentPage, pageSize]);
  const pageSymbols = useMemo(() => paginatedStocks.map((stock) => stock.symbol), [paginatedStocks]);
  const allPageSelected =
    pageSymbols.length > 0 && pageSymbols.every((symbol) => selectedSymbols.includes(symbol));

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, sortBy, pageSize]);

  const handleAddAllToWatchlist = async () => {
    if (!selectedSector || filteredSortedStocks.length === 0) return;
    setIsAddingAll(true);
    setActionMessage(null);

    let added = 0;
    let skipped = 0;

    for (const stock of filteredSortedStocks) {
      try {
        const response = await apiCall<{ success?: boolean; detail?: string }>(
          `/stock/stocks/watchlist?symbol=${encodeURIComponent(stock.symbol)}`,
          {
            method: 'POST',
            headers: getAuthHeaders(),
          }
        );
        if (response.success) {
          added += 1;
        } else {
          skipped += 1;
        }
      } catch {
        skipped += 1;
      }
    }

    setActionMessage(
      `Watchlist update complete for ${selectedSector.name}: ${added} added, ${skipped} skipped.`
    );
    setIsAddingAll(false);
  };

  const toggleStockSelection = (symbol: string) => {
    setSelectedSymbols((previous) =>
      previous.includes(symbol)
        ? previous.filter((item) => item !== symbol)
        : [...previous, symbol]
    );
  };

  const toggleSelectCurrentPage = () => {
    setSelectedSymbols((previous) => {
      if (allPageSelected) {
        return previous.filter((symbol) => !pageSymbols.includes(symbol));
      }
      const combined = new Set([...previous, ...pageSymbols]);
      return Array.from(combined);
    });
  };

  const handleAddSelectedToWatchlist = async () => {
    if (!selectedSector || selectedSymbols.length === 0) return;
    setIsAddingSelected(true);
    setActionMessage(null);

    let added = 0;
    let skipped = 0;

    for (const symbol of selectedSymbols) {
      try {
        const response = await apiCall<{ success?: boolean; detail?: string }>(
          `/stock/stocks/watchlist?symbol=${encodeURIComponent(symbol)}`,
          {
            method: 'POST',
            headers: getAuthHeaders(),
          }
        );
        if (response.success) {
          added += 1;
        } else {
          skipped += 1;
        }
      } catch {
        skipped += 1;
      }
    }

    setActionMessage(
      `Selected watchlist update for ${selectedSector.name}: ${added} added, ${skipped} skipped.`
    );
    setSelectedSymbols([]);
    setIsAddingSelected(false);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <ContextBreadcrumbs />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="h-8 w-8 text-green-600" />
                  Trending Sectors
                </h1>
                <p className="text-gray-600 mt-1">
                  Click any sector to view related stocks directly in this application.
                </p>
              </div>
              <Badge variant="secondary">In-app sector screener</Badge>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Sector Snapshot</CardTitle>
                <CardDescription>
                  {sectors.length} sectors • {totalGainersLosers} total movers
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {isLoadingSectors ? (
                  <div className="flex items-center gap-2 text-gray-600 px-6 py-8">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Loading sectors...
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Sector</TableHead>
                        <TableHead>Gainers / Losers (1D)</TableHead>
                        <TableHead className="text-right">1D Price Change</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sectors.map((sector) => (
                        <TableRow
                          key={sector.id}
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => loadSectorStocks(sector)}
                        >
                          <TableCell className="font-medium">{sector.name}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2 text-sm">
                              <Badge variant="secondary">{sector.gainers}</Badge>
                              <span className="text-gray-500">/</span>
                              <Badge variant="outline">{sector.losers}</Badge>
                            </div>
                          </TableCell>
                          <TableCell className="text-right text-green-600 font-medium">
                            {formatPercent(sector.one_day_change_percent)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>
                  {selectedSector ? `${selectedSector.name} Stocks` : 'Select a sector'}
                </CardTitle>
                <CardDescription>
                  {selectedSector
                    ? 'Live stock snapshots fetched from your stock API.'
                    : 'Click a sector above to load stocks.'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {error ? (
                  <p className="text-red-600">{error}</p>
                ) : isLoadingStocks ? (
                  <div className="flex items-center gap-2 text-gray-600">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Loading sector stocks...
                  </div>
                ) : sectorStocks.length === 0 ? (
                  <p className="text-gray-500">No stocks loaded yet.</p>
                ) : (
                  <div className="space-y-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div className="flex flex-col gap-2 md:flex-row md:items-center">
                        <Input
                          placeholder="Search symbol or company"
                          value={searchQuery}
                          onChange={(event) => setSearchQuery(event.target.value)}
                          className="md:w-72"
                        />
                        <select
                          value={sortBy}
                          onChange={(event) => setSortBy(event.target.value)}
                          className="h-10 rounded-md border border-gray-300 px-3 text-sm"
                        >
                          <option value="change_desc">Sort: Change high to low</option>
                          <option value="change_asc">Sort: Change low to high</option>
                          <option value="price_desc">Sort: Price high to low</option>
                          <option value="price_asc">Sort: Price low to high</option>
                          <option value="symbol_asc">Sort: Symbol A-Z</option>
                          <option value="symbol_desc">Sort: Symbol Z-A</option>
                        </select>
                        <select
                          value={String(pageSize)}
                          onChange={(event) => setPageSize(Number(event.target.value))}
                          className="h-10 rounded-md border border-gray-300 px-3 text-sm"
                        >
                          <option value="5">5 / page</option>
                          <option value="10">10 / page</option>
                          <option value="15">15 / page</option>
                        </select>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          onClick={handleAddSelectedToWatchlist}
                          disabled={isAddingSelected || selectedSymbols.length === 0}
                        >
                          {isAddingSelected
                            ? 'Adding selected...'
                            : `Add selected (${selectedSymbols.length})`}
                        </Button>
                        <Button onClick={handleAddAllToWatchlist} disabled={isAddingAll}>
                          {isAddingAll ? 'Adding...' : 'Add all to watchlist'}
                        </Button>
                      </div>
                    </div>

                    {actionMessage ? <p className="text-sm text-green-700">{actionMessage}</p> : null}

                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-[60px]">
                              <input
                                type="checkbox"
                                checked={allPageSelected}
                                onChange={toggleSelectCurrentPage}
                                aria-label="Select all stocks on current page"
                              />
                            </TableHead>
                            <TableHead>Symbol</TableHead>
                            <TableHead>Company</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>1D Change</TableHead>
                            <TableHead>Sector</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {paginatedStocks.map((stock) => (
                            <TableRow key={stock.symbol}>
                              <TableCell>
                                <input
                                  type="checkbox"
                                  checked={selectedSymbols.includes(stock.symbol)}
                                  onChange={() => toggleStockSelection(stock.symbol)}
                                  aria-label={`Select ${stock.symbol}`}
                                />
                              </TableCell>
                              <TableCell className="font-medium">{stock.symbol}</TableCell>
                              <TableCell>{stock.company_name || 'N/A'}</TableCell>
                              <TableCell>
                                {formatCurrency(stock.current_price, stock.currency || 'INR')}
                              </TableCell>
                              <TableCell
                                className={
                                  (stock.price_change_percent || 0) >= 0
                                    ? 'text-green-600'
                                    : 'text-red-600'
                                }
                              >
                                {formatPercent(stock.price_change_percent)}
                              </TableCell>
                              <TableCell>{stock.sector || selectedSector?.name || 'N/A'}</TableCell>
                              <TableCell className="text-right">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="gap-1"
                                  onClick={() =>
                                    navigate('/discovery/overview', {
                                      state: { stock },
                                    })
                                  }
                                >
                                  Analyze
                                  <ArrowUpRight className="h-4 w-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>

                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600">
                        Showing {paginatedStocks.length} of {filteredSortedStocks.length} stocks
                      </p>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={currentPage <= 1}
                          onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                        >
                          Previous
                        </Button>
                        <span className="text-sm text-gray-700">
                          Page {currentPage} of {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={currentPage >= totalPages}
                          onClick={() =>
                            setCurrentPage((page) => Math.min(totalPages, page + 1))
                          }
                        >
                          Next
                        </Button>
                      </div>
                    </div>
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

export default TrendingSectorsPage;
