import type React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Lightbulb, CheckCircle, AlertTriangle, Cpu, Clock } from 'lucide-react';

const InsightIcon = ({ type }): JSX.Element => {
  switch (type) {
    case 'processing':
      return <Cpu className="h-5 w-5 text-blue-500" />;
    case 'success':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'error':
      return <AlertTriangle className="h-5 w-5 text-red-500" />;
    default:
      return <Lightbulb className="h-5 w-5 text-yellow-500" />;
  }
};

const InsightBadge = ({ type }): JSX.Element => {
    switch (type) {
        case 'processing':
          return <Badge variant="secondary">Processing</Badge>;
        case 'success':
          return <Badge variant="success">Success</Badge>;
        case 'error':
          return <Badge variant="destructive">Error</Badge>;
        case 'progress':
            return <Badge variant="outline">Progress</Badge>;
        default:
          return <Badge>{type}</Badge>;
      }
}

export const AgentActivityViewer = ({ insights }): JSX.Element => {
  if (!insights || insights.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Cpu className="mr-2" />
          Agent Activity Log
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64 pr-4">
          <div className="space-y-4">
            {insights.map((insight, index) => (
              <div key={index} className="flex items-start space-x-4 p-3 bg-gray-50 rounded-lg">
                <InsightIcon type={insight.insight_type} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-gray-800">{insight.title}</p>
                    <InsightBadge type={insight.insight_type} />
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                  <div className="text-xs text-gray-400 mt-2 flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {new Date(insight.timestamp || Date.now()).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
