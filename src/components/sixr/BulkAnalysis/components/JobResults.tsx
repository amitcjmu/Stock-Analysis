import React from 'react';
import { 
  BarChart3, 
  Download, 
  FileText,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../ui/card';
import { Button } from '../../../ui/button';
import { Badge } from '../../../ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../ui/select';
import type { BulkAnalysisResult, BulkAnalysisSummary } from '../types';
import { strategyColors } from '../utils/analysisUtils';

interface JobResultsProps {
  results: BulkAnalysisResult[];
  summary: BulkAnalysisSummary;
  selectedJobId?: string;
  onExportResults: (jobId: string, format: 'csv' | 'json' | 'excel') => void;
}

export const JobResults: React.FC<JobResultsProps> = ({
  results,
  summary,
  selectedJobId,
  onExportResults
}) => {
  const [exportFormat, setExportFormat] = React.useState<'csv' | 'json' | 'excel'>('csv');

  const jobResults = selectedJobId 
    ? results.filter(r => r.job_id === selectedJobId)
    : results;

  const getResultIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'skipped':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Calculate summary stats for displayed results
  const resultStats = React.useMemo(() => {
    const completed = jobResults.filter(r => r.status === 'completed').length;
    const failed = jobResults.filter(r => r.status === 'failed').length;
    const skipped = jobResults.filter(r => r.status === 'skipped').length;
    const avgConfidence = jobResults
      .filter(r => r.status === 'completed')
      .reduce((sum, r) => sum + r.confidence_score, 0) / completed || 0;
    const avgProcessingTime = jobResults
      .reduce((sum, r) => sum + r.processing_time, 0) / jobResults.length || 0;

    return {
      total: jobResults.length,
      completed,
      failed,
      skipped,
      avgConfidence,
      avgProcessingTime
    };
  }, [jobResults]);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resultStats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{resultStats.completed}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{resultStats.failed}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getConfidenceColor(resultStats.avgConfidence)}`}>
              {(resultStats.avgConfidence * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {resultStats.avgProcessingTime.toFixed(1)}s
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Analysis Results</span>
              </CardTitle>
              <CardDescription>
                {selectedJobId 
                  ? `Results for job ${selectedJobId}`
                  : 'All analysis results across jobs'
                }
              </CardDescription>
            </div>
            
            {selectedJobId && (
              <div className="flex items-center space-x-2">
                <Select value={exportFormat} onValueChange={(value: unknown) => setExportFormat(value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="excel">Excel</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button
                  size="sm"
                  onClick={() => onExportResults(selectedJobId, exportFormat)}
                  className="flex items-center space-x-2"
                >
                  <Download className="h-4 w-4" />
                  <span>Export</span>
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {jobResults.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Available</h3>
              <p className="text-gray-600">
                {selectedJobId 
                  ? 'This job has not produced any results yet.'
                  : 'No analysis results to display.'
                }
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Application</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Recommended Strategy</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Processing Time</TableHead>
                  <TableHead>Iterations</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobResults.map((result, index) => (
                  <TableRow key={`${result.job_id}-${result.application_id}-${index}`}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{result.application_name}</div>
                        <div className="text-sm text-gray-600">ID: {result.application_id}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getResultIcon(result.status)}
                        <span className="capitalize">{result.status}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {result.status === 'completed' ? (
                        <Badge className={strategyColors[result.recommended_strategy] || 'bg-gray-100 text-gray-800'}>
                          {result.recommended_strategy}
                        </Badge>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {result.status === 'completed' ? (
                        <span className={`font-medium ${getConfidenceColor(result.confidence_score)}`}>
                          {(result.confidence_score * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{result.processing_time.toFixed(1)}s</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{result.iteration_count}</span>
                    </TableCell>
                    <TableCell>
                      {result.error_message ? (
                        <div className="max-w-xs">
                          <span className="text-sm text-red-600 truncate" title={result.error_message}>
                            {result.error_message}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};