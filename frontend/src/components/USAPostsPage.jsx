"use client"

import { useState, useEffect } from 'react'
import processedPosts from '../data/processedPosts.json'

export function USAPostsPage() {
  const [posts, setPosts] = useState(processedPosts)
  const [searchQuery, setSearchQuery] = useState('')
  const [clusterFilter, setClusterFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [selectedPost, setSelectedPost] = useState(null)

  // Get unique clusters for filtering
  const uniqueClusters = [...new Set(posts.map(post => post.cluster_name))]

  // Filter posts based on search and cluster
  const filteredPosts = posts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         post.content.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesCluster = clusterFilter === 'all' || post.cluster_name === clusterFilter
    
    return matchesSearch && matchesCluster
  })

  // Get author initials
  const getAuthorInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  // Get similar posts for sidebar
  const getSimilarPosts = (post) => {
    return posts
      .filter(p => p.id !== post.id && p.cluster_name === post.cluster_name)
      .sort((a, b) => b.similarity_score - a.similarity_score)
      .slice(0, 3)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Posts Area */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">USA Visa Posts</h2>
            <div className="text-sm text-gray-600">
              <span>{filteredPosts.length}</span> posts found
            </div>
          </div>
          
          {/* Search and Filter */}
          <div className="bg-white shadow-sm border-b rounded-lg p-4 mb-6">
            <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
              <div className="flex-1 max-w-lg">
                <form className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Search posts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Search
                  </button>
                </form>
              </div>
              <div className="flex gap-2">
                <select
                  value={clusterFilter}
                  onChange={(e) => setClusterFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Clusters</option>
                  {uniqueClusters.map(cluster => (
                    <option key={cluster} value={cluster}>{cluster}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          
          {/* Posts List */}
          <div className="space-y-6">
            {filteredPosts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No posts found. Try adjusting your search or filters.</p>
              </div>
            ) : (
              filteredPosts.map((post) => (
                <div key={post.id} className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="flex">
                    {/* Vote Controls */}
                    <div className="flex flex-col items-center px-4 py-6 space-y-2 border-r border-gray-200">
                      <button className="text-gray-500 hover:text-green-600 transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path>
                        </svg>
                      </button>
                      <span className="text-lg font-semibold text-gray-700">{post.upvotes}</span>
                      <button className="text-gray-500 hover:text-red-600 transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                      </button>
                    </div>
                    
                    {/* Post Content */}
                    <div className="flex-1 p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-700 font-bold">
                            {getAuthorInitials(post.author_name)}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900 hover:text-blue-600 cursor-pointer">
                              {post.title}
                            </h3>
                            <div className="text-sm text-gray-600">
                              <span>by {post.author_name}</span>
                              <span className="mx-2">•</span>
                              <span>{post.relative_time}</span>
                              <span className="mx-2">•</span>
                              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                {post.cluster_name}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">{post.comment_count} answers</span>
                          <span className="text-sm text-gray-500">{post.view_count} views</span>
                        </div>
                      </div>
                      
                      <div className="text-gray-700 mb-4 line-clamp-3">
                        {post.content}
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex flex-wrap gap-2">
                          {post.tags.map((tag, index) => (
                            <span key={index} className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs font-medium">
                              {tag}
                            </span>
                          ))}
                          <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-medium">
                            {Math.round(post.similarity_score * 100)}% match
                          </span>
                        </div>
                        
                        <div className="flex space-x-2">
                          <button 
                            onClick={() => setSelectedPost(post)}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                          >
                            View Full Post
                          </button>
                          <button className="text-gray-500 hover:text-gray-700 text-sm">
                            Share
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Sidebar with Similar Posts and Cluster Info */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-lg p-6 sticky top-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Cluster Statistics</h3>
            <div className="space-y-3 mb-6">
              {uniqueClusters.slice(0, 6).map((cluster) => {
                const clusterPosts = posts.filter(p => p.cluster_name === cluster)
                return (
                  <div key={cluster} className="flex justify-between items-center">
                    <span className="text-sm text-gray-700">{cluster}</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {clusterPosts.length}
                    </span>
                  </div>
                )
              })}
            </div>
            
            {selectedPost && (
              <>
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Similar Posts</h4>
                  <div className="space-y-3">
                    {getSimilarPosts(selectedPost).map((similarPost) => (
                      <div key={similarPost.id} className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <h5 className="font-medium text-gray-900 text-sm mb-1 line-clamp-2">
                          {similarPost.title}
                        </h5>
                        <div className="text-xs text-gray-600">
                          <span>{Math.round(similarPost.similarity_score * 100)}% similar</span>
                          <span className="mx-2">•</span>
                          <span>{similarPost.comment_count} answers</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="mt-4">
                  <button 
                    onClick={() => setSelectedPost(null)}
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    Hide similar posts
                  </button>
                </div>
              </>
            )}
            
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">About USA Visa Posts</h4>
              <p className="text-sm text-gray-600">
                This section contains Stack Overflow-style posts about USA visa issues, including H1B, F1, visa stamping, revocations, and more. Posts are clustered using semantic similarity for better content discovery.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}