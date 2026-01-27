import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/cache/get - Fetch from Worker KV cache
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const key = searchParams.get('key');

    if (!key) {
      return NextResponse.json({ error: 'Missing key' }, { status: 400 });
    }

    const workerUrl = process.env.WORKER_URL;
    const workerSecret = process.env.WORKER_SECRET;

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
      return NextResponse.json(
        { error: 'Not found in cache' },
        { status: 404 }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('GET /api/cache/get error:', error);
    return NextResponse.json(
      { error: error.message || 'Cache fetch failed' },
      { status: 500 }
    );
  }
}
