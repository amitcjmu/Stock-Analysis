import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiCall } from '@/lib/api/http';
import { StarRating } from '@/components/ui/star-rating';

interface Feedback {
  id: string;
  page_path: string;
  rating: number;
  feedback_text: string;
  status: 'needs_attention' | 'resolved';
  created_at: string;
  client_account_id: string;
  engagement_id: string;
}

interface FeedbackStats {
  total_count: number;
  average_rating: number;
  needs_attention_count: number;
  resolved_count: number;
}

const FeedbackView: React.FC = () => {
  const { getAuthHeaders, client, engagement } = useAuth();

  // Fetch feedback with React Query
  const { data: feedbackData, isLoading: feedbackLoading } = useQuery<{
    items: Feedback[];
    stats: FeedbackStats;
  }>({
    queryKey: ['feedback', client?.id],
    queryFn: async () => {
      try {
        const response = await apiCall('feedback', {
          headers: getAuthHeaders()
        });
        return response;
      } catch (error) {
        // Return demo data if API fails or if using demo client
        if (!client?.id || client.id === 'demo' || client.id === 'pujyam-corp') {
          return {
            items: [
              {
                id: 'demo-1',
                page_path: '/discovery/attribute-mapping',
                rating: 4,
                feedback_text: 'The attribute mapping interface is intuitive, but could use more examples.',
                status: 'needs_attention',
                created_at: new Date().toISOString(),
                client_account_id: client?.id || 'demo',
                engagement_id: engagement?.id || 'demo-engagement'
              },
              {
                id: 'demo-2',
                page_path: '/discovery/assessment-readiness',
                rating: 5,
                feedback_text: 'Assessment readiness checklist is very helpful.',
                status: 'resolved',
                created_at: new Date().toISOString(),
                client_account_id: client?.id || 'demo',
                engagement_id: engagement?.id || 'demo-engagement'
              }
            ],
            stats: {
              total_count: 2,
              average_rating: 4.5,
              needs_attention_count: 1,
              resolved_count: 1
            }
          };
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000 // 5 minutes
  });

  const feedback = feedbackData?.items || [];
  const stats = feedbackData?.stats || {
    total_count: 0,
    average_rating: 0,
    needs_attention_count: 0,
    resolved_count: 0
  };

  if (feedbackLoading) {
    return <div>Loading feedback...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Feedback Overview</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Total Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.total_count}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Average Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.average_rating.toFixed(1)}/5</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Needs Attention</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-yellow-600">{stats.needs_attention_count}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resolved</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">{stats.resolved_count}</p>
          </CardContent>
        </Card>
      </div>

      {/* Feedback List */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All Feedback</TabsTrigger>
          <TabsTrigger value="needs_attention">Needs Attention</TabsTrigger>
          <TabsTrigger value="resolved">Resolved</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <ScrollArea className="h-[600px]">
            <FeedbackList items={feedback} />
          </ScrollArea>
        </TabsContent>

        <TabsContent value="needs_attention">
          <ScrollArea className="h-[600px]">
            <FeedbackList
              items={feedback.filter(item => item.status === 'needs_attention')}
            />
          </ScrollArea>
        </TabsContent>

        <TabsContent value="resolved">
          <ScrollArea className="h-[600px]">
            <FeedbackList
              items={feedback.filter(item => item.status === 'resolved')}
            />
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const FeedbackList: React.FC<{ items: Feedback[] }> = ({ items }) => {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <Card key={item.id} className="w-full">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg">
                {item.page_path}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant={item.status === 'needs_attention' ? 'destructive' : 'default'}>
                  {item.status === 'needs_attention' ? 'Needs Attention' : 'Resolved'}
                </Badge>
                <div className="flex items-center gap-1">
                  <StarRating value={item.rating} readonly size={16} />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">{item.feedback_text}</p>
            <p className="text-sm text-gray-400 mt-2">
              {new Date(item.created_at).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default FeedbackView;
