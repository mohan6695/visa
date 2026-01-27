'use client';

import { useState, useEffect } from 'react';
import AdBanner from './ads/AdBanner';
import AdSidebar from './ads/AdSidebar';

interface Post {
  id: string;
  title: string;
  content: string;
  author_id: string | null;
  group_id: string | null;
  score: number;
  view_count: number;
  is_answered: boolean;
  created_at: string;
  rrf_score?: number;
  source?: string;
}

const USA_GROUP_ID = "550e8400-e29b-41d4-a716-446655440001";

export default function USAPostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [postCount, setPostCount] = useState('Loading...');
  const [latency, setLatency] = useState<number | null>(null);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const fetchPosts = async (query = '') => {
    setLoading(true);
    setPostCount('Loading...');

    try {
      const startTime = performance.now();
      const response = await fetch(`/api/v1/sidebar/search?q=${encodeURIComponent(query)}&group_id=${USA_GROUP_ID}&limit=12`);
      const data = await response.json();
      const endTime = performance.now();
      const newLatency = endTime - startTime;

      setPosts(data.posts || []);
      setLatency(newLatency);
      setPostCount(`${data.posts?.length || 0} posts ${newLatency ? `<span class="text-green-600 ml-2">(${newLatency.toFixed(0)}ms)</span>` : ''}`);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setPosts([]);
      setPostCount('Error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPosts(searchQuery);
  };

  const showPostDetails = (postId: string) => {
    window.location.href = `/post/${postId}`;
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <AdSidebar slotId="left-sidebar-usa" position="left" />
      <AdSidebar slotId="right-sidebar-usa" position="right" />
      <AdBanner slotId="top-banner-usa" format="horizontal" className="w-full mb-8" />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">USA Visa Posts</h2>
            <div className="text-sm text-gray-600" dangerouslySetInnerHTML={{ __html: postCount }} />
          </div>
          
          <form className="flex gap-2 mb-6" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search posts... (H1B, OPT, visa stamping...)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
              Search
            </button>
          </form>
          
          <div className="space-y-6">
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading posts...</p>
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No posts found. Try a different search.</p>
              </div>
            ) : (
              <>
                {posts.slice(0, 3).map((post, index) => (
                  <div key={post.id} className="bg-gradient-to-r from-blue-50 to-white rounded-lg border border-blue-200 p-6">
                    <div className="flex items-start space-x-4">
                      <div className="flex flex-col items-center">
                        <button className="text-blue-600 hover:text-green-600">
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path>
                          </svg>
                        </button>
                        <span className="text-lg font-semibold text-blue-700">{post.score}</span>
                        <button className="text-blue-600 hover:text-red-600">
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                          </svg>
                        </button>
                      </div>
                      <div className="flex-1">
                        <span className="inline-block bg-blue-600 text-white text-xs px-2 py-1 rounded mb-2">Answer {index + 1}</span>
                        <h3 className="font-semibold text-gray-900 text-lg">{post.title || 'No title'}</h3>
                        <p className="text-sm text-gray-600 mb-3">{formatDate(post.created_at)} • {post.source}</p>
                        <p className="text-gray-700 mb-3">{post.content?.slice(0, 500)}{post.content?.length > 500 ? '...' : ''}</p>
                        <button onClick={() => showPostDetails(post.id)} className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                          Read more →
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                
                <div className="mt-8">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Related Posts</h3>
                  <div className="grid gap-4">
                    {posts.slice(3).map((post) => (
                      <div key={post.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md cursor-pointer" onClick={() => showPostDetails(post.id)}>
                        <div className="flex items-start space-x-4">
                          <div className="flex flex-col items-center">
                            <span className="text-sm font-semibold text-gray-700">{post.score}</span>
                            <span className="text-xs text-gray-500">votes</span>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 mb-1">{post.title || 'No title'}</h4>
                            <p className="text-sm text-gray-600 line-clamp-2">{post.content?.slice(0, 150)}...</p>
                            <p className="text-xs text-gray-500 mt-1">{formatDate(post.created_at)} • {post.view_count} views</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-lg p-6 sticky top-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Filters</h3>
            {latency && (
              <div className="mb-4 p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-800">⚡ {latency.toFixed(0)}ms</p>
              </div>
            )}
            <div className="space-y-2">
              <button onClick={() => fetchPosts('')} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm">📊 All Posts</button>
              <button onClick={() => fetchPosts('H1B')} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm">🔤 H1B Visa</button>
              <button onClick={() => fetchPosts('OPT')} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm">🎓 OPT</button>
              <button onClick={() => fetchPosts('green card')} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm">🟢 Green Card</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
