import { NextRequest, NextResponse } from 'next/server';

/**
 * DELETE /api/r2-delete - Delete file from R2
 */
export async function DELETE(request: NextRequest) {
  try {
    const { key } = await request.json();

    if (!key) {
      return NextResponse.json({ error: 'Missing key' }, { status: 400 });
    }

    const bucketName = process.env.CF_R2_BUCKET_NAME;
    const accessKeySecret = process.env.CF_R2_ACCESS_KEY_SECRET;

    if (!bucketName || !accessKeySecret) {
      throw new Error('R2 credentials not configured');
    }

    const url = `https://${bucketName}.r2.cloudflarestorage.com/${key}`;

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessKeySecret}`
      }
    });

    if (!response.ok) {
      throw new Error(`R2 delete failed: ${response.statusText}`);
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('DELETE /api/r2-delete error:', error);
    return NextResponse.json(
      { error: error.message || 'Delete failed' },
      { status: 500 }
    );
  }
}
