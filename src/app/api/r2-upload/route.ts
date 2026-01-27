import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/r2-upload - Upload file to R2
 */
export async function POST(request: NextRequest) {
  try {
    const { key, content } = await request.json();

    if (!key || !content) {
      return NextResponse.json(
        { error: 'Missing key or content' },
        { status: 400 }
      );
    }

    const accountId = process.env.CF_ACCOUNT_ID;
    const accessKeyId = process.env.CF_R2_ACCESS_KEY_ID;
    const accessKeySecret = process.env.CF_R2_ACCESS_KEY_SECRET;
    const bucketName = process.env.CF_R2_BUCKET_NAME;

    if (!accountId || !accessKeyId || !accessKeySecret || !bucketName) {
      throw new Error('R2 credentials not configured');
    }

    const url = `https://${bucketName}.r2.cloudflarestorage.com/${key}`;

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessKeySecret}`,
        'Content-Type': 'application/json'
      },
      body: content
    });

    if (!response.ok) {
      throw new Error(`R2 upload failed: ${response.statusText}`);
    }

    return NextResponse.json({
      url: `s3://${bucketName}/${key}`,
      success: true
    });
  } catch (error: any) {
    console.error('POST /api/r2-upload error:', error);
    return NextResponse.json(
      { error: error.message || 'Upload failed' },
      { status: 500 }
    );
  }
}
