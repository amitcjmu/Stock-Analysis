import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { 
  Search, 
  Download, 
  Trash2, 
  Archive, 
  Eye, 
  GitCompare,
  Calendar,
  Filter,
  MoreHorizontal,
  FileText,
  BarChart3,
  Clock,
  CheckCircle,
  AlertCircle,
  Star,
  TrendingUp,
  Users,
  Building2
} from 'lucide-react';
import { toast } from 'sonner';

export interface AnalysisHistoryItem {
  id: number;
  application_name: string;
  application_id: number;
  department: string;
  business_unit?: string;
  analysis_date: Date;
  analyst: string;
  status: 'completed' | 'in_progress' | 'failed' | 'archived';
  recommended_strategy: string;
  confidence_score: number;
  iteration_count: number;
  estimated_effort: string;
  estimated_timeline: string;
  estimated_cost_impact: string;
  parameters: {
    business_value: number;
    technical_complexity: number;
    migration_urgency: number;
    compliance_requirements: number;
    cost_sensitivity: number;
    risk_tolerance: number;
    innovation_priority: number;
    application_type: string;
  };
  key_factors: string[];
  next_steps: string[];
  tags?: string[];
  notes?: string;
}

interface AnalysisHistoryProps {
  analyses: AnalysisHistoryItem[];
  onExport?: (selectedIds: number[], format: 'csv' | 'pdf' | 'json') => void;
  onDelete?: (analysisId: number) => void;
  onArchive?: (analysisId: number) => void;
  onCompare?: (analysisIds: number[]) => void;
  onViewDetails?: (analysisId: number) => void;
  className?: string;
}

const strategyColors = {
  rehost: 'bg-blue-100 text-blue-800',
  replatform: 'bg-green-100 text-green-800',
  refactor: 'bg-yellow-100 text-yellow-800',
  rearchitect: 'bg-purple-100 text-purple-800',
  rewrite: 'bg-indigo-100 text-indigo-800',
  replace: 'bg-orange-100 text-orange-800',
  retire: 'bg-red-100 text-red-800'
};

const statusColors = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
  archived: 'bg-gray-100 text-gray-800'
};

const effortColors = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  very_high: 'bg-red-100 text-red-800'
};

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({
  analyses,
  onExport,
  onDelete,
  onArchive,
  onCompare,
  onViewDetails,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [strategyFilter, setStrategyFilter] = useState<string>('all');
  const [departmentFilter, setDepartmentFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('all');
  const [selectedAnalyses, setSelectedAnalyses] = useState<number[]>([]);
  const [currentTab, setCurrentTab] = useState('list');
  const [showCompareDialog, setShowCompareDialog] = useState(false);

  // Filter and search logic
  const filteredAnalyses = useMemo(() => {
    return analyses.filter(analysis => {
      const matchesSearch = !searchTerm || 
        analysis.application_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        analysis.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
        analysis.analyst.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = statusFilter === 'all' || analysis.status === statusFilter;
      const matchesStrategy = strategyFilter === 'all' || analysis.recommended_strategy === strategyFilter;
      const matchesDepartment = departmentFilter === 'all' || analysis.department === departmentFilter;

      let matchesDate = true;
      if (dateRange !== 'all') {
        const now = new Date();
        const analysisDate = new Date(analysis.analysis_date);
        switch (dateRange) {
          case 'week':
            matchesDate = (now.getTime() - analysisDate.getTime()) <= 7 * 24 * 60 * 60 * 1000;
            break;
          case 'month':
            matchesDate = (now.getTime() - analysisDate.getTime()) <= 30 * 24 * 60 * 60 * 1000;
            break;
          case 'quarter':
            matchesDate = (now.getTime() - analysisDate.getTime()) <= 90 * 24 * 60 * 60 * 1000;
            break;
        }
      }

      return matchesSearch && matchesStatus && matchesStrategy && matchesDepartment && matchesDate;
    });
  }, [analyses, searchTerm, statusFilter, strategyFilter, departmentFilter, dateRange]);

  // Get unique values for filters
  const departments = useMemo(() => 
    [...new Set(analyses.map(a => a.department))].sort(),
    [analyses]
  );

  const strategies = useMemo(() => 
    [...new Set(analyses.map(a => a.recommended_strategy))].sort(),
    [analyses]
  );

  // Analytics calculations
  const analytics = useMemo(() => {
    const total = filteredAnalyses.length;
    const completed = filteredAnalyses.filter(a => a.status === 'completed').length;
    const avgConfidence = filteredAnalyses.reduce((sum, a) => sum + a.confidence_score, 0) / total || 0;
    
    const strategyDistribution = strategies.reduce((acc, strategy) => {
      acc[strategy] = filteredAnalyses.filter(a => a.recommended_strategy === strategy).length;
      return acc;
    }, {} as Record<string, number>);

    const departmentDistribution = departments.reduce((acc, dept) => {
      acc[dept] = filteredAnalyses.filter(a => a.department === dept).length;
      return acc;
    }, {} as Record<string, number>);

    return {
      total,
      completed,
      completionRate: total > 0 ? (completed / total) * 100 : 0,
      avgConfidence: avgConfidence * 100,
      strategyDistribution,
      departmentDistribution
    };
  }, [filteredAnalyses, strategies, departments]);

  const handleSelectAnalysis = (analysisId: number) => {
    setSelectedAnalyses(prev => 
      prev.includes(analysisId) 
        ? prev.filter(id => id !== analysisId)
        : [...prev, analysisId]
    );
  };

  const handleSelectAll = () => {
    setSelectedAnalyses(
      selectedAnalyses.length === filteredAnalyses.length 
        ? [] 
        : filteredAnalyses.map(a => a.id)
    );
  };

  const handleExport = (format: 'csv' | 'pdf' | 'json') => {
    if (selectedAnalyses.length === 0) {
      toast.error('Please select analyses to export');
      return;
    }
    
    if (onExport) {
      onExport(selectedAnalyses, format);
      toast.success(`Exported ${selectedAnalyses.length} analyses as ${format.toUpperCase()}`);
    }
  };

  const handleCompare = () => {
    if (selectedAnalyses.length < 2) {
      toast.error('Please select at least 2 analyses to compare');
      return;
    }
    
    if (selectedAnalyses.length > 5) {
      toast.error('Maximum 5 analyses can be compared at once');
      return;
    }

    if (onCompare) {
      onCompare(selectedAnalyses);
      setShowCompareDialog(true);
    }
  };

  const handleBulkAction = (action: 'archive' | 'delete') => {
    if (selectedAnalyses.length === 0) {
      toast.error('Please select analyses first');
      return;
    }

    const actionText = action === 'archive' ? 'archived' : 'deleted';
    
    selectedAnalyses.forEach(id => {
      if (action === 'archive' && onArchive) {
        onArchive(id);
      } else if (action === 'delete' && onDelete) {
        onDelete(id);
      }
    });

    toast.success(`${selectedAnalyses.length} analyses ${actionText}`);
    setSelectedAnalyses([]);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setStrategyFilter('all');
    setDepartmentFilter('all');
    setDateRange('all');
  };

  const renderAnalysisRow = (analysis: AnalysisHistoryItem) => {
    const isSelected = selectedAnalyses.includes(analysis.id);
    
    return (
      <TableRow 
        key={analysis.id} 
        className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
      >
        <TableCell>
          <Checkbox 
            checked={isSelected}
            onChange={() => handleSelectAnalysis(analysis.id)}
          />
        </TableCell>
        <TableCell className="font-medium">{analysis.application_name}</TableCell>
        <TableCell>{analysis.department}</TableCell>
        <TableCell>{analysis.analyst}</TableCell>
        <TableCell>{analysis.analysis_date.toLocaleDateString()}</TableCell>
        <TableCell>
          <Badge className={statusColors[analysis.status]}>
            {analysis.status.replace('_', ' ')}
          </Badge>
        </TableCell>
        <TableCell>
          <Badge className={strategyColors[analysis.recommended_strategy as keyof typeof strategyColors]}>
            {analysis.recommended_strategy}
          </Badge>
        </TableCell>
        <TableCell>
          <div className="flex items-center space-x-1">
            <span className="text-sm">{Math.round(analysis.confidence_score * 100)}%</span>
            {analysis.confidence_score >= 0.8 && <Star className="h-3 w-3 text-yellow-500" />}
          </div>
        </TableCell>
        <TableCell>
          <Badge className={effortColors[analysis.estimated_effort as keyof typeof effortColors]}>
            {analysis.estimated_effort}
          </Badge>
        </TableCell>
        <TableCell>
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewDetails?.(analysis.id)}
            >
              <Eye className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onArchive?.(analysis.id)}
            >
              <Archive className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete?.(analysis.id)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  const renderAnalytics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Total Analyses</p>
              <p className="text-2xl font-bold">{analytics.total}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold">{Math.round(analytics.completionRate)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold">{Math.round(analytics.avgConfidence)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <Building2 className="h-4 w-4 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Departments</p>
              <p className="text-2xl font-bold">{departments.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderComparisonDialog = () => (
    <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Analysis Comparison</DialogTitle>
          <DialogDescription>
            Comparing {selectedAnalyses.length} selected analyses
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Comparison table */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-200">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left">Metric</th>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <th key={id} className="border border-gray-200 p-2 text-left">
                        {analysis?.application_name}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Strategy</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        <Badge className={strategyColors[analysis?.recommended_strategy as keyof typeof strategyColors]}>
                          {analysis?.recommended_strategy}
                        </Badge>
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Confidence</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        {Math.round((analysis?.confidence_score || 0) * 100)}%
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Effort</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        <Badge className={effortColors[analysis?.estimated_effort as keyof typeof effortColors]}>
                          {analysis?.estimated_effort}
                        </Badge>
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Timeline</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        {analysis?.estimated_timeline}
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Business Value</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        {analysis?.parameters.business_value}/10
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="border border-gray-200 p-2 font-medium">Technical Complexity</td>
                  {selectedAnalyses.slice(0, 5).map(id => {
                    const analysis = analyses.find(a => a.id === id);
                    return (
                      <td key={id} className="border border-gray-200 p-2">
                        {analysis?.parameters.technical_complexity}/10
                      </td>
                    );
                  })}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Analysis History</CardTitle>
            <CardDescription>
              View, compare, and manage your 6R analysis history
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {selectedAnalyses.length} selected
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={clearFilters}
            >
              <Filter className="h-4 w-4 mr-1" />
              Clear Filters
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={currentTab} onValueChange={setCurrentTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="list">Analysis List</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="export">Export & Actions</TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            {/* Search and Filters */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search analyses..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>

              <Select value={strategyFilter} onValueChange={setStrategyFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Strategy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Strategies</SelectItem>
                  {strategies.map(strategy => (
                    <SelectItem key={strategy} value={strategy}>
                      {strategy}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem>
                  {departments.map(dept => (
                    <SelectItem key={dept} value={dept}>
                      {dept}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue placeholder="Date Range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="week">Last Week</SelectItem>
                  <SelectItem value="month">Last Month</SelectItem>
                  <SelectItem value="quarter">Last Quarter</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Bulk Actions */}
            {selectedAnalyses.length > 0 && (
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-sm text-blue-700">
                  {selectedAnalyses.length} analyses selected
                </span>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCompare}
                    disabled={selectedAnalyses.length < 2}
                  >
                    <GitCompare className="h-4 w-4 mr-1" />
                    Compare
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('archive')}
                  >
                    <Archive className="h-4 w-4 mr-1" />
                    Archive
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleBulkAction('delete')}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            )}

            {/* Analysis Table */}
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectedAnalyses.length === filteredAnalyses.length && filteredAnalyses.length > 0}
                        onChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Application</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Analyst</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Strategy</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Effort</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAnalyses.map(renderAnalysisRow)}
                </TableBody>
              </Table>
            </div>

            {filteredAnalyses.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No analyses found matching your criteria</p>
                <Button variant="outline" size="sm" onClick={clearFilters} className="mt-2">
                  Clear Filters
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            {renderAnalytics()}
            
            {/* Strategy Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Strategy Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(analytics.strategyDistribution).map(([strategy, count]) => (
                      <div key={strategy} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge className={strategyColors[strategy as keyof typeof strategyColors]}>
                            {strategy}
                          </Badge>
                        </div>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Department Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(analytics.departmentDistribution).map(([dept, count]) => (
                      <div key={dept} className="flex items-center justify-between">
                        <span className="text-sm">{dept}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="export" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Export Options</CardTitle>
                  <CardDescription>
                    Export selected analyses in various formats
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleExport('csv')}
                      disabled={selectedAnalyses.length === 0}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      CSV
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleExport('pdf')}
                      disabled={selectedAnalyses.length === 0}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      PDF
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleExport('json')}
                      disabled={selectedAnalyses.length === 0}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      JSON
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    {selectedAnalyses.length} analyses selected for export
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Bulk Actions</CardTitle>
                  <CardDescription>
                    Perform actions on multiple analyses
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleBulkAction('archive')}
                      disabled={selectedAnalyses.length === 0}
                    >
                      <Archive className="h-4 w-4 mr-1" />
                      Archive
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => handleBulkAction('delete')}
                      disabled={selectedAnalyses.length === 0}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    Actions will be applied to {selectedAnalyses.length} selected analyses
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {renderComparisonDialog()}
      </CardContent>
    </Card>
  );
};

export default AnalysisHistory; 