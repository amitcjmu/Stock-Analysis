import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Brain, Database, Share2 } from 'lucide-react';
import type { MemoryAnalytics } from '../../types';

interface MemoryTabProps {
  memoryAnalytics: MemoryAnalytics | null;
}

export const MemoryTab: React.FC<MemoryTabProps> = ({ memoryAnalytics }) => {
  if (!memoryAnalytics) {
    return (
      <div className="text-center py-8 text-gray-500">
        No memory analytics available yet
      </div>
    );
  }

  const workingMemoryUsage = Math.round(
    (memoryAnalytics.working_memory.used / memoryAnalytics.working_memory.total) * 100
  );
  const longTermMemoryUsage = Math.round(
    (memoryAnalytics.long_term_memory.used / memoryAnalytics.long_term_memory.total) * 100
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Working Memory */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Working Memory
            </CardTitle>
            <CardDescription>
              Active agent memory for current operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Usage</span>
                  <span className="text-sm font-medium">{workingMemoryUsage}%</span>
                </div>
                <Progress value={workingMemoryUsage} className="h-2" />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Used</span>
                  <p className="font-medium">{memoryAnalytics.working_memory.used} MB</p>
                </div>
                <div>
                  <span className="text-gray-600">Entries</span>
                  <p className="font-medium">{memoryAnalytics.working_memory.entries}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Long-term Memory */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Long-term Memory
            </CardTitle>
            <CardDescription>
              Persistent knowledge base
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Usage</span>
                  <span className="text-sm font-medium">{longTermMemoryUsage}%</span>
                </div>
                <Progress value={longTermMemoryUsage} className="h-2" />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Used</span>
                  <p className="font-medium">{memoryAnalytics.long_term_memory.used} MB</p>
                </div>
                <div>
                  <span className="text-gray-600">Knowledge Items</span>
                  <p className="font-medium">{memoryAnalytics.long_term_memory.knowledge_items}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Shared Context */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Shared Context
          </CardTitle>
          <CardDescription>
            Cross-crew memory sharing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-600">Cross-crew Items</span>
              <p className="text-2xl font-bold text-purple-600">
                {memoryAnalytics.shared_context.cross_crew_items}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Utilization Rate</span>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-green-600">
                  {memoryAnalytics.shared_context.utilization_rate}%
                </p>
                <Badge variant="secondary">Active</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
