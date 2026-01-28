'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useSession } from '@supabase/auth-helpers-react';
import styles from './ChatbotUI.module.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    post_id: number;
    title: string;
    relevance_score: number;
  }>;
  timestamp: Date;
  latency_ms?: number;
}

interface ChatbotUIProps {
  group_id: number;
  group_name: string;
}

export default function ChatbotUI({ group_id, group_name }: ChatbotUIProps) {
  const session = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const conversation_id = useRef(`conv_${Date.now()}`);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMessage.content,
          group_id,
          conversation_id: conversation_id.current,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get response');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
        latency_ms: data.latency_ms,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMsg);
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!session) {
    return (
      <div className={styles.container}>
        <div className={styles.loginPrompt}>
          <p>Please sign in to use the chatbot</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>{group_name} Community Assistant</h2>
        <p className={styles.subtitle}>
          Powered by AI - ask questions about posts in this group
        </p>
      </div>

      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.emptyState}>
            <h3>Welcome to {group_name} Assistant!</h3>
            <p>Ask any question about posts in this group, and I'll find the best answers from the community.</p>
            <div className={styles.exampleQuestions}>
              <p className={styles.exampleLabel}>Example questions:</p>
              <ul>
                <li>"What are best practices for database optimization?"</li>
                <li>"How do I implement authentication?"</li>
                <li>"What tools does the community recommend for X?"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`${styles.message} ${styles[message.role]}`}>
            <div className={styles.messageContent}>
              <p>{message.content}</p>

              {message.role === 'assistant' && (
                <>
                  {message.sources && message.sources.length > 0 && (
                    <div className={styles.sources}>
                      <p className={styles.sourcesLabel}>📚 Sources from community:</p>
                      <ul>
                        {message.sources.map((source) => (
                          <li key={source.post_id} className={styles.sourceItem}>
                            <a href={`/groups/${group_id}/posts/${source.post_id}`} target="_blank">
                              {source.title}
                            </a>
                            <span className={styles.relevance}>
                              {(source.relevance_score * 100).toFixed(0)}% match
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {message.latency_ms && (
                    <p className={styles.latency}>⚡ Response time: {message.latency_ms}ms</p>
                  )}
                </>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className={`${styles.message} ${styles.assistant}`}>
            <div className={styles.messageContent}>
              <div className={styles.typingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className={styles.errorMessage}>
            <p>⚠️ {error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className={styles.inputForm}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={loading ? 'Waiting for response...' : 'Ask a question...'}
          disabled={loading}
          className={styles.input}
          maxLength={500}
        />
        <button type="submit" disabled={loading || !input.trim()} className={styles.sendButton}>
          {loading ? '⏳ Sending...' : '🚀 Send'}
        </button>
      </form>

      <div className={styles.footer}>
        <p>Powered by Meilisearch + Groq RAG</p>
      </div>
    </div>
  );
}
