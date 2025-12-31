import { NextRequest, NextResponse } from 'next/server';

// API route to proxy AI questions to FastAPI backend
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question, group_id, community_id, use_cache, context_type } = body;

    // Call FastAPI backend
    const response = await fetch('http://localhost:8000/api/v1/ai/answer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        group_id,
        community_id,
        use_cache: use_cache ?? true,
        context_type: context_type ?? 'full'
      }),
    });

    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('AI Answer API Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to connect to AI service',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// Handle preflight requests
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}