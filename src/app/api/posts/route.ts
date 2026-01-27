import { storePostWithComments } from '@/lib/post-service';
import { fetchPosts } from '@/lib/supabase';
import type { PostPayload } from '@/lib/types';
import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/posts - Create a new post
 */
export async function POST(request: NextRequest) {
  try {
    const payload: PostPayload = await request.json();

    // Validate
    if (!payload.title || !payload.text || !payload.url) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const post = await storePostWithComments(payload);

    return NextResponse.json({ success: true, post }, { status: 201 });
  } catch (error: any) {
    console.error('POST /api/posts error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/posts - Fetch posts for a group
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const groupId = searchParams.get('groupId') || 'default';
    const posts = await fetchPosts(groupId);

    return NextResponse.json({ posts });
  } catch (error: any) {
    console.error('GET /api/posts error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
