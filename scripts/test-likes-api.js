#!/usr/bin/env node

import fetch from 'node-fetch';

const BASE_URL = 'http://localhost:3000';
const TEST_POST_ID = 'test-post-' + Date.now();
const TEST_USER_ID = 'test-user-' + Date.now();

async function testLikesAPI() {
  console.log('🧪 Testing Likes API...\n');

  try {
    // Test 1: Like a post
    console.log('1. Testing likePost:');
    const likeResponse = await fetch(`${BASE_URL}/api/likes/post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        postId: TEST_POST_ID,
        userId: TEST_USER_ID,
        action: 'like'
      })
    });

    if (!likeResponse.ok) {
      throw new Error(`Failed to like post: ${likeResponse.status}`);
    }

    const likeResult = await likeResponse.json();
    console.log('✅ Success:', likeResult);

    // Test 2: Check if post is liked
    console.log('\n2. Testing checkPostLike:');
    const checkResponse = await fetch(`${BASE_URL}/api/likes/post?postId=${TEST_POST_ID}&userId=${TEST_USER_ID}`);

    if (!checkResponse.ok) {
      throw new Error(`Failed to check post like: ${checkResponse.status}`);
    }

    const checkResult = await checkResponse.json();
    console.log('✅ Success:', checkResult);

    // Verify that the post is liked
    if (!checkResult.liked) {
      throw new Error('❌ Post should be liked');
    }

    // Test 3: Unlike the post
    console.log('\n3. Testing unlikePost:');
    const unlikeResponse = await fetch(`${BASE_URL}/api/likes/post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        postId: TEST_POST_ID,
        userId: TEST_USER_ID,
        action: 'unlike'
      })
    });

    if (!unlikeResponse.ok) {
      throw new Error(`Failed to unlike post: ${unlikeResponse.status}`);
    }

    const unlikeResult = await unlikeResponse.json();
    console.log('✅ Success:', unlikeResult);

    // Test 4: Verify post is unliked
    console.log('\n4. Verifying post is unliked:');
    const check2Response = await fetch(`${BASE_URL}/api/likes/post?postId=${TEST_POST_ID}&userId=${TEST_USER_ID}`);

    if (!check2Response.ok) {
      throw new Error(`Failed to check post like: ${check2Response.status}`);
    }

    const check2Result = await check2Response.json();
    console.log('✅ Success:', check2Result);

    if (check2Result.liked) {
      throw new Error('❌ Post should be unliked');
    }

    console.log('\n🎉 All API tests passed!');
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  }
}

// Run tests
testLikesAPI();
