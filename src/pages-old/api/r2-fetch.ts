import type { APIRoute } from 'astro';

/**
 * GET /api/r2-fetch - Fetch file from R2
 */
export const GET: APIRoute = async ({ url }) => {
  try {
    const key = url.searchParams.get('key');

    if (!key) {
      return new Response(JSON.stringify({ error: 'Missing key parameter' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const bucketName = import.meta.env.CF_R2_BUCKET_NAME;
    const accessKeySecret = import.meta.env.CF_R2_ACCESS_KEY_SECRET;

    if (!bucketName || !accessKeySecret) {
      throw new Error('R2 credentials not configured');
    }

    const r2Url = `https://${bucketName}.r2.cloudflarestorage.com/${key}`;

    const response = await fetch(r2Url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessKeySecret}`
      }
    });

    if (!response.ok) {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const content = await response.json();

    return new Response(JSON.stringify(content), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('GET /api/r2-fetch error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Fetch failed' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
