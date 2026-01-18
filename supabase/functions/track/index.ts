import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TrackRequest {
  event_type: string
  properties?: Record<string, any>
  session_id?: string
  distinct_id?: string
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    // Get authenticated user
    const {
      data: { user },
    } = await supabaseClient.auth.getUser()

    // Parse request body
    const body: TrackRequest = await req.json()
    const { event_type, properties = {}, session_id, distinct_id } = body

    if (!event_type) {
      return new Response(
        JSON.stringify({ error: 'event_type is required' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get client IP
    const clientIP = req.headers.get('CF-Connecting-IP') ||
                     req.headers.get('X-Forwarded-For') ||
                     req.headers.get('X-Real-IP') ||
                     'unknown'

    // Prepare event data
    const eventData = {
      event_name: event_type,
      user_id: user?.id,
      session_id: session_id,
      distinct_id: distinct_id || user?.id || `anon_${Date.now()}`,
      properties: {
        ...properties,
        ip_address: clientIP,
        user_agent: req.headers.get('User-Agent'),
        timestamp: new Date().toISOString()
      },
      event_type: 'custom',
      source: 'edge_function',
      environment: 'production'
    }

    // Insert into analytics_events table
    const { data, error } = await supabaseClient
      .from('analytics_events')
      .insert(eventData)
      .select()

    if (error) {
      console.error('Error inserting analytics event:', error)
      return new Response(
        JSON.stringify({ error: 'Failed to track event', details: error.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          event_id: data[0].id,
          event_type,
          tracked_at: new Date().toISOString()
        }
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error in track function:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})