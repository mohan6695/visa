'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useSupabaseClient } from '@supabase/auth-helpers-react';
import { useUser } from '@/hooks/useUser';
import { Message, UserPresence } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Send, MessageCircle, Users, Clock, Eye } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface GroupChatProps {
  groupId: number;
  groupName: string;
  onBack?: () => void;
}

export const GroupChat: React.FC<GroupChatProps> = ({ groupId, groupName, onBack }) => {
  const supabase = useSupabaseClient();
  const { user } = useUser();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<UserPresence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [activeUserCount, setActiveUserCount] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load initial messages
  useEffect(() => {
    loadInitialMessages();
    setupRealtimeSubscription();
    
    return () => {
      if (supabase) {
        supabase.removeChannel(`group:${groupId}`);
      }
    };
  }, [groupId, supabase]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadInitialMessages = async () => {
    try {
      setIsLoading(true);
      
      // Load recent messages
      const { data, error } = await supabase
        .from('group_messages')
        .select(`
          *,
          user:users(username, avatar_url)
        `)
        .eq('group_id', groupId)
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) throw error;

      setMessages(data || []);
      setIsLoading(false);
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setIsLoading(false);
    }
  };

  const setupRealtimeSubscription = () => {
    if (!supabase) return;

    const channel = supabase
      .channel(`group:${groupId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'group_messages',
          filter: `group_id=eq.${groupId}`
        },
        (payload) => {
          const newMsg: Message = {
            id: payload.new.id,
            content: payload.new.content,
            content_html: payload.new.content_html,
            user_id: payload.new.user_id,
            group_id: payload.new.group_id,
            message_type: payload.new.message_type,
            status: payload.new.status,
            like_count: payload.new.like_count,
            created_at: payload.new.created_at,
            updated_at: payload.new.updated_at,
            user: payload.new.user
          };
          
          setMessages(prev => [newMsg, ...prev]);
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'group_messages',
          filter: `group_id=eq.${groupId}`
        },
        (payload) => {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === payload.new.id 
                ? { ...msg, ...payload.new }
                : msg
            )
          );
        }
      )
      .subscribe();

    return () => supabase.removeChannel(channel);
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !user) return;

    try {
      const { error } = await supabase
        .from('group_messages')
        .insert({
          content: newMessage.trim(),
          user_id: user.id,
          group_id: groupId,
          message_type: 'text'
        });

      if (error) throw error;

      setNewMessage('');
      setIsTyping(false);
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = null;
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleTyping = () => {
    if (!isTyping) {
      setIsTyping(true);
      // Send typing indicator
      supabase?.channel(`group:${groupId}`).send({
        type: 'broadcast',
        event: 'typing',
        payload: { user_id: user?.id, username: user?.user_metadata?.username }
      });
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 3000);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatMessageTime = (date: string) => {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center space-x-4">
          {onBack && (
            <Button variant="ghost" size="sm" onClick={onBack}>
              ← Back
            </Button>
          )}
          <div className="flex items-center space-x-3">
            <MessageCircle className="h-6 w-6 text-primary" />
            <div>
              <h1 className="font-semibold">{groupName}</h1>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Users className="h-4 w-4" />
                  <span>{onlineUsers.length} online</span>
                </div>
                <span>•</span>
                <div className="flex items-center space-x-1">
                  <Eye className="h-4 w-4" />
                  <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {isLoading ? (
            <div className="text-center text-muted-foreground py-8">
              Loading messages...
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No messages yet. Start the conversation!
            </div>
          ) : (
            [...messages].reverse().map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.user_id === user?.id ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`flex max-w-xs lg:max-w-md space-x-2 ${
                    message.user_id === user?.id ? 'flex-row-reverse space-x-reverse' : 'flex-row'
                  }`}
                >
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={message.user?.avatar_url} />
                    <AvatarFallback>
                      {message.user?.username?.charAt(0)?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div
                    className={`px-4 py-2 rounded-lg ${
                      message.user_id === user?.id
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-card text-card-foreground'
                    }`}
                  >
                    {message.user_id !== user?.id && (
                      <div className="text-xs font-medium text-muted-foreground mb-1">
                        {message.user?.username}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className="text-xs text-muted-foreground mt-1 flex items-center space-x-2">
                      <Clock className="h-3 w-3" />
                      <span>{formatMessageTime(message.created_at)}</span>
                      {message.like_count > 0 && (
                        <span className="ml-2">❤️ {message.like_count}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t bg-card p-4">
        <div className="flex space-x-3">
          <Input
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              handleTyping();
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Type a message..."
            className="flex-1"
          />
          <Button onClick={sendMessage} disabled={!newMessage.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        
        {isTyping && (
          <div className="text-xs text-muted-foreground mt-2">
            Typing...
          </div>
        )}
      </div>
    </div>
  );
};