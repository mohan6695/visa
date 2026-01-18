import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

Deno.serve(async (req) => {
  const auth = req.headers.get('Authorization');
  if (auth !== 'Bearer ' + Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) {
    return new Response('Unauthorized', { status: 401 });
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Fetch ready, unclustered posts
  const { data: posts, error } = await supabase
    .from('posts')
    .select('id, embedding')
    .eq('embedding_status', 'ready')
    .is('cluster_id', null)
    .limit(200);

  if (error || !posts || posts.length === 0) {
    return new Response('No posts', { status: 200 });
  }

  for (const post of posts) {
    if (!post.embedding) continue;

    const { data: nearest, error: rpcErr } = await supabase
      .rpc('assign_nearest_centroid', { query_emb: post.embedding });

    if (rpcErr) {
      console.error('assign_nearest_centroid error', rpcErr);
      continue;
    }

    let clusterId: number | null = null;

    if (nearest && nearest.length > 0 && nearest[0].distance < 0.3) {
      clusterId = nearest[0].id;
    } else {
      // Create new cluster with this embedding as centroid
      const { data: newCluster, error: cErr } = await supabase
        .from('clusters')
        .insert({
          centroid: post.embedding,
          post_count: 0
        })
        .select('id')
        .single();

      if (cErr || !newCluster) {
        console.error('create cluster error', cErr);
        continue;
      }
      clusterId = newCluster.id;
    }

    // Update post + cluster count
    if (clusterId != null) {
      await supabase.from('posts').update({ cluster_id: clusterId }).eq('id', post.id);
      await supabase.rpc('update_cluster_count', { cluster_id: clusterId });
    }
  }

  return new Response('Clustered batch');
});