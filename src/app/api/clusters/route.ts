import { fetchClusteredPosts, getClusterDetails } from '@/lib/cluster-service';
import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/clusters - Fetch clustered posts for a group
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const groupId = searchParams.get('groupId') || 'default';
    const clusterId = searchParams.get('clusterId');

    if (clusterId) {
      // Get specific cluster
      const cluster = await getClusterDetails(clusterId, groupId);
      return NextResponse.json({ cluster });
    }

    // Get all clusters
    const clustered = await fetchClusteredPosts(groupId);

    return NextResponse.json(clustered);
  } catch (error: any) {
    console.error('GET /api/clusters error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
