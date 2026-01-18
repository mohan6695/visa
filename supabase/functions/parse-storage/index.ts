import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

Deno.serve(async (req) => {
  const auth = req.headers.get('Authorization');
  if (auth !== 'Bearer ' + Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) {
    return new Response('Unauthorized', { status: 401 });
  }

  const body = await req.json();
  const { name, bucket } = body.record ?? body;

  if (bucket !== 'scraped-data' || !name) {
    return new Response('Ignored', { status: 200 });
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const supabase = createClient(supabaseUrl, supabaseKey);

  const { data: file, error } = await supabase.storage
    .from('scraped-data')
    .download(name);

  if (error || !file) {
    console.error('Download error', error);
    return new Response('Error', { status: 500 });
  }

  const text = await file.text();
  const lines = text.split('\n').filter(Boolean);

  // Minimal JSONL parsing; adjust keys as per Apify result shape
  const batch: { scraped_url: string; title: string; content: string }[] = [];

  for (const line of lines) {
    try {
      const obj = JSON.parse(line);
      const url = obj.url || obj.pageUrl;
      const title = obj.title || obj.pageTitle;
      const content = obj.text || obj.content;

      if (!url || !title || !content) continue;

      batch.push({ scraped_url: url, title, content });
    } catch (e) {
      console.error('JSON parse error', e);
      continue;
    }
  }

  // Queue posts into pgmq "post_queue" as raw JSON
  // (embedding + insert happens in generate-embeddings function)
  for (const post of batch) {
    const { error: qErr } = await supabase
      .rpc('pgmq_send_wrapper', { queue_name: 'post_queue', message: post });

    if (qErr) console.error('Queue error', qErr);
  }

  return new Response('Queued posts');
});