import type { APIRoute } from 'astro';
import { storePostWithComments } from '../../lib/post-service';
import { fetchPosts } from '../../lib/supabase';
import type { PostPayload } from '../../lib/types';

/**
 * POST /api/posts - Create a new post
 */
export const POST: APIRoute = async ({ request }) => {
  try {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const payload: PostPayload = await request.json();

    // Validate
    if (!payload.title || !payload.text || !payload.url) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const post = await storePostWithComments(payload);

    return new Response(JSON.stringify({ success: true, post }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('POST /api/posts error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

/**
 * GET /api/posts - Fetch posts for a group
 */
export const GET: APIRoute = async ({ url }) => {
  try {
    const groupId = url.searchParams.get('groupId') || 'default';
    const posts = await fetchPosts(groupId);

    return new Response(JSON.stringify({ posts }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('GET /api/posts error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
