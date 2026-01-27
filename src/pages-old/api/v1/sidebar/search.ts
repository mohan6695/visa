import type { APIRoute } from 'astro';
import { fetchPosts } from '../../../../lib/supabase';

/**
 * GET /api/v1/sidebar/search - Search for posts with sidebar format
 */
export const GET: APIRoute = async ({ url }) => {
  try {
    const q = url.searchParams.get('q') || '';
    const groupId = url.searchParams.get('group_id') || '550e8400-e29b-41d4-a716-446655440001';
    const limit = parseInt(url.searchParams.get('limit') || '12');

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

    return new Response(
      JSON.stringify({
        posts: limitedPosts
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error: any) {
    console.error('GET /api/v1/sidebar/search error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
