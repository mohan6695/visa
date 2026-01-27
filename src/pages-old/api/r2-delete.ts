import type { APIRoute } from 'astro';

/**
 * DELETE /api/r2-delete - Delete file from R2
 */
export const DELETE: APIRoute = async ({ request }) => {
  try {
    const { key } = await request.json();

    if (!key) {
      return new Response(JSON.stringify({ error: 'Missing key' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const bucketName = import.meta.env.CF_R2_BUCKET_NAME;
    const accessKeySecret = import.meta.env.CF_R2_ACCESS_KEY_SECRET;

    if (!bucketName || !accessKeySecret) {
      throw new Error('R2 credentials not configured');
    }

    const url = `https://${bucketName}.r2.cloudflarestorage.com/${key}`;

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessKeySecret}`
      }
    });

    if (!response.ok) {
      throw new Error(`R2 delete failed: ${response.statusText}`);
    }

    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('DELETE /api/r2-delete error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Delete failed' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
