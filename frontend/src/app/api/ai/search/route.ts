import { NextRequest, NextResponse } from 'next/server';

// API route to proxy AI search to FastAPI backend
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('query');
    const group_id = searchParams.get('group_id');
    const community_id = searchParams.get('community_id');
    const limit = searchParams.get('limit') || '10';

    if (!query || !group_id) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Missing required parameters: query and group_id' 
        },
        { status: 400 }
      );
    }

    // Call FastAPI backend
    const response = await fetch(`http://localhost:8000/api/v1/ai/search?query=${encodeURIComponent(query)}&group_id=${group_id}&community_id=${community_id}&limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('AI Search API Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to connect to AI search service',
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
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}