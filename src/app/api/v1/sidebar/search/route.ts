import { fetchPosts } from '@/lib/supabase';
import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/v1/sidebar/search - Search for posts with sidebar format
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const q = searchParams.get('q') || '';
    const groupId = searchParams.get('group_id') || '550e8400-e29b-41d4-a716-446655440001';
    const limit = parseInt(searchParams.get('limit') || '12');

    // Fetch posts from Supabase
    const posts = await fetchPosts(groupId);

    // Filter posts based on search query (simple keyword match)
    const filteredPosts = q.trim() === '' 
      ? posts 
      : posts.filter(post => 
          (post.title && post.title.toLowerCase().includes(q.toLowerCase())) || 
          (post.content && post.content.toLowerCase().includes(q.toLowerCase()))
        );

    // Limit the results
    const limitedPosts = filteredPosts.slice(0, limit);

    return NextResponse.json({
      posts: limitedPosts
    });
  } catch (error: any) {
    console.error('GET /api/v1/sidebar/search error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
};
