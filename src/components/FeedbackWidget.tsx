import React from 'react'
import type { useState } from 'react'
import type { Filter } from 'lucide-react'
import { MessageSquare, ThumbsUp, Loader2, AlertTriangle, Send, Plus } from 'lucide-react'
import { useFeedback } from '@/hooks/useFeedback';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

const FeedbackWidget = () => {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newFeedback, setNewFeedback] = useState({
    type: 'Feature' as const,
    title: '',
    description: ''
  });
  const [filter, setFilter] = useState('All');
  const [newComment, setNewComment] = useState('');
  const [activeItem, setActiveItem] = useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    error,
    createFeedback,
    isCreating,
    createError,
    voteFeedback,
    isVoting,
    voteError,
    commentFeedback,
    isCommenting,
    commentError
  } = useFeedback();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading feedback...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error loading feedback: {error?.message}</p>
        </Alert>
      </div>
    );
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createFeedback(newFeedback);
    setIsCreateOpen(false);
    setNewFeedback({ type: 'Feature', title: '', description: '' });
  };

  const handleComment = (feedbackId: string) => {
    if (newComment.trim()) {
      commentFeedback({ feedbackId, text: newComment });
      setNewComment('');
      setActiveItem(null);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'New': 'bg-blue-100 text-blue-800',
      'In Review': 'bg-yellow-100 text-yellow-800',
      'Accepted': 'bg-green-100 text-green-800',
      'Rejected': 'bg-red-100 text-red-800',
      'Implemented': 'bg-purple-100 text-purple-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getTypeColor = (type: string) => {
    const colors = {
      'Bug': 'bg-red-100 text-red-800',
      'Feature': 'bg-blue-100 text-blue-800',
      'Improvement': 'bg-green-100 text-green-800',
      'Other': 'bg-gray-100 text-gray-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const filteredItems = data.items.filter(item => 
    filter === 'All' || item.status === filter
  );

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Feedback</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.total_items}</h3>
            </div>
            <MessageSquare className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Implemented</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.implemented_items}</h3>
            </div>
            <Badge variant="success">✓</Badge>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Review</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.pending_review}</h3>
            </div>
            <Badge variant="warning">!</Badge>
          </div>
        </Card>

        <Card className="p-4">
          <div>
            <p className="text-sm font-medium text-gray-600">Top Categories</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {data.stats.top_categories.map((category, index) => (
                <Badge key={index} className={getTypeColor(category.type)}>
                  {category.type} ({category.count})
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Actions Bar */}
      <div className="flex justify-between items-center">
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button variant="primary">
              <Plus className="h-5 w-5 mr-2" />
              New Feedback
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit New Feedback</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Select
                  value={newFeedback.type}
                  onValueChange={(value) => setNewFeedback({ ...newFeedback, type: value as 'Feature' | 'Bug' | 'Improvement' | 'Other' })}
                >
                  <option value="Feature">Feature Request</option>
                  <option value="Bug">Bug Report</option>
                  <option value="Improvement">Improvement</option>
                  <option value="Other">Other</option>
                </Select>
              </div>
              <Input
                placeholder="Title"
                value={newFeedback.title}
                onChange={(e) => setNewFeedback({ ...newFeedback, title: e.target.value })}
                required
              />
              <Textarea
                placeholder="Description"
                value={newFeedback.description}
                onChange={(e) => setNewFeedback({ ...newFeedback, description: e.target.value })}
                required
                rows={4}
              />
              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreating}>
                  {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Submit'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        <Select value={filter} onValueChange={setFilter}>
          <option value="All">All Status</option>
          <option value="New">New</option>
          <option value="In Review">In Review</option>
          <option value="Accepted">Accepted</option>
          <option value="Rejected">Rejected</option>
          <option value="Implemented">Implemented</option>
        </Select>
      </div>

      {/* Feedback List */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <Card key={item.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Badge className={getTypeColor(item.type)}>{item.type}</Badge>
                  <Badge className={getStatusColor(item.status)}>{item.status}</Badge>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{item.title}</h3>
                <p className="text-gray-600 mt-2">{item.description}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => voteFeedback(item.id)}
                disabled={isVoting || item.user_has_voted}
                className={item.user_has_voted ? 'bg-blue-50' : ''}
              >
                <ThumbsUp className={`h-4 w-4 mr-2 ${item.user_has_voted ? 'text-blue-600' : ''}`} />
                {item.votes}
              </Button>
            </div>

            {/* Comments Section */}
            <div className="mt-4 space-y-4">
              {item.comments.map((comment) => (
                <div key={comment.id} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{comment.user.name}</span>
                      <Badge variant="outline">{comment.user.role}</Badge>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(comment.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-700">{comment.text}</p>
                </div>
              ))}

              {activeItem === item.id ? (
                <div className="flex space-x-2">
                  <Input
                    placeholder="Add a comment..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                  />
                  <Button
                    onClick={() => handleComment(item.id)}
                    disabled={isCommenting || !newComment.trim()}
                  >
                    {isCommenting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setActiveItem(item.id)}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Add Comment
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Error States */}
      {createError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error creating feedback: {createError.message}</p>
        </Alert>
      )}
      {voteError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error voting on feedback: {voteError.message}</p>
        </Alert>
      )}
      {commentError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error adding comment: {commentError.message}</p>
        </Alert>
      )}
    </div>
  );
};

export default FeedbackWidget;
