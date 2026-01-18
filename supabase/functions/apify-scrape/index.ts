import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

Deno.serve(async (req) => {
  const auth = req.headers.get('Authorization');
  if (auth !== 'Bearer ' + Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')) {
    return new Response('Unauthorized', { status: 401 });
  }

  const apifyToken = Deno.env.get('APIFY_TOKEN');
  if (!apifyToken) return new Response('Missing APIFY_TOKEN', { status: 500 });

  const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const supabase = createClient(supabaseUrl, supabaseKey);

  // TODO: Move targetUrls to a config table if needed
  const targetUrls = ['https://example.com/posts'];

  for (const url of targetUrls) {
    // Start Apify actor run (simplified; adjust for your actor)
    const runRes = await fetch(`https://api.apify.com/v2/acts/apify~web-scraper/runs?token=${apifyToken}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        startUrls: [{ url }],
        maxPagesPerCrawl: 20
      })
    });

    if (!runRes.ok) {
      console.error('Apify run failed', await runRes.text());
      continue;
    }

    const run = await runRes.json();
    const datasetId = run.data?.defaultDatasetId;
    if (!datasetId) continue;

    // Fetch results as JSONL
    const dataRes = await fetch(
      `https://api.apify.com/v2/datasets/${datasetId}/items?format=jsonl&token=${apifyToken}`
    );
    if (!dataRes.ok) {
      console.error('Apify dataset fetch failed', await dataRes.text());
      continue;
    }

    const filename = `posts-${Date.now()}.jsonl`;
    const buffer = await dataRes.arrayBuffer();

    // Upload to Storage bucket: scraped-data
    const { error } = await supabase.storage
      .from('scraped-data')
      .upload(filename, new Blob([buffer]), {
        contentType: 'application/x-ndjson',
        upsert: false
      });

    if (error) {
      console.error('Storage upload error', error);
    }
  }

  return new Response('Apify scrape done');
});