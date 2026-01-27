import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/r2-fetch - Fetch file from R2
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const key = searchParams.get('key');

    if (!key) {
      return NextResponse.json(
        { error: 'Missing key parameter' },
        { status: 400 }
      );
    }

    const bucketName = process.env.CF_R2_BUCKET_NAME;
    const accessKeySecret = process.env.CF_R2_ACCESS_KEY_SECRET;

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
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    const content = await response.json();

    return NextResponse.json(content);
  } catch (error: any) {
    console.error('GET /api/r2-fetch error:', error);
    return NextResponse.json(
      { error: error.message || 'Fetch failed' },
      { status: 500 }
    );
  }
}
