import React from 'react'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext';
import { useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { StarRating } from '@/components/ui/star-rating';
import { apiCall } from '@/lib/api/http';
import { usePageContext } from '@/hooks/usePageContext';

interface FeedbackFormData {
  page: string;
  rating: number;
  comment: string;
  category: string;
  breadcrumb: string;
  timestamp: string;
  user_name?: string;
}

const ChatInterface: React.FC = () => {
  const { getAuthHeaders, client, engagement, user } = useAuth();
  const { pageContext, breadcrumb, flowState } = usePageContext();

  // Feedback form state
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Submit feedback mutation
  const submitFeedback = useMutation({
    mutationFn: async (data: FeedbackFormData) => {
      try {
        return await apiCall('feedback', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(data)
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
      setFeedbackSubmitted(true);
      // Reset success message after 3 seconds
      setTimeout(() => setFeedbackSubmitted(false), 3000);
    }
  });

  const handleFeedbackSubmit = (): void => {
    if (rating === 0 || !feedbackText.trim()) return;

    // Build context-aware comment
    const contextInfo: string[] = [];
    if (pageContext?.page_name) {
      contextInfo.push(`Page: ${pageContext.page_name}`);
    }
    if (flowState?.flow_type) {
      contextInfo.push(`Flow: ${flowState.flow_type}`);
    }
    if (flowState?.current_phase) {
      contextInfo.push(`Phase: ${flowState.current_phase}`);
    }

    const enrichedComment = contextInfo.length > 0
      ? `[${contextInfo.join(' | ')}]\n\n${feedbackText}`
      : feedbackText;

    submitFeedback.mutate({
      page: pageContext?.route || window.location.pathname,
      rating,
      comment: enrichedComment,
      category: 'ai_chat',
      breadcrumb: breadcrumb || 'Chat Assistant',
      timestamp: new Date().toISOString(),
      user_name: user?.name || user?.email || undefined
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
            {feedbackSubmitted ? (
              <div className="text-center py-8">
                <div className="text-green-600 text-lg font-medium mb-2">
                  Thank you for your feedback!
                </div>
                <p className="text-sm text-gray-500">
                  Your input helps us improve the assistant.
                </p>
              </div>
            ) : (
              <>
                {/* Context indicator */}
                {pageContext && (
                  <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                    Feedback for: <span className="font-medium">{pageContext.page_name}</span>
                    {flowState?.current_phase && (
                      <span className="ml-1">({flowState.current_phase})</span>
                    )}
                  </div>
                )}

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
                    placeholder="Tell us what you think about the AI assistant..."
                    className="min-h-[100px]"
                  />
                </div>

                <Button
                  onClick={handleFeedbackSubmit}
                  disabled={rating === 0 || !feedbackText.trim() || submitFeedback.isPending}
                  className="w-full"
                >
                  {submitFeedback.isPending ? 'Submitting...' : 'Submit Feedback'}
                </Button>
              </>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};

export default ChatInterface;
