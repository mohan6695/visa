import { NextRequest, NextResponse } from 'next/server';
import { likeComment, unlikeComment, checkCommentLike } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    const { commentId, userId = 'anonymous', action } = await request.json();

    if (!commentId) {
      return NextResponse.json(
        { error: 'Missing commentId' },
        { status: 400 }
      );
    }

    if (action === 'like') {
      await likeComment(commentId, userId);
    } else if (action === 'unlike') {
      await unlikeComment(commentId, userId);
    } else {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Error handling comment like:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to handle like' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const commentId = searchParams.get('commentId');
    const userId = searchParams.get('userId') || 'anonymous';

    if (!commentId) {
      return NextResponse.json(
        { error: 'Missing commentId' },
        { status: 400 }
      );
    }

    const liked = await checkCommentLike(commentId, userId);
    return NextResponse.json({ liked });
  } catch (error: any) {
    console.error('Error checking comment like:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to check like' },
      { status: 500 }
    );
  }
}
