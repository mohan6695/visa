import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
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

    if (!user) {
      return new Response(
        JSON.stringify({ error: 'Authentication required' }),
        {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get user_id from URL path
    const url = new URL(req.url)
    const pathParts = url.pathname.split('/')
    const targetUserId = pathParts[pathParts.length - 1] // Last part of path

    if (!targetUserId) {
      return new Response(
        JSON.stringify({ error: 'User ID is required' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Check if user is admin or the target user
    const { data: userProfile } = await supabaseClient
      .from('user_profiles')
      .select('subscription_tier')
      .eq('user_id', user.id)
      .single()

    const isAdmin = userProfile?.subscription_tier === 'admin' ||
                   user.email === 'admin@example.com' // Adjust as needed
    const isTargetUser = user.id === targetUserId

    if (!isAdmin && !isTargetUser) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get limit from query params
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '100'), 1000)

    // Get user activity
    const { data: userActivity, error: activityError } = await supabaseClient
      .from('analytics_events')
      .select('*')
      .eq('user_id', targetUserId)
      .order('created_at', { ascending: false })
      .limit(limit)

    if (activityError) {
      console.error('Error fetching user activity:', activityError)
      return new Response(
        JSON.stringify({ error: 'Failed to fetch user activity', details: activityError.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Calculate some summary stats
    const eventCounts: Record<string, number> = {}
    const sessions = new Set()
    let firstActivity: string | null = null
    let lastActivity: string | null = null

    userActivity?.forEach(event => {
      // Count events by type
      eventCounts[event.event_name] = (eventCounts[event.event_name] || 0) + 1

      // Track sessions
      if (event.session_id) {
        sessions.add(event.session_id)
      }

      // Track activity dates
      if (!firstActivity || event.created_at < firstActivity) {
        firstActivity = event.created_at
      }
      if (!lastActivity || event.created_at > lastActivity) {
        lastActivity = event.created_at
      }
    })

    const summary = {
      total_events: userActivity?.length || 0,
      unique_sessions: sessions.size,
      event_types: eventCounts,
      first_activity: firstActivity,
      last_activity: lastActivity,
      time_range_days: firstActivity && lastActivity ?
        Math.ceil((new Date(lastActivity).getTime() - new Date(firstActivity).getTime()) / (1000 * 60 * 60 * 24)) : 0
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          user_id: targetUserId,
          summary,
          activity: userActivity
        }
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error in user-analytics function:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})