"use client"

import { useState, useEffect } from 'react'

// Simple types for our posts
interface Post {
  id: string
  title: string
  content: string
  author_name: string
  upvotes: number
  downvotes: number
  score: number
  comment_count: number
  cluster_name: string
  cluster_keywords: string[]
  similarity_score: number
  created_at: string
}

// Mock data for demonstration
const mockPosts: Post[] = [
  {
    id: '1',
    title: 'H1B pending for long time - what are the options?',
    content: 'My boyfriend\'s H1B is pending for a long time, and he cannot work anymore due to that. What are the best paths he can take?',
    author_name: 'Vanessa Vega',
    upvotes: 2,
    downvotes: 0,
    score: 2,
    comment_count: 28,
    cluster_name: 'H1B Processing Issues',
    cluster_keywords: ['h1b', 'processing', 'pending'],
    similarity_score: 0.95,
    created_at: '2025-12-30T10:00:00Z'
  },
  {
    id: '2',
    title: 'H-1B and H-4 visa prudentially revoked under 221(i)',
    content: 'Both H-1B and H-4 visas were prudentially revoked under 221(i) due to a past record of the H-1B holder. Can the H-4 attend the visa interview independently?',
    author_name: 'Anonymous',
    upvotes: 2,
    downvotes: 0,
    score: 2,
    comment_count: 11,
    cluster_name: 'Visa Revocation Cases',
    cluster_keywords: ['revocation', '221i', 'h1b'],
    similarity_score: 0.92,
    created_at: '2025-12-30T09:00:00Z'
  },
  {
    id: '3',
    title: 'H1B extension stamping interview - 221(g) for social media',
    content: 'I had my H1B extension stamping interview in Chennai on December 18{