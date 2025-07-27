import React from 'react'
import { useState } from 'react'
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { StarRating } from '@/components/ui/star-rating';
import { apiCall } from '@/lib/api/http';

interface FeedbackFormData {
  page_path: string;
  rating: number;
  feedback_text: string;
}

const ChatInterface: React.FC = () => {
  const location = useLocation();
  const { getAuthHeaders, client, engagement } = useAuth();

  // Feedback form state
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');

  // Submit feedback mutation
  const submitFeedback = useMutation({
    mutationFn: async (data: FeedbackFormData) => {
      try {
        return await apiCall('feedback', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            ...data,
            client_account_id: client?.id || 'demo',
            engagement_id: engagement?.id || 'demo-engagement'
          })
        });
      } catch (error) {
        console.error('Error submitting feedback:', error);
        // In demo mode or if using demo client, just return success
        if (!client?.id || client.id === 'demo' || client.id === 'pujyam-corp') {
          return { status: 'success' };
        }
        throw error;
      }
    },
    onSuccess: () => {
      setRating(0);
      setFeedbackText('');
    }
  });

  const handleFeedbackSubmit = (): void => {
    if (rating === 0 || !feedbackText.trim()) return;

    submitFeedback.mutate({
      page_path: location.pathname,
      rating,
      feedback_text: feedbackText
    });
  };

  return (
    <Card className="fixed bottom-4 right-4 w-96 shadow-lg">
      <Tabs defaultValue="chat" className="w-full">
        <TabsList className="w-full">
          <TabsTrigger value="chat" className="w-1/2">Chat Assistant</TabsTrigger>
          <TabsTrigger value="feedback" className="w-1/2">Give Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="p-4">
          <div className="h-96 overflow-y-auto">
            {/* Chat messages will go here */}
            <p className="text-center text-gray-500">Chat functionality coming soon...</p>
          </div>
        </TabsContent>

        <TabsContent value="feedback" className="p-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Rate your experience
              </label>
              <StarRating
                value={rating}
                onChange={setRating}
                size={24}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Your feedback
              </label>
              <Textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Tell us what you think..."
                className="min-h-[100px]"
              />
            </div>

            <Button
              onClick={handleFeedbackSubmit}
              disabled={rating === 0 || !feedbackText.trim()}
              className="w-full"
            >
              Submit Feedback
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};

export default ChatInterface;
