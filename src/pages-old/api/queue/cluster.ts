import type { APIRoute } from 'astro';

/**
 * POST /api/queue/cluster - Send clustering job to Worker
 */
export const POST: APIRoute = async ({ request }) => {
  try {
    const payload = await request.json();

    const workerUrl = import.meta.env.WORKER_URL;
    const workerSecret = import.meta.env.WORKER_SECRET;

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
    return new Response(JSON.stringify(result), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('POST /api/queue/cluster error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to queue clustering' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
