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
  const llm = ai.createTextGenerator('phi-3-mini');

  // Get clusters that need summary update
  const { data: clusters, error } = await supabase
    .from('clusters')
    .select('id, post_count, updated_at')
    .gt('post_count', 5)
    .limit(10);

  if (error || !clusters || clusters.length === 0) {
    return new Response('No clusters', { status: 200 });
  }

  for (const cluster of clusters) {
    const { data: posts, error: pErr } = await supabase
      .from('posts')
      .select('content')
      .eq('cluster_id', cluster.id)
      .limit(20);

    if (pErr || !posts || posts.length === 0) continue;

    const joined = posts
      .map((p) => p.content?.slice(0, 200) ?? '')
      .join('\n');

    const prompt = `You are summarizing discussion posts into a short topic label and description.
Posts:
${joined}

Return 1–2 sentences describing the common topic.`;
    const summary = await llm.run(prompt);

    await supabase
      .from('clusters')
      .update({
        summary,
        label: summary.split('.')[0],
        updated_at: new Date().toISOString()
      })
      .eq('id', cluster.id);
  }

  return new Response('Summaries updated');
});