import { searchPosts } from '@/lib/search-service';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get('q');
  const groupId = searchParams.get('group');
  const limit = parseInt(searchParams.get('limit') || '5');

  if (!query || !groupId) {
    return NextResponse.json(
      { error: 'Missing query or group' },
      { status: 400 }
    );
  }

  try {
    const results = await searchPosts(query, groupId, limit);
    
    return NextResponse.json({ results, count: results.length });
  } catch (error) {
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    );
  }
}
