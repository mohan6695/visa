-- Migration: User-Centric Personal Spaces-2">How to register for H1B cap lottery?</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span>12 answers</span>
                                   
-- This migration creates a comprehensive user-centric data model with personal spaces
-- for interview experiences, private messages, and user interactions

-- =============================================
-- USER PERSONAL SPACES
-- =============================================

 <span class="mx-2">•</span>
                                    <span>2 days ago</span>
                                </div>
                            </div>
                            <div class="post-card p-4-- User personal spaces table (each user gets their own space)
CREATE TABLE IF NOT EXISTS user_spaces (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users bg-gray-50 rounded-lg">
                                <div class="flex items-center mb-2">
                                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text(id) ON DELETE CASCADE UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    bio TEXT,
    profile_image_url TEXT,
    location TEXT,
    website_url TEXT,
    created_at-xs font-medium">EB-2</span>
                                </div>
                                <h4 class="font-semibold text-gray-900 mb-2">PERM Processing Time</h4>
                                TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Analytics counters
    total_interviews INTEGER DEFAULT 0,
    total_posts INTEGER DEFAULT 0,
    total_messages_sent INTEGER DEFAULT 0,
    total_messages_received INTEGER DEFAULT 0,
    total_answers INTEGER DEFAULT 0,
    total_comments INTEGER DEFAULT 0
);

-- User <p class="text-sm text-gray-700 mb-2">Current processing times for PERM applications?</p>
                                <div class="flex items-center text-xs text-gray-500">
                                    <span>8 answers</span>
                                    <span class="mx-2">•</span>
                                    <span>5 days ago</span>
                                </div>
                            </div>
                       's interview experiences (personal space)
CREATE TABLE IF NOT EXISTS interview_experiences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE C </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 3: Groups -->
        <div id="content-groups" class="tab-content">
ASCADE NOT NULL,
    
    -- Interview details
    company_name TEXT NOT NULL,
    position_title TEXT NOT NULL,
    interview_date DATE NOT NULL,
    location_type TEXT CHECK (location_type IN            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Groups Section -->
                <div>
                    <div class="bg-white rounded-xl ('onsite', 'virtual', 'phone')) DEFAULT 'onsite',
    
    -- Content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[],
    
    -- Metadata shadow-lg p-8">
                        <h2 class="text-2xl font-bold text-gray-900 mb-6">Create a US Immigration Group</h2>

                        <div class="
    difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5),
    outcome TEXT CHECK (outcome IN ('selected', 'rejected', 'waiting')),
    is_public BOOLEAN DEFAULTgrid grid-cols-1 gap-6 mb-6">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Group Type</label>
 true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Search optimization
    embedding VECTOR(1536),
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('                                <select id="group-type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:borderenglish', title || ' ' || content || ' ' || company_name || ' ' || position_title)
    ) STORED,
    
    -- Timestamps
    created_at TIMESTAMPTZ-pink-500">
                                    <option value="">Select Group Type</option>
                                    <option value="h1b">H1-B Workers</option>
                                    <option value="f1"> DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_difficulty CHECK (difficulty_rating BETWEEN 1 AND 5)
);

-- UserF-1 Students</option>
                                    <option value="eb1">EB-1 Applicants</option>
                                    <option value="eb2">EB-2 Applicants</option>
                                    <option personal posts (not group-based)
CREATE TABLE IF NOT EXISTS user_posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT value="family">Family Immigration</option>
                                    <option value="general">General Immigration</option>
                                    <option value="professional">Professional Network</option>
                                </select>
                            </div NULL,
    
    -- Post content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    post_type TEXT CHECK (post_type IN ('note', 'question', 'achievement', '>
                        </div>

                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Group Name</label>
                            <inputmilestone', 'general')) DEFAULT 'general',
    
    -- Privacy and visibility
    visibility TEXT CHECK (visibility IN ('public', 'private', 'followers_only')) DEFAULT 'public',
    
 type="text" id="group-name" placeholder="e.g., H1B Warriors 2024" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500">
                        </div>

                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Group Description</label>
                            <textarea id="group-description" rows="3" placeholder="Describe what your group is about..." class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500"></textarea>
                        </div>

                        <!-- Features Builder -->
                        <div class="mb-6">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="text-lg font-semibold text-gray-900">Group Features</h3>
                                <button onclick="clearGroupFeatures()" class="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm transition-colors">
                                    Clear
                                </button>
                            </div>
                            <div class="bg-white rounded-lg shadow p-4 border">
                                <div class="toolbar mb-4    -- Metadata
    tags TEXT[],
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    
    -- Search optimization
    embedding VECTOR(1536),
    search" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                    <div class="chip-group" draggable="true" data-feature="weekly_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || content)
    ) STORED,
    
    -- Timestamps
    created_at TIMESTAMPT-chat" style="padding: 6px 12px; border-radius: 999px; border: 2px solid #10b981; background: #fff; cursor: grab; user-select: none; font-size: 12px;">💬 Weekly Chats</div>
                                    <div class="chip-group" draggable="true" data-feature="mentorship" styleZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User personal comments (replies to user posts or interview experiences)
CREATE TABLE IF NOT EXISTS user_comments (
    id="padding: 6px 12px; border-radius: 999px; border: 2px solid #8b5cf6; background: #fff; cursor: grab; user-select: none; font-size: 12px;">🎯 Mentorship</div>
                                    <div class="chip-group" draggable="true" data-feature="job-board" style="padding UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    
    -- Parent content reference
    parent_type TEXT CHECK (parent_type: 6px 12px; border-radius: 999px; border: 2px solid #f59e0b; background: #fff; cursor: grab; user-select: IN ('user_post', 'interview_experience', 'user_comment')) NOT NULL,
    parent_id UUID NOT NULL,
    
    -- Comment content
    content TEXT NOT NULL,
    
    -- none; font-size: 12px;">💼 Job Board</div>
                                </div>
                                <div class="lane" id="group-features-lane" style="min-height: 120px; border: 2px dashed #ccc; background: #f9f9f9; padding: 12px; border-radius: 8px;">
                                    <p style="color Threading support
    parent_comment_id UUID REFERENCES user_comments(id) ON DELETE CASCADE,
    
    -- Metadata
    is_liked BOOLEAN DEFAULT false,
    like_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- PRIVATE MESSAGING SYSTEM:#999;margin:0;text-align:center;font-size:14px;">Drag features here...</p>
                                </div>
                            </div>
                        </div>

                        <div class="flex justify
-- =============================================

-- Direct conversations between users
CREATE TABLE IF NOT EXISTS direct_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user1_id UUID REFERENCES auth.users(id-center">
                            <button onclick="createGroup()" class="bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white) ON DELETE CASCADE NOT NULL,
    user2_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at px-8 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg">
                                Create Group
                            </button>
                        </div>
                    </div>

                    <!-- Your Groups -->
                    <div class="bg-white rounded-xl shadow-lg p-6 mt-8">
                        <h3 class="text-xl font-bold text-gray-900 mb-6">Your TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata
    is_blocked BOOLEAN DEFAULT false,
    last_message_preview TEXT,
    
    -- Ensure no duplicate conversations
    CONSTRAINT unique Groups</h3>
                        <div id="your-groups" class="space-y-4">
                            <div class="text-center text-gray-500 py-8">
                                <p>No_conversation UNIQUE (user1_id, user2_id),
    CONSTRAINT different_users CHECK (user1_id != user2_id)
);

-- Messages within conversations
CREATE TABLE IF NOT EXISTS direct groups created yet. Create your first group above!</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Popular Groups Sidebar -->
                <div>
                    <div class="bg-white rounded-xl shadow-lg p-6">
                        <h3 class="text-xl font-bold text-gray-900 mb-6">Popular US Groups</h3>
                       _messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES direct_conversations(id) ON DELETE CASCADE NOT NULL,
    sender_id UUID REFERENCES auth.users(id) <div id="popular-groups" class="space-y-4">
                            <div class="group-card p-4 bg-gray-50 rounded-lg">
                                <div class="flex items-center mb ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    
    -- Message status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    is_edited-2">
                                    <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-medium">H1-B</span>
                                </div>
                                 BOOLEAN DEFAULT false,
    edited_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Message read receipts
CREATE TABLE IF<h4 class="font-semibold text-gray-900 mb-2">H1B Transfer Support</h4>
                                <p class="text-sm text-gray-700 mb-2">Helping NOT EXISTS message_read_receipts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    message_id UUID REFERENCES direct_messages(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES H1B workers navigate employer transfers.</p>
                                <div class="flex items-center justify-between text-xs text-gray-500">
                                    <span>2,847 members</span>
                                     auth.users(id) ON DELETE CASCADE NOT NULL,
    read_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate receipts
    UNIQUE(message_id, user_id<button onclick="joinGroup(this)" class="text-blue-600 hover:text-blue-800 font-medium">Join</button>
                                </div>
                            </div>
                            <div class="group-card)
);

-- =============================================
-- USER INTERACTIONS
-- =============================================

-- User likes on user posts and interview experiences
CREATE TABLE IF NOT EXISTS user_likes (
    id UUID DEFAULT gen_random_uuid p-4 bg-gray-50 rounded-lg">
                                <div class="flex items-center mb-2">
                                    <span class="bg-purple-100 text-purple-800 px-2 py-() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    
    -- Liked content reference
    content_type TEXT CHECK (content_type IN ('user_post1 rounded text-xs font-medium">EB-2</span>
                                </div>
                                <h4 class="font-semibold text-gray-900 mb-2">EB2 NIW Warriors', 'interview_experience', 'user_comment')) NOT NULL,
    content_id UUID NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
   </h4>
                                <p class="text-sm text-gray-700 mb-2">National Interest Waiver applicants sharing strategies.</p>
                                <div class="flex items-center justify-between text-xs text-gray-500">
                                    <span>3,156 members</span>
                                    <button onclick="joinGroup(this)" class="text-blue-600 hover:text-blue-800 font-medium">Join -- Unique constraint to prevent duplicate likes
    UNIQUE(user_id, content_type, content_id)
);

-- User follows (for follower-only content)
CREATE TABLE IF NOT EXISTS user_follows (
   </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 4: Visa Information -->
 id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    follower_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    following_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT        <div id="content-visa" class="tab-content">
            <!-- Quick Stats -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate follows
    UNIQUE(follower_id, following_id),
    CONSTRAINT different_users CHECK mb-12">
                <div class="bg-white p-6 rounded-lg shadow-sm border text-center">
                    <div class="text-2xl font-bold text-blue-600 mb-2 (follower_id != following_id)
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- User spaces indexes
CREATE INDEX IF NOT EXISTS idx_user_spaces_user_id ON user">2-6</div>
                    <div class="text-sm text-gray-600">Months Processing</div>
                </div>
                <div class="bg-white p-6 rounded-lg_spaces(user_id);

-- Interview experiences indexes
CREATE INDEX IF NOT EXISTS idx_interview_experiences_user_id ON interview_experiences(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_ex shadow-sm border text-center">
                    <div class="text-2xl font-bold text-green-600 mb-2">85-95%</div>
                    <div class="text-sm textperiences_company ON interview_experiences(company_name);
CREATE INDEX IF NOT EXISTS idx_interview_experiences_date ON interview_experiences(interview_date);
CREATE INDEX IF NOT EXISTS idx-gray-600">Success Rate</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-sm border text-center">
                    <div class="text-2xl_interview_experiences_is_public ON interview_experiences(is_public);
CREATE INDEX IF NOT EXISTS idx_interview_experiences_embedding ON interview_experiences USING ivfflat (embedding vector_c font-bold text-purple-600 mb-2">$160-$2,805</div>
                    <div class="text-sm text-gray-600">Visa Fees</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-sm border text-center">
                    <div class="text-2xl font-bold text-orange-600 mb-2">7</divosine_ops) WITH (lists = 100);

-- User posts indexes
CREATE INDEX IF NOT EXISTS idx_user_posts_author_id ON user_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_user_posts_created_at ON user_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_posts_visibility ON user_posts(visibility);
CREATE INDEX IF NOT EXISTS idx_user_posts_embedding ON user_posts USING ivfflat>
                    <div class="text-sm text-gray-600">Major Visa Types</div>
                </div>
            </div>

            <!-- Visa Types Grid -->
            <div class="mb- (embedding vector_cosine_ops) WITH (lists = 100);

-- User comments indexes
CREATE INDEX IF NOT EXISTS idx_user_comments_parent ON user_comments(parent_type, parent_id);
CREATE INDEX IF12">
                <h2 class="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                    <svg class="w-8 h-8 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke NOT EXISTS idx_user_comments_author_id ON user_comments(author_id);
CREATE INDEX IF NOT EXISTS idx_user_comments_parent_comment ON user_comments(parent_comment_id);

-- Direct conversations indexes
CREATE INDEX IF NOT EXISTS idx_direct_conversations_user1 ON direct_conversations(user1_id);
CREATE INDEX IF NOT EXISTS idx_direct_conversations_user2 ON direct_conversations(user2_id);
CREATE INDEX IF-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2 NOT EXISTS idx_direct_conversations_last_message ON direct_conversations(last_message_at DESC);

-- Direct messages indexes
CREATE INDEX IF NOT EXISTS idx_direct_messages_conversation ON direct_messages(conversation_idH5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 );
CREATE INDEX IF NOT EXISTS idx_direct_messages_created_at ON direct_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_direct_messages_sender ON direct_messages(sender_id);

-- Message read receipts indexes
00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 CREATE INDEX IF NOT EXISTS idx_message_read_receipts_message ON message_read_receipts(message_id);
CREATE INDEX IF NOT EXISTS idx_message_read_receipts_user ON message_read_receipts(user2 0 012 2v2M7 7h10"></path>
                    </svg>
                    Popular US Visa Types
                </h2>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- H1-B Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm border" onclick="selectVisa('h1b')">
                        <div class="flex items-center mb-4">
                            <div class="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                            <h3 class="text-lg font-semibold text-gray-900">H-1B Visa</h3>
                            <span class="ml-auto text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Work</span>
                        </div>
                        <p class="text-gray-600 text-sm mb-4">For skilled workers in specialty occupations</p>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="_id);

-- User likes indexes
CREATE INDEX IF NOT EXISTS idx_user_likes_content ON user_likes(content_type, content_id);
CREATE INDEX IF NOT EXISTS idx_user_likes_user ON user_ltext-gray-500">Processing:</span>
                                <span class="font-medium">2-6 months</span>
                            </div>
                            <div class="flex justify-between">
                                <spanikes(user_id);

-- User follows indexes
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following class="text-gray-500">Fee:</span>
                                <span class="font-medium">$190</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Validity:</span>
                                <span class="font-medium">3 years</span>
                            </div>
                        </div>
                    </div>

                    <!-- F- ON user_follows(following_id);

-- =============================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on all user-centric tables
ALTER TABLE user_spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_experiences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE1 Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm border" onclick="selectVisa('f1')">
                        <div class="flex items-center mb- direct_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE direct_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_read_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_likes ENABLE ROW LEVEL SECURITY;
4">
                            <div class="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                            <h3 class="text-lg font-semibold text-gray-900ALTER TABLE user_follows ENABLE ROW LEVEL SECURITY;

-- User spaces policies
CREATE POLICY "Users can view their own space" ON user_spaces
    FOR SELECT USING (auth.uid() = user">F-1 Visa</h3>
                            <span class="ml-auto text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Student</span>
                        _id);

CREATE POLICY "Users can update their own space" ON user_spaces
    FOR UPDATE USING (auth.uid() = user_id);

-- Interview experiences policies
CREATE POLICY "Users can view</div>
                        <p class="text-gray-600 text-sm mb-4">For international students</p>
                        <div class="space-y-2 text-sm">
                            <div class=" public interview experiences" ON interview_experiences
    FOR SELECT USING (is_public = true);

CREATE POLICY "Users can view their own interview experiences" ON interview_experiences
    FOR SELECTflex justify-between">
                                <span class="text-gray-500">Processing:</span>
                                <span class="font-medium">2-4 months</span>
                            </div>
                            <div USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own interview experiences" ON interview_experiences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE class="flex justify-between">
                                <span class="text-gray-500">Fee:</span>
                                <span class="font-medium">$160</span>
                            </div>
                            <div POLICY "Users can update their own interview experiences" ON interview_experiences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own interview experiences" ON class="flex justify-between">
                                <span class="text-gray-500">Validity:</span>
                                <span class="font-medium">Study period</span>
                            </div>
                        </div interview_experiences
    FOR DELETE USING (auth.uid() = user_id);

-- User posts policies
CREATE POLICY "Users can view public user posts" ON user_posts
    FOR SELECT USING>
                    </div>

                    <!-- EB-1 Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm border" onclick="selectVisa('eb1')">
                        (
        visibility = 'public' OR
        (visibility = 'followers_only' AND auth.uid() IN (
            SELECT following_id FROM user_follows WHERE follower_id = user <div class="flex items-center mb-4">
                            <div class="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                            <h3 class="text-lg font-semibold text-gray-900">EB-1 Visa</h3>
                            <span class="ml-auto text-xs bg-orange-100 text-orange-800 px-2 py-_posts.author_id
        )) OR
        auth.uid() = author_id
    );

CREATE POLICY "Users can create their own posts" ON user_posts
    FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update their own posts" ON user_posts
    FOR UPDATE USING (auth.uid() = author_id);

CREATE POLICY "Users can delete their own posts1 rounded">Immigration</span>
                        </div>
                        <p class="text-gray-600 text-sm mb-4">Priority workers & extraordinary ability</p>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Processing:</span>
                                <span class="font-medium">8-15" ON user_posts
    FOR DELETE USING (auth.uid() = author_id);

-- User comments policies
CREATE POLICY "Users can view comments on accessible content" ON user_comments
    FOR SELECT USING (
        auth.uid() = author_id OR
        EXISTS (
            SELECT 1 FROM user_posts
            WHERE user_posts.id = user_comments.parent_id
            AND user_comments.parent_type = months</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Fee:</span>
                                <span class="font-medium">$2,805</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Validity:</span>
                                <span class="font-medium 'user_post'
            AND (
                user_posts.visibility = 'public' OR
                (user_posts.visibility = 'followers_only' AND auth.uid() IN (
                    SELECT following_id FROM user_follows WHERE follower_id = user_posts.author_id
                )) OR
                auth.uid() = user_posts.author_id
            )
        )
    );

CREATE POLICY "Users can create">Permanent</span>
                            </div>
                        </div>
                    </div>

                    <!-- EB-2 Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm comments" ON user_comments
    FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update their own comments" ON user_comments
    FOR UPDATE USING (auth.uid border" onclick="selectVisa('eb2')">
                        <div class="flex items-center mb-4">
                            <div class="w-3 h-3 bg-purple-500 rounded-full mr-3"></div>
                            <h3 class="text-lg font-semibold text-gray-900">EB-2 Visa</h3>
                            <span class="ml-auto text-xs bg() = author_id);

CREATE POLICY "Users can delete their own comments" ON user_comments
    FOR DELETE USING (auth.uid() = author_id);

-- Direct conversations policies
CREATE POLICY "Users can view their own conversations" ON direct_conversations
    FOR SELECT USING (auth.uid() = user1_id OR auth.uid() = user2_id);

CREATE POLICY "Users can create conversations-purple-100 text-purple-800 px-2 py-1 rounded">Immigration</span>
                        </div>
                        <p class="text-gray-600 text-sm mb-4">Advanced degree" ON direct_conversations
    FOR INSERT WITH CHECK (auth.uid() = user1_id OR auth.uid() = user2_id);

-- Direct messages policies
CREATE POLICY "Users can view professionals</p>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Processing:</span>
                                messages in their conversations" ON direct_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM direct_conversations
            WHERE direct_conversations.id = direct_messages.conversation_id <span class="font-medium">12-24 months</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Fee:</span
            AND (direct_conversations.user1_id = auth.uid() OR direct_conversations.user2_id = auth.uid())
        )
    );

CREATE POLICY "Users can send messages" ON>
                                <span class="font-medium">$2,805</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Validity direct_messages
    FOR INSERT WITH CHECK (
        auth.uid() = sender_id AND
        EXISTS (
            SELECT 1 FROM direct_conversations
            WHERE direct_conversations.id = direct:</span>
                                <span class="font-medium">Permanent</span>
                            </div>
                        </div>
                    </div>

                    <!-- L-1 Visa -->
                    <div class="visa_messages.conversation_id
            AND (direct_conversations.user1_id = auth.uid() OR direct_conversations.user2_id = auth.uid())
            AND direct_conversations.is_blocked-card bg-white p-6 rounded-lg shadow-sm border" onclick="selectVisa('l1')">
                        <div class="flex items-center mb-4">
                            <div class="w- = false
        )
    );

CREATE POLICY "Users can update their own messages" ON direct_messages
    FOR UPDATE USING (auth.uid() = sender_id);

-- Message read receipts policies
CREATE3 h-3 bg-indigo-500 rounded-full mr-3"></div>
                            <h3 class="text-lg font-semibold text-gray-900">L-1 Visa</h3 POLICY "Users can view read receipts on their messages" ON message_read_receipts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM direct_messages
            WHERE direct_messages.id =>
                            <span class="ml-auto text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">Work</span>
                        </div>
                        <p class message_read_receipts.message_id
            AND direct_messages.sender_id = auth.uid()
        )
    );

CREATE POLICY "Users can update read receipts on their received messages" ON message_read_receipts
    FOR ALL USING (auth.uid() = user_id);

-- User likes policies
CREATE POLICY "Users can view likes on accessible content" ON user_likes
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_posts
            WHERE user_posts.id = user_likes.content_id
            AND user_likes.content_type = 'user_post'
            AND (
                user_posts.visibility = 'public' OR
                (user_posts.visibility = 'followers_only' AND auth.uid() IN (
                    SELECT following_id FROM user_follows WHERE follower_id = user_posts.author_id
                )) OR
                auth.uid() = user_posts.author_id
            )
        )
        OR
        EXISTS (
            SELECT 1 FROM interview_experiences
            WHERE interview_experiences.id = user_likes.content_id
            AND user_likes.content_type = 'interview_experience'
            AND (interview_experiences.is="text-gray-600 text-sm mb-4">Intra-company transfers</p>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                               _public = true OR auth.uid() = interview_experiences.user_id)
        )
    );

CREATE POLICY "Users can manage their own likes" ON user_likes
    FOR ALL USING (auth <span class="text-gray-500">Processing:</span>
                                <span class="font-medium">1-4 months</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Fee:</span>
                                <span class="font-medium">$190</span>
                            </div>
                            <div class="flex justify-between.uid() = user_id);

-- User follows policies
CREATE POLICY "Users can view their own follows" ON user_follows
    FOR SELECT USING (auth.uid() = follower_id OR auth.uid">
                                <span class="text-gray-500">Validity:</span>
                                <span class="font-medium">1-7 years</span>
                            </div>
                        </div>
                    () = following_id);

CREATE POLICY "Users can follow others" ON user_follows
    FOR INSERT WITH CHECK (auth.uid() = follower_id);

CREATE POLICY "Users can unfollow others" ON user_follows
    FOR DELETE USING (auth.uid() = follower_id);

-- =============================================
-- FUNCTIONS FOR BUSINESS LOGIC
-- =============================================

-- Function to update</div>

                    <!-- O-1 Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm border" onclick="selectVisa('o1')">
                        <div class user space analytics
CREATE OR REPLACE FUNCTION update_user_space_analytics(user_uuid UUID)
RETURNS void AS $$
BEGIN
    UPDATE user_spaces
    SET 
        total_interviews = (SELECT COUNT(*) FROM interview_experiences WHERE user_id = user_uuid),
        total_posts = (SELECT COUNT(*) FROM user_posts WHERE author_id = user_uuid),
        total_answers = (SELECT COUNT(*) FROM user_comments WHERE author_id = user_comments.parent_type = 'user_post'),
        total_comments = (SELECT COUNT(*) FROM user_comments WHERE author_id = user_uuid),
        updated_at = NOW()
    WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's personal feed
CREATE OR REPLACE FUNCTION get_user_personal_feed(
    user_uuid UUID,
    limit_count INTEGER DEFAULT 20,
    offset_count INTEGER DEFAULT 0
)
RETURNS="flex items-center mb-4">
                            <div class="w-3 h-3 bg-pink-500 rounded-full mr-3"></div>
                            <h3 class="text-lg TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    content_type TEXT,
    author_id UUID,
    created_at TIMESTAMPTZ,
    like_count INTEGER font-semibold text-gray-900">O-1 Visa</h3>
                            <span class="ml-auto text-xs bg-pink-100 text-pink-800 px-2 py-,
    comment_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH user_feed AS (
        -- Public posts from followed users
        SELECT1 rounded">Work</span>
                        </div>
                        <p class="text-gray-600 text-sm mb-4">Individuals with extraordinary ability</p>
                        <div class="space-y 
            up.id,
            up.title,
            up.content,
            'user_post' as content_type,
            up.author_id,
            up.created_at,
            up.like_count,
           -2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Processing:</span>
                                <span class="font-medium">2-4 months (SELECT COUNT(*) FROM user_comments WHERE parent_type = 'user_post' AND parent_id = up.id) as comment_count
        FROM user_posts up
        WHERE up.visibility =</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Fee:</span>
                                <span class="font-medium">$190</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Validity:</span>
                                <span class="font-medium">3 years 'public'
        AND up.author_id IN (
            SELECT following_id FROM user_follows WHERE follower_id = user_uuid
        )
        
        UNION ALL
        
        -- Public interview experiences from</span>
                            </div>
                        </div>
                    </div>

                    <!-- Tourist Visa -->
                    <div class="visa-card bg-white p-6 rounded-lg shadow-sm border" onclick=" followed users
        SELECT 
            ie.id,
            ie.title,
            ie.content,
            'interview_experience' as content_type,
            ie.user_id as author_id,
            ie.created_at,
            0 as like_count, -- Interview experiences don't have likes yet
            0 as comment_count -- Interview experiences don't have comments yet
        FROMselectVisa('tourist')">
                        <div class="flex items-center mb-4">
                            <div class="w-3 h-3 bg-gray-500 rounded-full mr-3"> interview_experiences ie
        WHERE ie.is_public = true
        AND ie.user_id IN (
            SELECT following_id FROM user_follows WHERE follower_id = user_uuid
        )
    )
</div>
                            <h3 class="text-lg font-semibold text-gray-900">B1/B2 Tourist</h3>
                            <span class="ml-auto text-xs bg-gray-100    SELECT * FROM user_feed
    ORDER BY created_at DESC
    LIMIT limit_count OFFSET offset_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search text-gray-800 px-2 py-1 rounded">Tourist</span>
                        </div>
                        <p class="text-gray-600 text-sm mb-4">Business & tourism visits user's personal content
CREATE OR REPLACE FUNCTION search_user_content(
    user_uuid UUID,
    search_query TEXT,
    content_types TEXT[] DEFAULT ARRAY['user</p>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Processing:</span>
                                _post', 'interview_experience']
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    content_type TEXT,
    created_at TIMESTAMPTZ,
    rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH search_results AS (
        -- Search user posts
        SELECT 
            up.id,
<span class="font-medium">3-5 days</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Fee:</span>
                                <span class="font-medium">$160</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Validity:</span>
            up.title,
            up.content,
            'user_post' as content_type,
            up.created_at,
            ts_rank(up.search_vector, plainto_tsquery('english', search_query                                <span class="font-medium">10 years</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Content Area for selected visa)) as rank
        FROM user_posts up
        WHERE up.author_id = user_uuid
        AND 'user_post' = ANY(content_types)
        AND up.search_vector @@ plainto_tsquery -->
            <div id="visa-content-area" class="bg-white rounded-lg shadow-sm border p-8">
                <div class="text-center py-12">
                    <div class="w('english', search_query)
        
        UNION ALL
        
        -- Search interview experiences
        SELECT 
            ie.id,
            ie.title,
            ie.content,
            'interview_experience' as-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-12 h-12 text-blue-600" fill=" content_type,
            ie.created_at,
            ts_rank(ie.search_vector, plainto_tsquery('english', search_query)) as rank
        FROM interview_experiences ie
        WHERE ienone" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d=".user_id = user_uuid
        AND 'interview_experience' = ANY(content_types)
        AND ie.search_vector @@ plainto_tsquery('english', search_query)
    )
    SELECT *M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 FROM search_results
    ORDER BY rank DESC, created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- TRIGGERS FOR AUTOMATION
-- =============================================

 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M-- Function to create user space when user is created
CREATE OR REPLACE FUNCTION create_user_space()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_spaces (5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 user_id, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.email)
    );
    RETURN NEW;
END2v2M7 7h10"></path>
                        </svg>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-900 mb-4">;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user space
CREATE TRIGGER trigger_create_user_space
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTESelect a Visa Type Above</h3>
                    <p class="text-gray-600 text-lg max-w-2xl mx-auto">
                        Click on any visa type to view detailed information, requirements FUNCTION create_user_space();

-- Function to update user space analytics
CREATE OR REPLACE FUNCTION trigger_update_user_space_analytics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE, and community experiences.
                    </p>
                </div>
            </div>

            <!-- Related Communities -->
            <div class="mt-12 bg-gray-100 rounded-lg p-8">
_NAME = 'interview_experiences' THEN
        PERFORM update_user_space_analytics(NEW.user_id);
    ELSIF TG_TABLE_NAME = 'user_posts' THEN
        PER                <h3 class="text-2xl font-bold text-gray-900 mb-6 text-center">Related US Immigration Communities</h3>
                <div class="grid grid-cols-FORM update_user_space_analytics(NEW.author_id);
    ELSIF TG_TABLE_NAME = 'user_comments' THEN
        PERFORM update_user_space_analytics(NEW.author_id);
    END1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-6 rounded-lg shadow-sm border">
                        <h4 class="font-semibold text-gray- IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Triggers to update analytics
CREATE TRIGGER trigger_update_analytics_inter900 mb-2">🇺🇸 H1B Workers Network</h4>
                        <p class="text-gray-600 text-sm mb-4">Support for H1-B visa holdersview_experiences
    AFTER INSERT OR DELETE ON interview_experiences
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_user_space_analytics();

CREATE TRIGGER trigger_update_analytics_user_posts
    AFTER INSERT OR DELETE ON user_posts
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_user_space_analytics();

CREATE TRIGGER trigger_update_analytics_user and applicants</p>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-500">4,523 members</span>
                            <button class="_comments
    AFTER INSERT OR DELETE ON user_comments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_user_space_analytics();

-- =============================================
-- VIEWS FOR COMMON QUERIESbg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 transition-colors">Join</button>
                        </div>
                    </div>

                    <div class
-- =============================================

-- View for user's personal dashboard
CREATE OR REPLACE VIEW user_dashboard AS
SELECT 
    us.user_id,
    us.display_name,
    us.bio,
="bg-white p-6 rounded-lg shadow-sm border">
                        <h4 class="font-semibold text-gray-900 mb-2">🎓 F1 Students Hub</h4>
                        <p class="text-gray-600 text-sm mb-4">Student visa holders and applicants</p>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-500">3,892 members</span>
                            <button class="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 transition-colors">Join</button>
                        </div>
                    </div>

                    <div class="bg-white p-6 rounded-lg shadow-sm border">
                        <h4 class="font-semibold text-gray-900 mb-2">🏆 EB Immigration Champions</h4>
                        <p class="text-gray-600 text-sm mb-4">Employment-based immigration discussions</p>
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-500">2,734 members</span>
                            <button class="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 transition-colors">Join</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    us.total_interviews,
    us.total_posts,
    us.total_answers,
    us.total_comments,
    -- Recent activity
    (
        SELECT COUNT(*)::    </div>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white mt-16">
        <div class="max-w-7xl mx-auto px-4 py-INTEGER
        FROM interview_experiences ie
        WHERE ie.user_id = us.user_id
        AND ie.created_at > NOW() - INTERVAL '30 days'
    ) as12">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div>
                    <div class="flex items-center space-x-3 recent_interviews,
    (
        SELECT COUNT(*)::INTEGER
        FROM user_posts up
        WHERE up.author_id = us.user_id
        AND up.created_at > NOW() - INTERVAL mb-4">
                        <div class="w-8 h-8 bg-pink-600 rounded-full flex items-center justify-center">
                            <span class="text-white font-bold">V '30 days'
    ) as recent_posts,
    -- Engagement
    (
        SELECT COALESCE(SUM(up.like_count), 0)
        FROM user_posts up
</span>
                        </div>
                        <span class="text-xl font-bold">Visa Platform</span>
                    </div>
                    <p class="text-gray-400">
                        Your trusted partner for        WHERE up.author_id = us.user_id
    ) as total_likes_received,
    (
        SELECT COUNT(*)::INTEGER
        FROM user_follows
        WHERE following_id = us global visa information and immigration guidance.
                    </p>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Quick Links</h4>
                    .user_id
    ) as followers_count,
    (
        SELECT COUNT(*)::INTEGER
        FROM user_follows
        WHERE follower_id = us.user_id
    ) as following_count
FROM user_spaces us;

-- View for conversation summaries
CREATE OR REPLACE VIEW conversation_summaries AS
SELECT 
    dc.id as conversation_id,
   <ul class="space-y-2 text-gray-400">
                        <li><a href="index.html" class="hover:text-white transition-colors">Home</a></li>
                        <li><a href="countries.html" class="hover:text-white transition-colors">All Countries</a></li>
                        <li><a href="communities.html" class="hover:text-white transition dc.user1_id,
    dc.user2_id,
    dc.last_message_at,
    dc.last_message_preview,
    dc.is_blocked,
    -- Message counts
    (
-colors">Communities</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Popular Countries</h4        SELECT COUNT(*)::INTEGER
        FROM direct_messages dm
        WHERE dm.conversation_id = dc.id
        AND dm.created_at > NOW() - INTERVAL '24 hours'
   >
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="country-usa.html" class="hover:text-white transition-colors">United States</a ) as recent_message_count,
    -- Unread count
    (
        SELECT COUNT(*)::INTEGER
        FROM direct_messages dm
        WHERE dm.conversation_id = dc.id
        AND dm.sender_id != auth.uid()
        AND dm.is_read = false
    ) as unread_count
FROM direct_conversations dc
WHERE dc.user1_id =></li>
                        <li><a href="country-canada.html" class="hover:text-white transition-colors">Canada</a></li>
                        <li><a href="country-uk auth.uid() OR dc.user2_id = auth.uid();

-- =============================================
-- COMMENTS
-- =============================================

/*
This migration provides:

1. User Personal.html" class="hover:text-white transition-colors">United Kingdom</a></li>
                        <li><a href="country-australia.html" class="hover:text-white transition-colors">Australia</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="font-semibold mb-4">Support</h4>
                    <ul class=" Spaces:
   - Each user gets their own personal space for managing their content
   - Analytics counters for engagement tracking
   - Profile information and biospace-y-2 text-gray-400">
                        <li><a href="help.html" class="hover:text-white transition-colors">Help Center</a></li>
                        <li><a management

2. Interview Experiences:
   - Structured storage for interview experiences
   - Public/private visibility controls
   - Search optimization with embeddings and tsvector
   - Difficulty ratings and outcomes tracking

3. Personal Posts:
   - User-generated content separate from group posts
   - Visibility href="contact.html" class="hover:text-white transition-colors">Contact Us</a></li>
                        <li><a href="privacy.html" class="hover:text-white transition-colors"> controls (public, private, followers-only)
   - Full search capabilities with embeddings

4. Private Messaging System:
   - Direct conversations betweenPrivacy Policy</a></li>
                        <li><a href="terms.html" class="hover:text-white transition-colors">Terms of Service</a></li>
                    </ul>
                </div>
            </div>
            <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
                <p>© 2024 Visa Platform users
   - Message read receipts
   - Blocking functionality
   - Real-time message threading

5. User Interactions:
   - Like system for posts and interview. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script>
        let currentRating = { interview: 0, immigration: 0 };
        experiences
   - Follow system for content subscriptions
   - Comprehensive engagement tracking

6. Performance Optimizations:
   - Strategic indexes on all frequently queried columns
   - Vector similarity indexes for semantic search
   - Compound indexes for complex queries

7. Security:
   - RLS policies ensuring let postedExperiences = [];

        // Tab switching
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
                btn.classList.add('bg-gray-100', 'text-gray-700', 'hover:bg-gray-200');
            });
            document.getElementById users can only access their own data
   - Public content properly exposed
   - Follower-only content correctly protected

8(`tab-${tabName}`).classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.remove('bg-gray-100', 'text-gray-700. Business Logic Functions:
   - Personal feed generation
   - Content search capabilities
   - Analytics updating triggers

This schema enables each user to have their own private space while allowing
for social interactions through follows, likes, and private messaging.
*/
