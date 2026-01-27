import { clusterDocuments, type Doc } from './clustering';

/**
 * Supabase client for Worker
 */
function createSupabaseClient(env: any) {
  const supabaseUrl = env.SUPABASE_URL;
  const supabaseKey = env.SUPABASE_SERVICE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Supabase credentials not configured');
  }

  return {
    url: supabaseUrl,
    key: supabaseKey,

    async request(method: string, path: string, body?: any) {
      const url = `${supabaseUrl}${path}`;
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseKey}`,
          'apikey': supabaseKey
        },
        body: body ? JSON.stringify(body) : undefined
      });

      if (!response.ok) {
        throw new Error(`Supabase ${method} ${path} failed: ${response.status}`);
      }

      return response.json();
    },

    async select(table: string) {
      return this.request('GET', `/rest/v1/${table}`);
    },

    async update(table: string, id: string, body: any) {
      return this.request('PATCH', `/rest/v1/${table}?id=eq.${id}`, body);
    }
  };
}

/**
 * Handle queue messages from Astro
 */
export async function handleQueueMessage(batch: any, env: any): Promise<void> {
  console.log(`Processing ${batch.messages.length} queue messages`);

  for (const message of batch.messages) {
    try {
      const job = JSON.parse(message.body);
      console.log('Processing job:', job);

      switch (job.action) {
        case 'cluster-post':
          await processSinglePost(job, env);
          break;
        case 'recluster-group':
          await reclusterGroup(job, env);
          break;
        default:
          console.warn('Unknown job action:', job.action);
      }

      message.ack();
    } catch (error) {
      console.error('Error processing message:', error);
      message.nack();
    }
  }
}

async function processSinglePost(job: any, env: any): Promise<void> {
  const { postId, text, groupId } = job;

  console.log(`Clustering post ${postId}`);

  const supabase = createSupabaseClient(env);

  const response = await fetch(
    `${supabase.url}/rest/v1/posts?group_id=eq.${groupId}&order=created_at.desc&limit=100`,
    {
      headers: {
        'Authorization': `Bearer ${supabase.key}`,
        'apikey': supabase.key
      }
    }
  );

  const posts = await response.json();

  const docs: Doc[] = posts.map((p: any) => ({
    id: p.id,
    text: p.text || ''
  }));

  docs.push({ id: postId, text });

  const clusters = clusterDocuments(docs);

  const postCluster = clusters.find(c => c.docIds.includes(postId));

  if (postCluster) {
    await fetch(
      `${supabase.url}/rest/v1/posts?id=eq.${postId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabase.key}`,
          'apikey': supabase.key
        },
        body: JSON.stringify({ cluster_id: postCluster.clusterId })
      }
    );

    console.log(`Post ${postId} assigned to cluster ${postCluster.clusterId}`);

    await env.POSTS_KV.put(
      `clusters:${groupId}`,
      JSON.stringify({
        clusters: clusters.map(c => ({
          id: c.clusterId,
          postIds: c.docIds,
          size: c.size
        })),
        timestamp: new Date().toISOString()
      }),
      { expirationTtl: 3600 }
    );
  }
}

async function reclusterGroup(job: any, env: any): Promise<void> {
  const { groupId } = job;

  console.log(`Reclustering group ${groupId}`);

  const supabase = createSupabaseClient(env);

  const response = await fetch(
    `${supabase.url}/rest/v1/posts?group_id=eq.${groupId}&order=created_at.desc`,
    {
      headers: {
        'Authorization': `Bearer ${supabase.key}`,
        'apikey': supabase.key
      }
    }
  );

  const posts = await response.json();

  const docs: Doc[] = posts.map((p: any) => ({
    id: p.id,
    text: p.text || ''
  }));

  if (docs.length === 0) {
    console.log('No posts to cluster');
    return;
  }

  const clusters = clusterDocuments(docs);

  const updatePromises = clusters.flatMap(cluster =>
    cluster.docIds.map(postId =>
      fetch(`${supabase.url}/rest/v1/posts?id=eq.${postId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabase.key}`,
          'apikey': supabase.key
        },
        body: JSON.stringify({ cluster_id: cluster.clusterId })
      })
    )
  );

  await Promise.all(updatePromises);

  console.log(`Clustered ${docs.length} posts into ${clusters.length} clusters`);

  await env.POSTS_KV.put(
    `clusters:${groupId}`,
    JSON.stringify({
      clusters: clusters.map(c => ({
        id: c.clusterId,
        postIds: c.docIds,
        size: c.size
      })),
      timestamp: new Date().toISOString()
    }),
    { expirationTtl: 3600 }
  );
}
