import type { APIRoute } from 'astro';
import { searchPosts } from '../../../lib/search-service';

export const GET: APIRoute = async ({ url }) => {
  const query = url.searchParams.get('q');
  const groupId = url.searchParams.get('group');
  const limit = parseInt(url.searchParams.get('limit') || '5');

  if (!query || !groupId) {
    return new Response(JSON.stringify({ error: 'Missing query or group' }), {
      status: 400,
    });
  }

  try {
    const results = await searchPosts(query, groupId, limit);
    
    return new Response(JSON.stringify({ results, count: results.length }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Search failed' }), {
      status: 500,
    });
  }
};
