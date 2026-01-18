import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { ai } from 'https://esm.sh/@supabase/supabase-js@2/ai';

Deno.serve(async (req) => {
  const auth = req.headers.get('Authorization');
  if (auth !== 'Bearer ' + Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) {
    return new Response('Unauthorized', { status: 401 });
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Read up to 50 jobs from post_queue (raw scraped posts)
  const { data: jobs, error } = await supabase
    .rpc('pgmq_read_wrapper', { queue_name: 'post_queue', batch_size: 50 });

  if (error || !jobs || jobs.length === 0) {
    return new Response('No jobs', { status: 200 });
  }

  const texts: string[] = [];
  const toInsert: any[] = [];

  for (const job of jobs) {
    const payload = job.message; // jsonb
    texts.push(payload.content);
    toInsert.push({
      scraped_url: payload.scraped_url,
      title: payload.title,
      content: payload.content,
      embedding_status: 'pending'
    });
  }

  const embedder = ai.createEmbeddings('gte-small');
  const vectors = await embedder.embed(texts);

  const rows = toInsert.map((p, i) => ({
    ...p,
    embedding: vectors[i],
    embedding_status: 'ready',
    processed_at: new Date().toISOString()
  }));

  const { error: insErr } = await supabase.from('posts').insert(rows);
  if (insErr) {
    console.error('Insert posts error', insErr);
  }

  // Delete processed jobs from queue
  const msgIds = jobs.map((j: any) => j.msg_id);
  const { error: delErr } = await supabase
    .rpc('pgmq_delete_wrapper', { queue_name: 'post_queue', msg_ids: msgIds });

  if (delErr) console.error('Queue delete error', delErr);

  return new Response(JSON.stringify({ embedded: rows.length }), {
    headers: { 'Content-Type': 'application/json' }
  });
});