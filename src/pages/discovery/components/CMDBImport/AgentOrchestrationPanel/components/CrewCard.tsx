import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Users } from 'lucide-react';
import type { CrewProgress } from '../types';
import { getStatusBadgeVariant } from '../utils'
import { getStatusIconWithStyles, getCrewStatusStyles, getIconContainerStyles, formatStatusText } from '../utils'

interface CrewCardProps {
  crew: CrewProgress;
}

export const CrewCard: React.FC<CrewCardProps> = ({ crew }) => (
  <Card className={`transition-all duration-300 ${getCrewStatusStyles(crew.status)}`}>
    <CardHeader className="pb-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${getIconContainerStyles(crew.status)}`}>
            {crew.icon}
          </div>
          <div>
            <CardTitle className="text-lg">{crew.name}</CardTitle>
            <CardDescription className="text-sm mt-1">
              {crew.description}
            </CardDescription>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusIconWithStyles(crew.status)}
          <Badge variant={getStatusBadgeVariant(crew.status)}>
            {formatStatusText(crew.status)}
          </Badge>
        </div>
      </div>
    </CardHeader>

    <CardContent className="pt-0">
      <div className="space-y-4">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Progress</span>
            <span>{crew.progress}%</span>
          </div>
          <Progress value={crew.progress} className="h-2" />
        </div>

        {/* Current Task */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-1">Current Task:</p>
          <p className="text-sm text-gray-600">{crew.currentTask}</p>
        </div>

        {/* Agents */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Agents:</p>
          <div className="flex flex-wrap gap-2">
            {crew.agents.map((agent, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                <Users className="h-3 w-3 mr-1" />
                {agent.name}
              </Badge>
            ))}
          </div>
        </div>

        {/* Results (if available) */}
        {crew.results && crew.status === 'completed' && (
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <p className="text-sm font-medium text-green-800 mb-1">Results:</p>
            <div className="text-sm text-green-700 space-y-1">
              {crew.results.records_processed && (
                <p>• Records processed: {crew.results.records_processed}</p>
              )}
              {crew.results.assets_classified && (
                <p>• Assets classified: {crew.results.assets_classified}</p>
              )}
              {crew.results.fields_mapped && (
                <p>• Fields mapped: {crew.results.fields_mapped}</p>
              )}
              {crew.results.quality_score && (
                <p>• Quality score: {(crew.results.quality_score * 100).toFixed(1)}%</p>
              )}
            </div>
          </div>
        )}

        {/* Error (if failed) */}
        {crew.status === 'failed' && crew.results?.error && (
          <div className="bg-red-50 p-3 rounded-lg border border-red-200">
            <p className="text-sm font-medium text-red-800 mb-1">Error:</p>
            <p className="text-sm text-red-700">{crew.results.error}</p>
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);
