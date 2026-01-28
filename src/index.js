export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.slice(1);
    
    if (path === "run") {
      return await runProducer(env, ctx);
    } else if (path === "list") {
      return await listBucketContents(env, ctx);
    } else if (path === "health") {
      return new Response(JSON.stringify({ status: "healthy" }), {
        headers: { "Content-Type": "application/json" }
      });
    }
    
    return new Response("R2 → Supabase Pipeline. /run to process new_posts.json, /list to list bucket contents", {
      headers: { "Content-Type": "text/plain" }
    });
  },
  
  async queue(batch, env, ctx) {
    return await handleQueueMessages(batch, env, ctx);
  }
};

async function listBucketContents(env, ctx) {
  try {
    const bucket = env.MY_BUCKET;
    const objectsResult = await bucket.list();
    console.log("Bucket list result:", JSON.stringify(objectsResult));
    return new Response(JSON.stringify(objectsResult), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    console.error("Error listing bucket contents:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}

async function runProducer(env, ctx) {
  try {
    const bucket = env.MY_BUCKET;
    const processedKeysKV = env.PROCESSED_KEYS;
    const queue = env.PROCESS_QUEUE;

    console.log("Listing bucket contents...");
    const objectsResult = await bucket.list();
    console.log("Bucket list result:", JSON.stringify(objectsResult));
    
    let processedCount = 0;
    let failedCount = 0;
    const MAX_BATCH_SIZE = 100000; // Keep messages under 128KB limit

    if (objectsResult.objects) {
      for (const obj of objectsResult.objects) {
        const key = obj.key;
        console.log("Found object:", key);
        
        if (key.endsWith("new_posts.json")) {
          const isProcessed = await processedKeysKV.get(key);
          console.log("Is processed:", isProcessed);
          
          if (isProcessed) {
            continue;
          }

          try {
            console.log("Downloading object...");
            const response = await bucket.get(key);
            if (!response) {
              console.error("No response from bucket.get()");
              failedCount++;
              continue;
            }

            const fileContent = await response.text();
            console.log("File content length:", fileContent.length);
            const posts = JSON.parse(fileContent);

            console.log(`Processing ${posts.length} posts in batches...`);
            
            // Split posts into batches that fit within queue message size limit
            const batches = [];
            let currentBatch = [];
            let currentSize = 0;

            for (const post of posts) {
              const postSize = JSON.stringify(post).length;
              
              if (currentSize + postSize > MAX_BATCH_SIZE) {
                batches.push(currentBatch);
                currentBatch = [];
                currentSize = 0;
              }
              
              currentBatch.push(post);
              currentSize += postSize;
            }
            
            if (currentBatch.length > 0) {
              batches.push(currentBatch);
            }

            console.log(`Split into ${batches.length} batches`);
            
            // Send each batch to queue
            for (let i = 0; i < batches.length; i++) {
              const batch = batches[i];
              console.log(`Sending batch ${i+1}/${batches.length} with ${batch.length} posts...`);
              
              await queue.send(JSON.stringify({ 
                key, 
                posts: batch, 
                batchNumber: i + 1, 
                totalBatches: batches.length 
              }));
              
              processedCount += batch.length;
            }
            
            await processedKeysKV.put(key, new Date().toISOString());
            console.log("Successfully processed:", key);
            
          } catch (error) {
            console.error(`Error processing ${key}:`, error);
            console.error(`Error stack:`, error.stack);
            failedCount++;
          }
        }
      }
    }

    const result = { processed: processedCount, failed: failedCount };
    console.log("Processed result:", JSON.stringify(result));
    
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    console.error("Fatal error in runProducer:", error);
    console.error("Fatal error stack:", error.stack);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}

async function handleQueueMessages(batch, env, ctx) {
  try {
    const supabaseUrl = env.SUPABASE_URL;
    const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;

    for (const message of batch.messages) {
      const data = JSON.parse(message.body);
      const posts = data.posts;
      const key = data.key;

      console.log(`Processing batch ${data.batchNumber}/${data.totalBatches} from ${key}`);
      
      for (const post of posts) {
        try {
          // Generate unique post ID and R2 key
          const postId = crypto.randomUUID();
          const r2Key = `posts/${postId}`;

          // Upload full content to R2
          const contentPayload = {
            title: post.title,
            text: post.content,
            url: post.url || '',
            createdAt: new Date().toISOString(),
            commentCount: post.comments?.length || 0,
            comments: post.comments?.map(c => ({
              text: c.text,
              createdAt: c.createdAt?.toISOString() || new Date().toISOString(),
              userId: c.userId || 'anonymous'
            })) || []
          };

          await env.MY_BUCKET.put(`${r2Key}/content.json`, JSON.stringify(contentPayload));

          // Create metadata in Supabase
          await fetch(`${supabaseUrl}/rest/v1/posts`, {
            method: "POST",
            headers: {
              "apikey": serviceRoleKey,
              "Authorization": `Bearer ${serviceRoleKey}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              id: postId,
              title: post.title,
              url: post.url || '',
              group_id: post.group_id || 'default',
              r2_key: r2Key,
              comment_count: post.comments?.length || 0,
              created_user_id: post.user_id || 'anonymous',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            })
          });

          // Add comments to Supabase (if any)
          if (post.comments && post.comments.length > 0) {
            const commentsData = post.comments.map((comment, index) => ({
              id: `${postId}_comment_${index}`,
              post_id: postId,
              text: comment.text,
              user_id: comment.userId || 'anonymous',
              created_at: comment.createdAt?.toISOString() || new Date().toISOString()
            }));

            await fetch(`${supabaseUrl}/rest/v1/comments`, {
              method: "POST",
              headers: {
                "apikey": serviceRoleKey,
                "Authorization": `Bearer ${serviceRoleKey}`,
                "Content-Type": "application/json"
              },
              body: JSON.stringify(commentsData)
            });
          }

          console.log(`Successfully processed post: ${postId}`);
        } catch (error) {
          console.error("Error processing post:", error);
        }
      }
    }

    return new Response(JSON.stringify({ status: "success" }), {
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    console.error("Queue handler error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
