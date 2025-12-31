'use client';

import React, { useState, useEffect } from 'react';
import { useUser } from '@/hooks/useUser';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Send, Bot, Search, RefreshCw, Sparkles } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';
import apiClient from '@/lib/api';

interface QAComponentProps {
  groupId: number;
  communityId?: number;
  className?: string;
}

interface QuestionHistory {
  id: string;
  question: string;
  answer: string;
  source: string;
  timestamp: string;
  sources?: Array<{
    type: string;
    id: number;
    content: string;
    created_at: string;
  }>;
}

export const QAComponent: React.FC<QAComponentProps> = ({ 
  groupId, 
  communityId, 
  className 
}) => {
  const { user } = useUser();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [questionHistory, setQuestionHistory] = useState<QuestionHistory[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('ai_model');
  const [useCache, setUseCache] = useState(true);

  // Load question history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem(`qa_history_${groupId}`);
    if (savedHistory) {
      try {
        setQuestionHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Failed to parse question history:', error);
      }
    }
  }, [groupId]);

  const saveQuestionHistory = (history: QuestionHistory[]) => {
    localStorage.setItem(`qa_history_${groupId}`, JSON.stringify(history));
    setQuestionHistory(history);
  };

  const askQuestion = async () => {
    if (!question.trim() || !user) {
      toast({
        title: "Please sign in",
        description: "You need to be signed in to ask questions.",
      });
      return;
    }

    if (question.length < 2) {
      toast({
        title: "Question too short",
        description: "Please enter a question with at least 2 characters.",
      });
      return;
    }

    setIsLoading(true);
    setAnswer('');

    try {
      const data = await apiClient.askQuestion({
        question: question.trim(),
        group_id: groupId,
        community_id: communityId,
        use_cache: useCache,
        context_type: selectedSource,
      });

      if (data.success) {
        const newHistory: QuestionHistory = {
          id: Date.now().toString(),
          question: question.trim(),
          answer: data.answer,
          source: data.source,
          timestamp: new Date().toISOString(),
          sources: data.sources,
        };

        const updatedHistory = [newHistory, ...questionHistory.slice(0, 9)]; // Keep last 10 questions
        saveQuestionHistory(updatedHistory);

        setAnswer(data.answer);
        setQuestion('');
        
        toast({
          title: "Answer generated successfully",
          description: `Source: ${data.source}`,
        });
      } else {
        throw new Error(data.error || 'Failed to generate answer');
      }
    } catch (error) {
      console.error('Failed to ask question:', error);
      toast({
        title: "Error",
        description: "Failed to generate answer. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const searchContent = async () => {
    if (!question.trim()) return;

    setIsSearching(true);
    setSearchResults([]);

    try {
      const data = await apiClient.searchContent({
        query: question.trim(),
        group_id: groupId,
        community_id: communityId,
        limit: 10,
      });

      if (data.success) {
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error('Failed to search content:', error);
      toast({
        title: "Search failed",
        description: "Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const loadHistoryQuestion = (history: QuestionHistory) => {
    setQuestion(history.question);
    setAnswer(history.answer);
  };

  const clearHistory = () => {
    saveQuestionHistory([]);
    toast({
      title: "History cleared",
      description: "Your question history has been cleared.",
    });
  };

  const formatTime = (dateString: string) => {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Question Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bot className="h-5 w-5" />
            <span>Ask AI Assistant</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  askQuestion();
                }
              }}
              placeholder="Ask a question about visa processes, community discussions, or search for information..."
              className="flex-1"
            />
            <Button onClick={askQuestion} disabled={isLoading || !question.trim()}>
              <Send className="h-4 w-4 mr-2" />
              {isLoading ? 'Thinking...' : 'Ask'}
            </Button>
          </div>

          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useCache}
                onChange={(e) => setUseCache(e.target.checked)}
              />
              <span>Use cached answers</span>
            </label>
            
            <div className="flex items-center space-x-2">
              <span>Context:</span>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="full">Full context</option>
                <option value="summary">Summary only</option>
              </select>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={searchContent}
              disabled={isSearching || !question.trim()}
            >
              <Search className="h-4 w-4 mr-2" />
              {isSearching ? 'Searching...' : 'Search Content'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Answer Display */}
      {answer && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <span>AI Answer</span>
              <Badge variant="secondary">{selectedSource}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              {answer.split('\n').map((paragraph, index) => (
                <p key={index} className="mb-2">
                  {paragraph}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5" />
              <span>Search Results</span>
              <Badge variant="outline">{searchResults.length} results</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-3">
                {searchResults.map((result, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="secondary">{result.type}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatTime(result.created_at)}
                      </span>
                    </div>
                    <p className="text-sm">{result.content}</p>
                    {result.author_id && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Author: {result.author_id}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Question History */}
      {questionHistory.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <RefreshCw className="h-5 w-5" />
              <span>Recent Questions</span>
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={clearHistory}
              className="text-xs"
            >
              Clear History
            </Button>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48">
              <div className="space-y-2">
                {questionHistory.map((history) => (
                  <div
                    key={history.id}
                    className="border rounded-lg p-3 hover:bg-accent cursor-pointer"
                    onClick={() => loadHistoryQuestion(history)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{history.question}</span>
                      <Badge variant="outline" className="text-xs">
                        {history.source}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatTime(history.timestamp)}
                    </p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
};