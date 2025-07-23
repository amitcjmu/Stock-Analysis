import React from 'react';
import { AlertCircle, XCircle, Info } from 'lucide-react'
import { CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface DataQualityPanelProps {
  dataQuality: {
    overall_score: number;
    completeness_by_field: Record<string, number>;
    missing_critical_data: Array<{
      asset_id: string;
      asset_name: string;
      missing_fields: string[];
      completeness: number;
    }>;
  };
  className?: string;
}

const DataQualityPanel: React.FC<DataQualityPanelProps> = ({
  dataQuality,
  className = '',
}) => {
  const overallScore = Math.round(dataQuality.overall_score * 100);
  const issuesCount = dataQuality.missing_critical_data.length;
  const fieldsCount = Object.keys(dataQuality.completeness_by_field).length;
  
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 90) return 'bg-green-100';
    if (score >= 70) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getSeverity = (completeness: number) => {
    if (completeness >= 90) return 'Low';
    if (completeness >= 70) return 'Medium';
    return 'High';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'High': return 'bg-red-100 text-red-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Get top 5 fields by completeness
  const fieldCompleteness = Object.entries(dataQuality.completeness_by_field)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 5);

  // Get top 5 assets with missing data
  const problemAssets = [...dataQuality.missing_critical_data]
    .sort((a, b) => a.completeness - b.completeness)
    .slice(0, 5);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Data Quality</CardTitle>
            <CardDescription>
              {overallScore >= 90 
                ? 'Excellent data quality' 
                : overallScore >= 70 
                  ? 'Good data quality' 
                  : 'Needs improvement'}
            </CardDescription>
          </div>
          <Badge 
            className={`${getScoreBgColor(overallScore)} ${getScoreColor(overallScore)} text-sm font-medium`}
          >
            {overallScore}% Complete
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          {/* Overall Score */}
          <div>
            <div className="flex justify-between text-sm font-medium mb-1">
              <span>Overall Data Quality</span>
              <span>{overallScore}%</span>
            </div>
            <Progress value={overallScore} className="h-2" />
          </div>

          {/* Field Completeness */}
          <div>
            <h4 className="text-sm font-medium mb-2">Field Completeness</h4>
            <div className="space-y-2">
              {fieldCompleteness.map(([field, completeness]) => (
                <div key={field} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">{field}</span>
                    <span className="font-medium">{Math.round(completeness * 100)}%</span>
                  </div>
                  <Progress 
                    value={completeness * 100} 
                    className="h-1.5" 
                    indicatorClassName={completeness > 0.9 ? 'bg-green-500' : completeness > 0.7 ? 'bg-yellow-500' : 'bg-red-500'}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Critical Issues */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium">Critical Data Issues</h4>
              <Badge variant={issuesCount > 0 ? 'destructive' : 'secondary'} className="text-xs">
                {issuesCount} {issuesCount === 1 ? 'Issue' : 'Issues'}
              </Badge>
            </div>
            
            {issuesCount === 0 ? (
              <div className="flex items-center text-sm text-green-600 bg-green-50 p-3 rounded-md">
                <CheckCircle className="h-4 w-4 mr-2" />
                No critical data issues found
              </div>
            ) : (
              <div className="space-y-3">
                {problemAssets.map((asset) => (
                  <div key={asset.asset_id} className="text-sm p-3 border rounded-md">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{asset.asset_name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          Missing {asset.missing_fields.length} field{asset.missing_fields.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getSeverityColor(getSeverity(asset.completeness * 100))}`}
                      >
                        {getSeverity(asset.completeness * 100)} Severity
                      </Badge>
                    </div>
                    <div className="mt-2">
                      <div className="flex justify-between text-xs mb-1">
                        <span>Completeness</span>
                        <span>{Math.round(asset.completeness * 100)}%</span>
                      </div>
                      <Progress 
                        value={asset.completeness * 100} 
                        className="h-1.5"
                        indicatorClassName={
                          asset.completeness > 0.9 
                            ? 'bg-green-500' 
                            : asset.completeness > 0.7 
                              ? 'bg-yellow-500' 
                              : 'bg-red-500'
                        }
                      />
                    </div>
                  </div>
                ))}
                
                {issuesCount > 5 && (
                  <Button variant="ghost" size="sm" className="w-full text-sm">
                    View all {issuesCount} issues
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Data Quality Recommendations */}
          <div className="bg-blue-50 p-3 rounded-md border border-blue-100">
            <div className="flex">
              <Info className="h-4 w-4 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-blue-800">Improve Data Quality</h4>
                <p className="text-xs text-blue-700 mt-0.5">
                  {overallScore < 70 
                    ? 'Address critical issues to improve data quality and migration readiness.'
                    : overallScore < 90 
                      ? 'Your data quality is good, but there is still room for improvement.'
                      : 'Great job! Your data quality is excellent.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DataQualityPanel;
