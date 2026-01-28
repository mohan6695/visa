import { NextRequest, NextResponse } from 'next/server';
import { likePost, unlikePost, checkPostLike } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    const { postId, userId = 'anonymous', action } = await request.json();

    if (!postId) {
      return NextResponse.json(
        { error: 'Missing postId' },
        { status: 400 }
      );
    }

    if (action === 'like') {
      await likePost(postId, userId);
    } else if (action === 'unlike') {
      await unlikePost(postId, userId);
    } else {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Error handling post like:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to handle like' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const postId = searchParams.get('postId');
    const userId = searchParams.get('userId') || 'anonymous';

    if (!postId) {
      return NextResponse.json(
        { error: 'Missing postId' },
        { status: 400 }
      );
    }

    const liked = await checkPostLike(postId, userId);
    return NextResponse.json({ liked });
  } catch (error: any) {
    console.error('Error checking post like:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to check like' },
      { status: 500 }
    );
  }
}
