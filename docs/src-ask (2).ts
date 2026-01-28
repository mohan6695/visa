import { Env } from './index';

interface AskRequest {
  question: string;
  group_id: number;
  user_id: string;
  conversation_id?: string;
}

interface AskResponse {
  answer: string;
  sources: Array<{
    post_id: number;
    title: string;
    relevance_score: number;
  }>;
  latency_ms: number;
  conversation_id: string;
}

export async function handleRequest(
  request: Request,
  env: Env,
  ctx: ExecutionContext
): Promise<Response> {
  const startTime = Date.now();

  try {
    const { question, group_id, user_id, conversation_id } = (await request.json()) as AskRequest;

    if (!question || !group_id || !user_id) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: question, group_id, user_id' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const authHeader = request.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const token = authHeader.slice(7);
    console.log('Token received');

    const rateLimitKey = `rate_limit:${user_id}`;
    const countStr = await env.RATE_LIMIT.get(rateLimitKey);
    const count = countStr ? parseInt(countStr) : 0;

    if (count > 100) {
      return new Response(JSON.stringify({ error: 'Rate limit exceeded (100/day)' }), {
        status: 429,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    await env.RATE_LIMIT.put(rateLimitKey, String(count + 1), {
      expirationTtl: 86400,
    });

    console.log('Generating embedding for question...');
    const embeddingResult = await env.AI.run(
      '@cf/baai/bge-base-en-v1.5' as any,
      { text: question }
    );

    if (!embeddingResult || !embeddingResult.data || !embeddingResult.data[0]) {
      throw new Error('Failed to generate embedding');
    }

    const questionEmbedding = embeddingResult.data[0];

    console.log('Searching Meilisearch...');
    const meilisearchResponse = await fetch(
      `${env.MEILISEARCH_URL}/indexes/posts/search`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.MEILISEARCH_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          q: question,
          vector: questionEmbedding,
          filter: [`group_id = ${group_id}`],
          limit: 10,
          attributesToRetrieve: [
            'chunk_text',
            'post_id',
            'title',
            'author_id',
            'tags',
            'chunk_index',
          ],
        }),
      }
    );

    if (!meilisearchResponse.ok) {
      throw new Error(`Meilisearch error: ${meilisearchResponse.statusText}`);
    }

    const searchResults = await meilisearchResponse.json() as any;
    const retrievedChunks = searchResults.hits || [];

    if (retrievedChunks.length === 0) {
      return new Response(
        JSON.stringify({
          answer: 'No relevant posts found in your community. Try asking a different question.',
          sources: [],
          latency_ms: Date.now() - startTime,
          conversation_id: conversation_id || `conv_${Date.now()}`,
        }),
        { headers: { 'Content-Type': 'application/json' } }
      );
    }

    const context = retrievedChunks
      .slice(0, 5)
      .map(
        (chunk: any, idx: number) =>
          `[Post ${chunk.post_id} - Relevance: ${(chunk._rankingScore * 100).toFixed(1)}%]\n${chunk.chunk_text}`
      )
      .join('\n\n---\n\n');

    console.log('Calling Groq API...');
    const groqResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.1-8b-instant',
        messages: [
          {
            role: 'system',
            content: `You are a helpful assistant for a community Q&A platform. Answer questions using ONLY the provided context from community posts. 
            
If the context doesn't contain the answer, say "I don't have information about this in the community posts."

Be concise, helpful, and cite the post numbers when relevant.`,
          },
          {
            role: 'user',
            content: `Context from community posts:\n\n${context}\n\n---\n\nUser Question: ${question}\n\nAnswer:`,
          },
        ],
        temperature: 0.7,
        max_tokens: 500,
      }),
    });

    if (!groqResponse.ok) {
      const error = await groqResponse.text();
      console.error('Groq error:', error);
      throw new Error(`Groq API error: ${groqResponse.statusText}`);
    }

    const groqData = (await groqResponse.json()) as any;
    const answer = groqData.choices[0].message.content;

    const logPayload = {
      user_id,
      group_id,
      question,
      answer,
      used_post_ids: Array.from(new Set(retrievedChunks.map((c: any) => c.post_id))),
      conversation_id: conversation_id || `conv_${Date.now()}`,
      created_at: new Date().toISOString(),
    };

    try {
      await fetch(`${env.SUPABASE_URL}/rest/v1/chat_logs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.SUPABASE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify(logPayload),
      });
    } catch (logErr) {
      console.warn('Failed to log chat', logErr);
    }

    const response: AskResponse = {
      answer,
      sources: retrievedChunks.slice(0, 5).map((chunk: any) => ({
        post_id: chunk.post_id,
        title: chunk.title || `Post ${chunk.post_id}`,
        relevance_score: chunk._rankingScore || 0,
      })),
      latency_ms: Date.now() - startTime,
      conversation_id: conversation_id || `conv_${Date.now()}`,
    };

    return new Response(JSON.stringify(response), {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
      },
    });
  } catch (error) {
    console.error('Error in handleRequest:', error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Internal server error',
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
