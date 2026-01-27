import type { APIRoute } from 'astro';

/**
 * POST /api/r2-upload - Upload file to R2
 */
export const POST: APIRoute = async ({ request }) => {
  try {
    const { key, content } = await request.json();

    if (!key || !content) {
      return new Response(JSON.stringify({ error: 'Missing key or content' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const accountId = import.meta.env.CF_ACCOUNT_ID;
    const accessKeyId = import.meta.env.CF_R2_ACCESS_KEY_ID;
    const accessKeySecret = import.meta.env.CF_R2_ACCESS_KEY_SECRET;
    const bucketName = import.meta.env.CF_R2_BUCKET_NAME;

    if (!accountId || !accessKeyId || !accessKeySecret || !bucketName) {
      throw new Error('R2 credentials not configured');
    }

    const url = `https://${bucketName}.r2.cloudflarestorage.com/${key}`;

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessKeySecret}`,
        'Content-Type': 'application/json'
      },
      body: content
    });

    if (!response.ok) {
      throw new Error(`R2 upload failed: ${response.statusText}`);
    }

    return new Response(
      JSON.stringify({
        url: `s3://${bucketName}/${key}`,
        success: true
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error: any) {
    console.error('POST /api/r2-upload error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Upload failed' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
