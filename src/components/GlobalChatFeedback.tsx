import React, { useState } from 'react';
import { MessageSquare, Loader2, AlertTriangle, Send, Clock, Users, Bot, Reply } from 'lucide-react';
import { useGlobalChat } from '@/hooks/useGlobalChat';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Avatar } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';

const GlobalChatFeedback = () => {
  const [newMessage, setNewMessage] = useState('');
  const [replyText, setReplyText] = useState('');
  const [activeThread, setActiveThread] = useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    error,
    sendMessage,
    isSending,
    sendError,
    replyToMessage,
    isReplying,
    replyError,
    reactToMessage,
    isReacting
  } = useGlobalChat();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading chat...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error loading chat: {error?.message}</p>
        </Alert>
      </div>
    );
  }

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      sendMessage(newMessage);
      setNewMessage('');
    }
  };

  const handleReply = (messageId: string) => {
    if (replyText.trim()) {
      replyToMessage({ messageId, text: replyText });
      setReplyText('');
      setActiveThread(null);
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getMessageTypeColor = (type: string) => {
    const colors = {
      'user': 'bg-blue-100 text-blue-800',
      'agent': 'bg-purple-100 text-purple-800',
      'system': 'bg-gray-100 text-gray-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Messages</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.total_messages}</h3>
            </div>
            <MessageSquare className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.active_users}</h3>
            </div>
            <Users className="h-8 w-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Response Rate</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.response_rate}%</h3>
            </div>
            <Bot className="h-8 w-8 text-purple-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.stats.average_response_time}s</h3>
            </div>
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>
        </Card>
      </div>

      {/* Chat Area */}
      <Card className="flex-1">
        <div className="h-full flex flex-col">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {data.messages.map((message) => (
                <div key={message.id} className="space-y-2">
                  {/* Main Message */}
                  <div className="flex items-start space-x-4">
                    <Avatar>
                      <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-lg">{message.user.name[0]}</span>
                      </div>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium">{message.user.name}</span>
                        <Badge variant="outline">{message.user.role}</Badge>
                        <Badge className={getMessageTypeColor(message.type)}>{message.type}</Badge>
                        <span className="text-sm text-gray-500">{formatTime(message.created_at)}</span>
                      </div>
                      <p className="text-gray-900">{message.text}</p>
                      
                      {/* Reactions */}
                      <div className="flex items-center space-x-2 mt-2">
                        {message.reactions.map((reaction, index) => (
                          <Button
                            key={index}
                            variant="ghost"
                            size="sm"
                            onClick={() => reactToMessage({ messageId: message.id, reaction: reaction.type })}
                            disabled={isReacting || reaction.user_has_reacted}
                            className={reaction.user_has_reacted ? 'bg-gray-100' : ''}
                          >
                            {reaction.type} {reaction.count}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Thread */}
                  {message.thread && message.thread.length > 0 && (
                    <div className="ml-14 space-y-2">
                      {message.thread.map((reply) => (
                        <div key={reply.id} className="flex items-start space-x-4">
                          <Avatar>
                            <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center">
                              <span className="text-sm">{reply.user.name[0]}</span>
                            </div>
                          </Avatar>
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="font-medium text-sm">{reply.user.name}</span>
                              <Badge variant="outline" className="text-xs">{reply.user.role}</Badge>
                              <span className="text-xs text-gray-500">{formatTime(reply.created_at)}</span>
                            </div>
                            <p className="text-sm text-gray-900">{reply.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reply Input */}
                  {activeThread === message.id && (
                    <div className="ml-14 flex space-x-2">
                      <Input
                        placeholder="Reply to thread..."
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                      />
                      <Button
                        onClick={() => handleReply(message.id)}
                        disabled={isReplying || !replyText.trim()}
                      >
                        {isReplying ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  )}

                  {/* Reply Button */}
                  {activeThread !== message.id && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-14"
                      onClick={() => setActiveThread(message.id)}
                    >
                      <Reply className="h-4 w-4 mr-2" />
                      Reply
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>

          {/* Message Input */}
          <div className="p-4 border-t">
            <form onSubmit={handleSendMessage} className="flex space-x-2">
              <Input
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
              />
              <Button type="submit" disabled={isSending || !newMessage.trim()}>
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </div>
      </Card>

      {/* Error States */}
      {sendError && (
        <Alert variant="destructive" className="mt-4">
          <AlertTriangle className="h-4 w-4" />
          <p>Error sending message: {sendError.message}</p>
        </Alert>
      )}
      {replyError && (
        <Alert variant="destructive" className="mt-4">
          <AlertTriangle className="h-4 w-4" />
          <p>Error sending reply: {replyError.message}</p>
        </Alert>
      )}
    </div>
  );
};

export default GlobalChatFeedback; 