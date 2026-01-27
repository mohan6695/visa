import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/queue/cluster - Send clustering job to Worker
 */
export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();

    const workerUrl = process.env.WORKER_URL;
    const workerSecret = process.env.WORKER_SECRET;

    if (!workerUrl || !workerSecret) {
      throw new Error('Worker credentials not configured');
    }

    // Forward to Worker
    const response = await fetch(`${workerUrl}/queue/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${workerSecret}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(
        `Worker responded with ${response.status}: ${response.statusText}`
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('POST /api/queue/cluster error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to queue clustering' },
      { status: 500 }
    );
  }
}
