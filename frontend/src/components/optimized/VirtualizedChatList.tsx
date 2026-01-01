'use client';

import React, { useRef, useEffect, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Message } from '@/types/chat';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatDistanceToNow } from 'date-fns';
import { Clock } from 'lucide-react';

interface VirtualizedChatListProps {
  messages: Message[];
  currentUserId: string;
  className?: string;
}

export const VirtualizedChatList: React.FC<VirtualizedChatListProps> = ({
  messages,
  currentUserId,
  className = ''
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const [parentHeight, setParentHeight] = useState(0);
  
  // Update parent height on resize
  useEffect(() => {
    const updateParentHeight = () => {
      if (parentRef.current) {
        setParentHeight(parentRef.current.offsetHeight);
      }
    };
    
    // Initial height
    updateParentHeight();
    
    // Add resize listener
    window.addEventListener('resize', updateParentHeight);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', updateParentHeight);
    };
  }, []);
  
  // Create virtualizer
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Estimated row height
    overscan: 5, // Number of items to render outside of the visible area
  });
  
  // Format message time
  const formatMessageTime = (date: string) => {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  };
  
  return (
    <div 
      ref={parentRef} 
      className={`h-full overflow-auto ${className}`}
      style={{ height: '100%', position: 'relative' }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualItem) => {
          const message = messages[virtualItem.index];
          const isCurrentUser = message.user_id === currentUserId;
          
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <div
                className={`flex max-w-xs lg:max-w-md space-x-2 mb-4 ${
                  isCurrentUser ? 'flex-row-reverse space-x-reverse ml-auto' : 'flex-row'
                }`}
              >
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarImage src={message.user?.avatar_url} />
                  <AvatarFallback>
                    {message.user?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                
                <div
                  className={`px-4 py-2 rounded-lg ${
                    isCurrentUser
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card text-card-foreground'
                  }`}
                >
                  {!isCurrentUser && (
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      {message.user?.username || 'Unknown User'}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap break-words">{message.content}</div>
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
          );
        })}
      </div>
    </div>
  );
};

export default VirtualizedChatList;