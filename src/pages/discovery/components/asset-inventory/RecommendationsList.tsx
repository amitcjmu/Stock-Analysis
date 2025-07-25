import React from 'react';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react'
import { ArrowRight, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  category: 'data-quality' | 'security' | 'performance' | 'cost' | 'compliance';
  affected_assets: number;
  estimated_effort: string;
  impact: string;
  status: 'pending' | 'in-progress' | 'completed' | 'dismissed';
  created_at: string;
  updated_at: string;
}

interface RecommendationsListProps {
  recommendations: Recommendation[];
  maxItems?: number;
  className?: string;
}

const priorityIcons = {
  high: AlertTriangle,
  medium: AlertCircle,
  low: Info,
};

const priorityColors = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

const categoryIcons = {
  'data-quality': BarChart2,
  'security': Shield,
  'performance': Zap,
  'cost': DollarSign,
  'compliance': FileText,
};

const categoryColors = {
  'data-quality': 'bg-purple-100 text-purple-800',
  'security': 'bg-red-100 text-red-800',
  'performance': 'bg-blue-100 text-blue-800',
  'cost': 'bg-green-100 text-green-800',
  'compliance': 'bg-amber-100 text-amber-800',
};

const statusColors = {
  'pending': 'bg-gray-100 text-gray-800',
  'in-progress': 'bg-blue-100 text-blue-800',
  'completed': 'bg-green-100 text-green-800',
  'dismissed': 'bg-gray-100 text-gray-500',
};

const RecommendationsList: React.FC<RecommendationsListProps> = ({
  recommendations: initialRecommendations,
  maxItems = 5,
  className = '',
}) => {
  // Sort recommendations by priority (high to low) and then by affected assets (descending)
  const recommendations = React.useMemo(() => {
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    return [...initialRecommendations]
      .sort((a, b) => {
        if (a.priority !== b.priority) {
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        }
        return b.affected_assets - a.affected_assets;
      })
      .slice(0, maxItems);
  }, [initialRecommendations, maxItems]);

  if (recommendations.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Recommendations</CardTitle>
          <CardDescription>No active recommendations at this time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-6 text-center">
            <div className="text-center">
              <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-2" />
              <h3 className="text-sm font-medium text-gray-900">No Recommendations</h3>
              <p className="text-sm text-gray-500">Your assets are well-optimized. We'll notify you when we find ways to improve.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Recommendations</CardTitle>
            <CardDescription>
              {recommendations.length} action item{recommendations.length !== 1 ? 's' : ''} to improve your migration
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" className="text-blue-600 hover:bg-blue-50">
            View all
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="divide-y divide-gray-100">
          {recommendations.map((rec) => {
            const PriorityIcon = priorityIcons[rec.priority];
            const CategoryIcon = categoryIcons[rec.category] || Info;

            return (
              <div key={rec.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start">
                  <div className="flex-shrink-0 pt-0.5">
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center ${priorityColors[rec.priority]}`}>
                      <PriorityIcon className="h-4 w-4" />
                    </div>
                  </div>

                  <div className="ml-3 flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-gray-900">{rec.title}</h3>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusColors[rec.status]}`}>
                          {rec.status.replace('-', ' ')}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          <CategoryIcon className="h-3 w-3 mr-1" />
                          {rec.category.replace('-', ' ')}
                        </Badge>
                      </div>
                    </div>

                    <p className="mt-1 text-sm text-gray-600">{rec.description}</p>

                    <div className="mt-2 flex items-center text-xs text-gray-500 space-x-4">
                      <span className="flex items-center">
                        <Users className="h-3 w-3 mr-1 text-gray-400" />
                        {rec.affected_assets} {rec.affected_assets === 1 ? 'asset' : 'assets'}
                      </span>
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1 text-gray-400" />
                        {rec.estimated_effort}
                      </span>
                      <span className="flex items-center">
                        <Zap className="h-3 w-3 mr-1 text-gray-400" />
                        {rec.impact} impact
                      </span>
                    </div>

                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm" className="h-7 text-xs">
                          Dismiss
                        </Button>
                        <Button variant="outline" size="sm" className="h-7 text-xs">
                          View details
                        </Button>
                      </div>
                      <span className="text-xs text-gray-500">
                        Updated {new Date(rec.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {initialRecommendations.length > maxItems && (
          <div className="border-t border-gray-100 px-4 py-3 text-center">
            <Button variant="ghost" size="sm" className="text-blue-600">
              View all {initialRecommendations.length} recommendations
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RecommendationsList;
