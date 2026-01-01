'use client';

import React, { useRef, useEffect, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRouter } from 'next/navigation';
import { OptimizedImage } from './OptimizedImage';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { formatDistanceToNow } from 'date-fns';
import { MessageSquare, ThumbsUp, ThumbsDown, Eye, Tag } from 'lucide-react';

interface Post {
  id: string;
  title?: string;
  content: string;
  author_id: string;
  author?: {
    username: string;
    avatar_url?: string;
  };
  upvotes: number;
  downvotes: number;
  score: number;
  view_count: number;
  created_at: string;
  tags?: string[];
  comment_count?: number;
}

interface VirtualizedPostListProps {
  posts: Post[];
  currentUserId: string;
  onVote?: (postId: string, voteType: 'upvote' | 'downvote') => void;
  onViewPost?: (postId: string) => void;
  className?: string;
}

export const VirtualizedPostList: React.FC<VirtualizedPostListProps> = ({
  posts,
  currentUserId,
  onVote,
  onViewPost,
  className = ''
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const [parentHeight, setParentHeight] = useState(0);
  const router = useRouter();
  
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
    count: posts.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 250, // Estimated row height
    overscan: 5, // Number of items to render outside of the visible area
  });
  
  // Format post time
  const formatPostTime = (date: string) => {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  };
  
  // Handle post click
  const handlePostClick = (postId: string) => {
    if (onViewPost) {
      onViewPost(postId);
    } else {
      router.push(`/posts/${postId}`);
    }
  };
  
  // Handle vote
  const handleVote = (e: React.MouseEvent, postId: string, voteType: 'upvote' | 'downvote') => {
    e.stopPropagation(); // Prevent post click
    if (onVote) {
      onVote(postId, voteType);
    }
  };
  
  // Extract image URL from content if present
  const extractImageUrl = (content: string): string | null => {
    const imgRegex = /!\[.*?\]\((.*?)\)/;
    const match = content.match(imgRegex);
    return match ? match[1] : null;
  };
  
  // Truncate content for preview
  const truncateContent = (content: string, maxLength: number = 200): string => {
    // Remove image markdown
    const contentWithoutImages = content.replace(/!\[.*?\]\(.*?\)/g, '');
    
    if (contentWithoutImages.length <= maxLength) {
      return contentWithoutImages;
    }
    
    return contentWithoutImages.substring(0, maxLength) + '...';
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
          const post = posts[virtualItem.index];
          const imageUrl = extractImageUrl(post.content);
          
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
                padding: '0.5rem',
              }}
            >
              <Card 
                className="h-full cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handlePostClick(post.id)}
              >
                <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold line-clamp-2">
                      {post.title || truncateContent(post.content, 50)}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {post.author?.username || 'Anonymous'} • {formatPostTime(post.created_at)}
                    </p>
                  </div>
                  
                  <div className="flex flex-col items-center space-y-1">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="px-2 py-0 h-auto"
                      onClick={(e) => handleVote(e, post.id, 'upvote')}
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </Button>
                    <span className="text-sm font-medium">{post.score}</span>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="px-2 py-0 h-auto"
                      onClick={(e) => handleVote(e, post.id, 'downvote')}
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                
                <CardContent className="p-4 pt-2">
                  <div className="flex flex-row gap-4">
                    {imageUrl && (
                      <div className="w-24 h-24 flex-shrink-0">
                        <OptimizedImage
                          src={imageUrl}
                          alt="Post image"
                          width={96}
                          height={96}
                          className="rounded-md"
                          placeholder="blur"
                        />
                      </div>
                    )}
                    
                    <div className="flex-1">
                      <p className="text-sm line-clamp-3">
                        {truncateContent(post.content)}
                      </p>
                    </div>
                  </div>
                  
                  {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {post.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
                
                <CardFooter className="p-4 pt-2 flex justify-between text-xs text-muted-foreground">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center">
                      <MessageSquare className="h-3 w-3 mr-1" />
                      <span>{post.comment_count || 0} comments</span>
                    </div>
                    <div className="flex items-center">
                      <Eye className="h-3 w-3 mr-1" />
                      <span>{post.view_count || 0} views</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <span>
                      {post.upvotes} upvotes • {post.downvotes} downvotes
                    </span>
                  </div>
                </CardFooter>
              </Card>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VirtualizedPostList;