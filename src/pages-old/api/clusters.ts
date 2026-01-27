import type { APIRoute } from 'astro';
import { fetchClusteredPosts, getClusterDetails } from '../../lib/cluster-service';

/**
 * GET /api/clusters - Fetch clustered posts for a group
 */
export const GET: APIRoute = async ({ url }) => {
  try {
    const groupId = url.searchParams.get('groupId') || 'default';
    const clusterId = url.searchParams.get('clusterId');

    if (clusterId) {
      // Get specific cluster
      const cluster = await getClusterDetails(clusterId, groupId);
      return new Response(JSON.stringify({ cluster }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get all clusters
    const clustered = await fetchClusteredPosts(groupId);

    return new Response(JSON.stringify(clustered), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error: any) {
    console.error('GET /api/clusters error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
