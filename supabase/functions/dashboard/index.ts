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

    // Check if user is admin (you might need to adjust this based on your user roles)
    const { data: userProfile } = await supabaseClient
      .from('user_profiles')
      .select('subscription_tier')
      .eq('user_id', user.id)
      .single()

    const isAdmin = userProfile?.subscription_tier === 'admin' ||
                   user.email === 'admin@example.com' // Adjust as needed

    if (!isAdmin) {
      return new Response(
        JSON.stringify({ error: 'Admin access required' }),
        {
          status: 403,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Get period from query params
    const url = new URL(req.url)
    const period = url.searchParams.get('period') || 'week'

    // Calculate date range
    const now = new Date()
    let startDate: Date

    switch (period) {
      case 'day':
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        break
      case 'week':
        const weekStart = now.getDate() - now.getDay()
        startDate = new Date(now.getFullYear(), now.getMonth(), weekStart)
        break
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1)
        break
      default:
        return new Response(
          JSON.stringify({ error: 'Invalid period. Must be day, week, or month' }),
          {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        )
    }

    const startDateStr = startDate.toISOString()
    const endDateStr = now.toISOString()

    // Get event counts
    const { data: eventCountsData, error: eventCountsError } = await supabaseClient
      .from('analytics_events')
      .select('event_name')
      .gte('created_at', startDateStr)
      .lte('created_at', endDateStr)

    if (eventCountsError) {
      console.error('Error fetching event counts:', eventCountsError)
    }

    const eventCounts: Record<string, number> = {}
    eventCountsData?.forEach(event => {
      eventCounts[event.event_name] = (eventCounts[event.event_name] || 0) + 1
    })

    // Get active users (distinct user_id in period)
    const { data: activeUsersData, error: activeUsersError } = await supabaseClient
      .from('analytics_events')
      .select('user_id', { count: 'exact' })
      .gte('created_at', startDateStr)
      .lte('created_at', endDateStr)
      .not('user_id', 'is', null)

    if (activeUsersError) {
      console.error('Error fetching active users:', activeUsersError)
    }

    const activeUsers = new Set(activeUsersData?.map(event => event.user_id)).size

    // Get premium conversion (simplified - count premium-related events)
    const { data: premiumEvents, error: premiumError } = await supabaseClient
      .from('analytics_events')
      .select('user_id')
      .gte('created_at', startDateStr)
      .lte('created_at', endDateStr)
      .or('event_name.eq.upgrade_premium,event_name.eq.premium_signup')

    if (premiumError) {
      console.error('Error fetching premium events:', premiumError)
    }

    const premiumConversions = new Set(premiumEvents?.map(event => event.user_id)).size

    // Get search analytics (count search-related events)
    const { data: searchEvents, error: searchError } = await supabaseClient
      .from('analytics_events')
      .select('*')
      .gte('created_at', startDateStr)
      .lte('created_at', endDateStr)
      .or('event_name.eq.search,event_name.eq.search_query')

    if (searchError) {
      console.error('Error fetching search events:', searchError)
    }

    const searchAnalytics = {
      total_searches: searchEvents?.length || 0,
      unique_searchers: new Set(searchEvents?.map(event => event.user_id)).size
    }

    // Get AI analytics (count AI-related events)
    const { data: aiEvents, error: aiError } = await supabaseClient
      .from('analytics_events')
      .select('*')
      .gte('created_at', startDateStr)
      .lte('created_at', endDateStr)
      .or('event_name.eq.ai_query,event_name.eq.ai_response,event_name.eq.ai_chat')

    if (aiError) {
      console.error('Error fetching AI events:', aiError)
    }

    const aiAnalytics = {
      total_ai_interactions: aiEvents?.length || 0,
      unique_ai_users: new Set(aiEvents?.map(event => event.user_id)).size
    }

    const dashboardData = {
      period,
      start_date: startDateStr,
      end_date: endDateStr,
      event_counts: eventCounts,
      active_users: activeUsers,
      premium_conversion: {
        conversions: premiumConversions,
        rate: activeUsers > 0 ? (premiumConversions / activeUsers) * 100 : 0
      },
      search_analytics: searchAnalytics,
      ai_analytics: aiAnalytics
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: dashboardData
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Error in dashboard function:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})