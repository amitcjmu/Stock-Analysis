/**
 * ApplicationTable Component
 * Extracted from ApplicationSelector.tsx for modularization
 */

import React from 'react';
import { Users, Code, CheckCircle, AlertCircle, Clock, Play } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Checkbox } from '../../ui/checkbox';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import type { ApplicationTableProps } from '../types/ApplicationSelectorTypes'
import type { Application } from '../types/ApplicationSelectorTypes'

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

export const ApplicationTable: React.FC<ApplicationTableProps> = ({
  applications,
  selectedApplications,
  onSelectApplication,
  onSelectAll
}) => {
  const renderApplicationRow = (app: Application): JSX.Element => {
    const isSelected = selectedApplications.includes(app.id);

    return (
      <TableRow
        key={app.id}
        className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
        onClick={() => onSelectApplication(app.id)}
      >
        <TableCell>
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onSelectApplication(app.id)}
            onClick={(e) => e.stopPropagation()}
          />
        </TableCell>
        <TableCell className="font-medium">{app.name}</TableCell>
        <TableCell>
          <div className="flex flex-wrap gap-1">
            {(app.technology_stack || []).slice(0, 2).map(tech => (
              <Badge key={tech} variant="outline" className="text-xs">
                {tech}
              </Badge>
            ))}
            {(app.technology_stack || []).length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{(app.technology_stack || []).length - 2}
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

  return (
    <div className="border rounded-lg">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={selectedApplications.length === applications.length && applications.length > 0}
                onCheckedChange={onSelectAll}
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
          {applications.map(renderApplicationRow)}
        </TableBody>
      </Table>
    </div>
  );
};
