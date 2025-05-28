import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Checkbox } from '../ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { 
  Search, 
  Filter, 
  Plus, 
  Minus, 
  Play, 
  Pause,
  Trash2,
  Download,
  Upload,
  Settings,
  Info,
  CheckCircle,
  Clock,
  AlertCircle,
  Database,
  Server,
  Code,
  Users
} from 'lucide-react';
import { toast } from 'sonner';

export interface Application {
  id: number;
  name: string;
  description?: string;
  technology_stack: string[];
  department: string;
  business_unit?: string;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  complexity_score?: number;
  user_count?: number;
  data_volume?: string;
  compliance_requirements?: string[];
  dependencies?: string[];
  last_updated?: Date;
  analysis_status?: 'not_analyzed' | 'in_progress' | 'completed' | 'failed';
  recommended_strategy?: string;
  confidence_score?: number;
}

export interface AnalysisQueue {
  id: string;
  name: string;
  applications: number[];
  status: 'pending' | 'in_progress' | 'completed' | 'paused';
  created_at: Date;
  priority: number;
  estimated_duration?: number;
}

interface ApplicationSelectorProps {
  applications: Application[];
  selectedApplications: number[];
  onSelectionChange: (selectedIds: number[]) => void;
  onStartAnalysis: (applicationIds: number[], queueName?: string) => void;
  analysisQueues?: AnalysisQueue[];
  onQueueAction?: (queueId: string, action: 'start' | 'pause' | 'cancel') => void;
  maxSelections?: number;
  showQueue?: boolean;
  className?: string;
}

const criticalityColors = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
};

const analysisStatusColors = {
  not_analyzed: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800'
};

const analysisStatusIcons = {
  not_analyzed: <Clock className="h-3 w-3" />,
  in_progress: <Play className="h-3 w-3" />,
  completed: <CheckCircle className="h-3 w-3" />,
  failed: <AlertCircle className="h-3 w-3" />
};

export const ApplicationSelector: React.FC<ApplicationSelectorProps> = ({
  applications,
  selectedApplications,
  onSelectionChange,
  onStartAnalysis,
  analysisQueues = [],
  onQueueAction,
  maxSelections = 50,
  showQueue = true,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState<string>('all');
  const [criticalityFilter, setCriticalityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [technologyFilter, setTechnologyFilter] = useState<string>('all');
  const [currentTab, setCurrentTab] = useState('applications');
  const [queueName, setQueueName] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Get unique filter values
  const departments = useMemo(() => 
    [...new Set(applications.map(app => app.department))].sort(),
    [applications]
  );

  const technologies = useMemo(() => 
    [...new Set(applications.flatMap(app => app.technology_stack))].sort(),
    [applications]
  );

  // Filter applications
  const filteredApplications = useMemo(() => {
    return applications.filter(app => {
      const matchesSearch = !searchTerm || 
        app.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.technology_stack.some(tech => tech.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesDepartment = departmentFilter === 'all' || app.department === departmentFilter;
      const matchesCriticality = criticalityFilter === 'all' || app.criticality === criticalityFilter;
      const matchesStatus = statusFilter === 'all' || app.analysis_status === statusFilter;
      const matchesTechnology = technologyFilter === 'all' || 
        app.technology_stack.includes(technologyFilter);

      return matchesSearch && matchesDepartment && matchesCriticality && 
             matchesStatus && matchesTechnology;
    });
  }, [applications, searchTerm, departmentFilter, criticalityFilter, statusFilter, technologyFilter]);

  const handleSelectAll = () => {
    const allIds = filteredApplications.map(app => app.id);
    const newSelection = selectedApplications.length === allIds.length ? [] : allIds;
    onSelectionChange(newSelection.slice(0, maxSelections));
  };

  const handleSelectApplication = (appId: number) => {
    const newSelection = selectedApplications.includes(appId)
      ? selectedApplications.filter(id => id !== appId)
      : [...selectedApplications, appId].slice(0, maxSelections);
    
    onSelectionChange(newSelection);
  };

  const handleStartAnalysis = () => {
    if (selectedApplications.length === 0) {
      toast.error('Please select at least one application');
      return;
    }

    const finalQueueName = queueName || `Analysis ${new Date().toLocaleString()}`;
    onStartAnalysis(selectedApplications, finalQueueName);
    setQueueName('');
    toast.success(`Started analysis for ${selectedApplications.length} applications`);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDepartmentFilter('all');
    setCriticalityFilter('all');
    setStatusFilter('all');
    setTechnologyFilter('all');
  };

  const renderApplicationRow = (app: Application) => {
    const isSelected = selectedApplications.includes(app.id);
    
    return (
      <TableRow 
        key={app.id} 
        className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
        onClick={() => handleSelectApplication(app.id)}
      >
        <TableCell>
          <Checkbox 
            checked={isSelected}
            onChange={() => handleSelectApplication(app.id)}
          />
        </TableCell>
        <TableCell className="font-medium">{app.name}</TableCell>
        <TableCell>
          <div className="flex flex-wrap gap-1">
            {app.technology_stack.slice(0, 2).map(tech => (
              <Badge key={tech} variant="outline" className="text-xs">
                {tech}
              </Badge>
            ))}
            {app.technology_stack.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{app.technology_stack.length - 2}
              </Badge>
            )}
          </div>
        </TableCell>
        <TableCell>{app.department}</TableCell>
        <TableCell>
          <Badge className={criticalityColors[app.criticality]}>
            {app.criticality}
          </Badge>
        </TableCell>
        <TableCell>
          {app.analysis_status && (
            <div className="flex items-center space-x-1">
              {analysisStatusIcons[app.analysis_status]}
              <Badge className={analysisStatusColors[app.analysis_status]}>
                {app.analysis_status.replace('_', ' ')}
              </Badge>
            </div>
          )}
        </TableCell>
        <TableCell>
          {app.recommended_strategy && (
            <div className="flex items-center space-x-1">
              <Badge variant="outline">{app.recommended_strategy}</Badge>
              {app.confidence_score && (
                <span className="text-xs text-gray-500">
                  ({Math.round(app.confidence_score * 100)}%)
                </span>
              )}
            </div>
          )}
        </TableCell>
        <TableCell>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            {app.user_count && (
              <div className="flex items-center space-x-1">
                <Users className="h-3 w-3" />
                <span>{app.user_count}</span>
              </div>
            )}
            {app.complexity_score && (
              <div className="flex items-center space-x-1">
                <Code className="h-3 w-3" />
                <span>{app.complexity_score}/10</span>
              </div>
            )}
          </div>
        </TableCell>
      </TableRow>
    );
  };

  const renderQueueItem = (queue: AnalysisQueue) => {
    const queueApplications = applications.filter(app => queue.applications.includes(app.id));
    
    return (
      <div key={queue.id} className="p-4 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="font-medium">{queue.name}</h4>
            <p className="text-sm text-gray-600">
              {queue.applications.length} applications • Created {queue.created_at.toLocaleDateString()}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={queue.status === 'completed' ? 'default' : 'secondary'}>
              {queue.status}
            </Badge>
            {onQueueAction && (
              <div className="flex space-x-1">
                {queue.status === 'pending' && (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => onQueueAction(queue.id, 'start')}
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                )}
                {queue.status === 'in_progress' && (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => onQueueAction(queue.id, 'pause')}
                  >
                    <Pause className="h-3 w-3" />
                  </Button>
                )}
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => onQueueAction(queue.id, 'cancel')}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {queueApplications.slice(0, 3).map(app => (
              <Badge key={app.id} variant="outline" className="text-xs">
                {app.name}
              </Badge>
            ))}
            {queueApplications.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{queueApplications.length - 3} more
              </Badge>
            )}
          </div>
          
          {queue.estimated_duration && (
            <div className="text-xs text-gray-500">
              Estimated duration: {Math.round(queue.estimated_duration / 60)} minutes
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold">Application Selection</CardTitle>
            <CardDescription>
              Select applications for 6R migration strategy analysis
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {selectedApplications.length}/{maxSelections} selected
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              <Filter className="h-4 w-4 mr-1" />
              Filters
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Search and Filters */}
        <div className="space-y-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search applications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Departments</SelectItem>
                {departments.map(dept => (
                  <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {showAdvancedFilters && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <Select value={criticalityFilter} onValueChange={setCriticalityFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Criticality" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Criticality</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Analysis Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="not_analyzed">Not Analyzed</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>

              <Select value={technologyFilter} onValueChange={setTechnologyFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Technology" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Technologies</SelectItem>
                  {technologies.map(tech => (
                    <SelectItem key={tech} value={tech}>{tech}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="md:col-span-3 flex justify-end">
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  Clear Filters
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="applications">
              Applications ({filteredApplications.length})
            </TabsTrigger>
            {showQueue && (
              <TabsTrigger value="queue">
                Analysis Queue ({analysisQueues.length})
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="applications" className="space-y-4">
            {/* Selection Actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                >
                  {selectedApplications.length === filteredApplications.length ? (
                    <>
                      <Minus className="h-4 w-4 mr-1" />
                      Deselect All
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-1" />
                      Select All
                    </>
                  )}
                </Button>
                {selectedApplications.length > 0 && (
                  <span className="text-sm text-gray-600">
                    {selectedApplications.length} applications selected
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </Button>
                <Button variant="outline" size="sm">
                  <Upload className="h-4 w-4 mr-1" />
                  Import
                </Button>
              </div>
            </div>

            {/* Applications Table */}
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox 
                        checked={selectedApplications.length === filteredApplications.length && filteredApplications.length > 0}
                        onChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Application</TableHead>
                    <TableHead>Technology</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Criticality</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Recommendation</TableHead>
                    <TableHead>Metrics</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredApplications.map(renderApplicationRow)}
                </TableBody>
              </Table>
            </div>

            {filteredApplications.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No applications found matching your criteria</p>
                <Button variant="outline" size="sm" onClick={clearFilters} className="mt-2">
                  Clear Filters
                </Button>
              </div>
            )}
          </TabsContent>

          {showQueue && (
            <TabsContent value="queue" className="space-y-4">
              <div className="space-y-4">
                {analysisQueues.map(renderQueueItem)}
                
                {analysisQueues.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No analysis queues found</p>
                  </div>
                )}
              </div>
            </TabsContent>
          )}
        </Tabs>

        {/* Analysis Actions */}
        {selectedApplications.length > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <Input
                  placeholder="Analysis queue name (optional)"
                  value={queueName}
                  onChange={(e) => setQueueName(e.target.value)}
                />
              </div>
              <Button onClick={handleStartAnalysis} className="bg-blue-600 hover:bg-blue-700">
                <Play className="h-4 w-4 mr-2" />
                Start Analysis ({selectedApplications.length})
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ApplicationSelector; 