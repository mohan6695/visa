import type { APIRoute } from 'astro';

/**
 * GET /api/cache/get - Fetch from Worker KV cache
 */
export const GET: APIRoute = async ({ url }) => {
  try {
    const key = url.searchParams.get('key');

    if (!key) {
      return new Response(JSON.stringify({ error: 'Missing key' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const workerUrl = import.meta.env.WORKER_URL;
    const workerSecret = import.meta.env.WORKER_SECRET;

    if (!workerUrl || !workerSecret) {
      throw new Error('Worker credentials not configured');
    }

    const response = await fetch(
      `${workerUrl}/kv/get?key=${encodeURIComponent(key)}`,
      {
        headers: {
          'Authorization': `Bearer ${workerSecret}`
        }
      }
    );

    if (!response.ok) {
      return new Response(JSON.stringify({ error: 'Not found in cache' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('GET /api/cache/get error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Cache fetch failed' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
