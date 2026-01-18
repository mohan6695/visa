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

    // Get group_id from URL path
    const url = new URL(req.url)
    const pathParts = url.pathname.split('/')
    const groupId = pathParts[pathParts.length - 1] // Last part of path

    if (!groupId) {
      return new Response(
        JSON.stringify({ error: 'Group ID is required' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Check if user is admin or group leader
    const { data: userProfile } = await supabaseClient
      .from('user_profiles')
      .select('subscription_tier, group_id')
      .eq('user_id', user.id)
      .single()

    const isAdmin = userProfile?.subscription_tier === 'admin' ||
                   user.email === 'admin@example.com' // Adjust as needed
    const isGroupLeader = userProfile?.group_id === groupId &&
                         userProfile?.subscription_tier === 'group_leader'

    if (!isAdmin && !isGroupLeader) {
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

    // Get users in the group
    const { data: groupUsers, error: usersError } = await supabaseClient
      .from('user_profiles')
      .select('user_id')
      .eq('group_id', groupId)

    if (usersError) {
      console.error('Error fetching group users:', usersError)
      return new Response(
        JSON.stringify({ error: 'Failed to fetch group users', details: usersError.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    const userIds = groupUsers?.map(u => u.user_id) || []

    if (userIds.length === 0) {
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            group_id: groupId,
            summary: {
              total_users: 0,
              total_events: 0,
              event_types: {}
            },
            activity: []
          }
        }),
        {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get group activity (events from group users)
    const { data: groupActivity, error: activityError } = await supabaseClient
      .from('analytics_events')
      .select('*')
      .in('user_id', userIds)
      .order('created_at', { ascending: false })
      .limit(limit)

    if (activityError) {
      console.error('Error fetching group activity:', activityError)
      return new Response(
        JSON.stringify({ error: 'Failed to fetch group activity', details: activityError.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Calculate summary stats
    const eventCounts: Record<string, number> = {}
    const activeUsers = new Set()
    let firstActivity: string | null = null
    let lastActivity: string | null = null

    groupActivity?.forEach(event => {
      // Count events by type
      eventCounts[event.event_name] = (eventCounts[event.event_name] || 0) + 1

      // Track active users
      if (event.user_id) {
        activeUsers.add(event.user_id)
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
      total_users: userIds.length,
      active_users: activeUsers.size,
      total_events: groupActivity?.length || 0,
      event_types: eventCounts,
      first_activity: firstActivity,
      last_activity: lastActivity,
      activity_period_days: firstActivity && lastActivity ?
        Math.ceil((new Date(lastActivity).getTime() - new Date(firstActivity).getTime()) / (1000 * 60 * 60 * 24)) : 0
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          group_id: groupId,
          summary,
          activity: groupActivity
        }
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error in group-analytics function:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})