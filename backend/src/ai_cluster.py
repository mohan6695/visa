import json
from typing import List, Dict, Any

async def cluster_posts_batched(env, posts: List[Dict[str, Any]], batch_size: int = 25) -> List[Dict[str, Any]]:
    """Cluster posts using Workers AI + Llama"""
    enriched = []
    
    for batch_idx in range(0, len(posts), batch_size):
        batch_posts = posts[batch_idx : batch_idx + batch_size]
        
        # Build docs for clustering
        docs = []
        for idx, post in enumerate(batch_posts):
            docs.append({
                "idx": idx,
                "id": post["id"],
                "title": post["title"],
                "text_snippet": post.get("text_ref", "")[:250]
            })
        
        # AI Clustering Prompt
        cluster_prompt = f"""
        Classify these Stack Overflow posts into ONE category each.
        Categories: database, api-design, frontend, devops, security, performance, architecture, mobile
        
        Output JSON format: [{{"idx": 0, "cluster_id": "category", "relevance": 0.95}}, ...]
        
        Posts:
        {json.dumps(docs)}
        """
        
        try:
            cluster_result = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
                "prompt": cluster_prompt,
                "max_tokens": 1024,
                "temperature": 0.1
            })
            
            clusters = json.loads(cluster_result.response)
        except:
            clusters = [{"idx": i, "cluster_id": "general", "relevance": 0.5} for i in range(len(batch_posts))]
        
        # AI Summarization
        for idx, post in enumerate(batch_posts):
            summary_prompt = f"Summarize in 1 sentence (max 100 chars):\n{post.get('text_ref', '')[:500]}"
            
            try:
                summary_result = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
                    "prompt": summary_prompt,
                    "max_tokens": 50,
                    "temperature": 0.3
                })
                summary = summary_result.response.strip()
            except:
                summary = post.get("text_ref", "")[:100]
            
            cluster_info = next((c for c in clusters if c["idx"] == idx), {"cluster_id": "general", "relevance": 0.5})
            
            enriched.append({
                **post,
                "summary": summary,
                "cluster_id": cluster_info.get("cluster_id", "general"),
                "ai_relevance_score": cluster_info.get("relevance", 0.5)
            })
    
    return enriched
