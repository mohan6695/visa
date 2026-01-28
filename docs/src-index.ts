import { handleRequest } from './ask';
import { handleIngestion } from './ingestion';

export interface Env {
  SUPABASE_URL: string;
  SUPABASE_KEY: string;
  MEILISEARCH_URL: string;
  MEILISEARCH_KEY: string;
  GROQ_API_KEY: string;
  RATE_LIMIT: KVNamespace;
  AI: Fetcher;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);

    if (request.method === 'POST' && url.pathname === '/api/chat/rag') {
      return handleRequest(request, env, ctx);
    }

    if (request.method === 'GET' && url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response('Not found', { status: 404 });
  },

  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    console.log('Ingestion worker triggered');
    ctx.waitUntil(handleIngestion(env, ctx));
  },
};
