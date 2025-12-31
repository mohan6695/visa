// Chat-related TypeScript interfaces

export interface Message {
  id: number;
  content: string;
  content_html?: string;
  user_id: number;
  group_id: number;
  message_type: 'text' | 'image' | 'file';
  status: 'published' | 'edited' | 'deleted';
  like_count: number;
  created_at: string;
  updated_at: string;
  user?: {
    username: string;
    avatar_url?: string;
  };
}

export interface UserPresence {
  user_id: number;
  group_id: number;
  last_seen: string;
  username?: string;
  avatar_url?: string;
}

export interface TypingIndicator {
  user_id: number;
  username: string;
  timestamp: string;
}

export interface ChatState {
  messages: Message[];
  onlineUsers: UserPresence[];
  typingUsers: TypingIndicator[];
  isLoading: boolean;
  isConnected: boolean;
}

export interface SendMessageRequest {
  content: string;
  group_id: number;
  message_type?: 'text' | 'image' | 'file';
}

export interface SendMessageResponse {
  success: boolean;
  message?: Message;
  error?: string;
}

export interface LoadMessagesRequest {
  group_id: number;
  limit?: number;
  offset?: number;
}

export interface LoadMessagesResponse {
  success: boolean;
  messages: Message[];
  total: number;
  has_more: boolean;
}

export interface AIQuestionRequest {
  question: string;
  group_id: number;
  community_id?: number;
  use_cache?: boolean;
  context_type?: 'full' | 'summary';
}

export interface AIQuestionResponse {
  success: boolean;
  answer: string;
  source: 'cache' | 'ai_model' | 'no_context' | 'error';
  sources?: Array<{
    type: string;
    id: number;
    content: string;
    created_at: string;
  }>;
  cached_at?: string;
  timestamp?: string;
}

export interface SemanticSearchRequest {
  query: string;
  group_id: number;
  community_id?: number;
  limit?: number;
}

export interface SemanticSearchResponse {
  success: boolean;
  results: Array<{
    type: 'post' | 'comment' | 'message';
    id: number;
    content: string;
    author_id: number;
    community_id: number;
    created_at: string;
    distance: number;
  }>;
  query: string;
  total: number;
}

export interface ThreadSummaryRequest {
  group_id: number;
  thread_content: Array<{
    type: string;
    content: string;
    created_at: string;
  }>;
  summary_type?: 'concise' | 'detailed';
}

export interface ThreadSummaryResponse {
  success: boolean;
  summary: string;
  group_id: number;
  summary_type: string;
}

export interface CacheStatusRequest {
  group_id: number;
  question: string;
}

export interface CacheStatusResponse {
  success: boolean;
  is_cached: boolean;
  cached_answer?: any;
}

export interface CostEstimateRequest {
  prompt_tokens: number;
  response_tokens: number;
}

export interface CostEstimateResponse {
  success: boolean;
  estimated_cost: number;
  prompt_tokens: number;
  response_tokens: number;
  provider: string;
}

export interface AIProvider {
  name: string;
  description: string;
  models: string[];
}

export interface AIProvidersResponse {
  success: boolean;
  providers: AIProvider[];
  current_provider: string;
}