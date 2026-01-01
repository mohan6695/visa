from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import asyncio
from datetime import datetime
from supabase import Client
from ..services.optimized_ai_service import OptimizedAIService
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class AutoTaggingService:
    """Service for automatic tagging and clustering of content"""
    
    def __init__(
        self, 
        supabase_client: Client, 
        ai_service: OptimizedAIService,
        embedding_service: EmbeddingService
    ):
        self.supabase = supabase_client
        self.ai_service = ai_service
        self.embedding_service = embedding_service
        
        # Configuration
        self.similarity_threshold = 0.85  # Threshold for similarity-based tag inheritance
        self.max_tags_per_post = 5  # Maximum number of tags per post
        self.max_inherited_tags = 3  # Maximum number of tags to inherit from similar posts
    
    async def auto_tag_post(self, post_id: str, content: str, title: Optional[str] = None) -> List[str]:
        """
        Automatically tag a post using LLM and similarity-based approaches
        
        Args:
            post_id: Post ID
            content: Post content
            title: Optional post title
            
        Returns:
            List[str]: Applied tag names
        """
        try:
            # Combine approaches for better tagging
            llm_tags = await self._tag_with_llm(content, title)
            similarity_tags = await self._find_similar_post_tags(post_id, content)
            
            # Combine and deduplicate tags
            all_tags = list(set(llm_tags + similarity_tags))
            
            # Limit to max tags
            final_tags = all_tags[:self.max_tags_per_post]
            
            # Apply tags to post
            await self._apply_tags_to_post(post_id, final_tags)
            
            return final_tags
        except Exception as e:
            logger.error(f"Error in auto-tagging post {post_id}: {str(e)}")
            return []
    
    async def _tag_with_llm(self, content: str, title: Optional[str] = None) -> List[str]:
        """
        Tag content using LLM classification
        
        Args:
            content: Post content
            title: Optional post title
            
        Returns:
            List[str]: Tag names from LLM
        """
        try:
            # Get available tags
            tags_response = self.supabase.table("tags").select("name, category").execute()
            
            if not tags_response.data:
                logger.warning("No tags found in database")
                return []
            
            # Format tags by category for better context
            tags_by_category = {}
            for tag in tags_response.data:
                category = tag.get("category", "general")
                if category not in tags_by_category:
                    tags_by_category[category] = []
                tags_by_category[category].append(tag["name"])
            
            # Create prompt for LLM
            prompt = f"""You are an expert tagger for visa and immigration content. 
            Analyze the following content and assign the most relevant tags from the provided list.
            
            Content: {title + ': ' if title else ''}{content[:1000]}
            
            Available tags by category:
            """
            
            for category, tags in tags_by_category.items():
                prompt += f"\n{category.upper()}: {', '.join(tags)}"
            
            prompt += """
            
            Select 1-5 most relevant tags from the available tags list.
            Respond with a JSON object in this exact format:
            {"tags": ["tag1", "tag2", "tag3"]}
            
            Only include tags from the provided list. Do not create new tags.
            """
            
            # Call LLM
            response_text, _ = await self.ai_service.call_groq_api(
                prompt=prompt,
                model="llama-3.1-8b-instant",  # Using smaller, faster model for tagging
                max_tokens=100,
                temperature=0.1  # Low temperature for more deterministic results
            )
            
            if not response_text:
                logger.warning("Empty response from LLM for tagging")
                return []
            
            # Parse response
            try:
                # Extract JSON from response (in case there's additional text)
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    response_data = json.loads(json_str)
                    
                    if "tags" in response_data and isinstance(response_data["tags"], list):
                        # Validate tags against available tags
                        available_tags = [tag["name"] for tag in tags_response.data]
                        valid_tags = [tag for tag in response_data["tags"] if tag in available_tags]
                        
                        return valid_tags
                
                logger.warning(f"Invalid JSON format in LLM response: {response_text}")
                return []
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Error in LLM tagging: {str(e)}")
            return []
    
    async def _find_similar_post_tags(self, post_id: str, content: str) -> List[str]:
        """
        Find tags from similar posts using vector similarity
        
        Args:
            post_id: Post ID
            content: Post content
            
        Returns:
            List[str]: Tag names from similar posts
        """
        try:
            # Get embedding for the post
            embedding = await self.embedding_service.get_embedding(content)
            
            if not embedding:
                logger.warning(f"Failed to generate embedding for post {post_id}")
                return []
            
            # Find similar posts using vector similarity
            similar_posts_rpc = self.supabase.rpc(
                'find_similar_posts',
                {
                    'query_embedding': embedding,
                    'match_threshold': self.similarity_threshold,
                    'match_count': 5
                }
            ).execute()
            
            if not similar_posts_rpc.data:
                return []
            
            # Get tags from similar posts
            tag_counts = {}
            
            for similar_post in similar_posts_rpc.data:
                similar_post_id = similar_post.get("id")
                
                if similar_post_id == post_id:
                    continue  # Skip the current post
                
                # Get tags for this similar post
                post_tags_response = self.supabase.table("post_tags").select(
                    "tags(id, name, category)"
                ).eq("post_id", similar_post_id).execute()
                
                if post_tags_response.data:
                    for post_tag in post_tags_response.data:
                        tag = post_tag.get("tags", {})
                        tag_name = tag.get("name")
                        
                        if tag_name:
                            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
            
            # Sort tags by frequency
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Return top tags
            return [tag for tag, _ in sorted_tags[:self.max_inherited_tags]]
            
        except Exception as e:
            logger.error(f"Error finding similar post tags: {str(e)}")
            return []
    
    async def _apply_tags_to_post(self, post_id: str, tag_names: List[str]) -> bool:
        """
        Apply tags to a post
        
        Args:
            post_id: Post ID
            tag_names: List of tag names to apply
            
        Returns:
            bool: True if successful
        """
        try:
            if not tag_names:
                return True  # Nothing to do
            
            # Get tag IDs
            tags_response = self.supabase.table("tags").select("id, name").in_("name", tag_names).execute()
            
            if not tags_response.data:
                logger.warning(f"No matching tags found for names: {tag_names}")
                return False
            
            # Create post_tags entries
            for tag in tags_response.data:
                # Insert with on conflict do nothing to handle duplicates
                self.supabase.table("post_tags").insert({
                    "post_id": post_id,
                    "tag_id": tag["id"]
                }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying tags to post: {str(e)}")
            return False
    
    async def cluster_similar_posts(self, limit: int = 100) -> Dict[str, Any]:
        """
        Cluster similar posts for content organization
        
        Args:
            limit: Maximum number of posts to process
            
        Returns:
            Dict: Clustering results
        """
        try:
            # Get posts without clusters
            posts_response = self.supabase.table("posts").select(
                "id, title, content, embedding"
            ).is_("cluster_id", "null").limit(limit).execute()
            
            if not posts_response.data:
                return {"status": "success", "message": "No posts to cluster", "clusters": 0}
            
            # Group posts by similarity
            clusters = await self._create_clusters(posts_response.data)
            
            # Update posts with cluster IDs
            for cluster_id, post_ids in clusters.items():
                for post_id in post_ids:
                    self.supabase.table("posts").update({
                        "cluster_id": cluster_id
                    }).eq("id", post_id).execute()
            
            return {
                "status": "success",
                "message": f"Clustered {len(posts_response.data)} posts into {len(clusters)} clusters",
                "clusters": len(clusters),
                "posts_processed": len(posts_response.data)
            }
            
        except Exception as e:
            logger.error(f"Error clustering posts: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create_clusters(self, posts: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create clusters from posts based on similarity
        
        Args:
            posts: List of posts to cluster
            
        Returns:
            Dict: Mapping of cluster IDs to post IDs
        """
        try:
            import uuid
            
            # Initialize clusters
            clusters = {}
            processed_posts = set()
            
            # Process each post
            for i, post in enumerate(posts):
                post_id = post.get("id")
                
                if post_id in processed_posts:
                    continue
                
                # Create a new cluster
                cluster_id = str(uuid.uuid4())
                clusters[cluster_id] = [post_id]
                processed_posts.add(post_id)
                
                # Find similar posts for this cluster
                embedding = post.get("embedding")
                if not embedding:
                    continue
                
                # Check similarity with remaining posts
                for j in range(i + 1, len(posts)):
                    other_post = posts[j]
                    other_post_id = other_post.get("id")
                    
                    if other_post_id in processed_posts:
                        continue
                    
                    other_embedding = other_post.get("embedding")
                    if not other_embedding:
                        continue
                    
                    # Calculate similarity
                    similarity = await self.embedding_service.calculate_similarity(embedding, other_embedding)
                    
                    # Add to cluster if similar enough
                    if similarity >= self.similarity_threshold:
                        clusters[cluster_id].append(other_post_id)
                        processed_posts.add(other_post_id)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error creating clusters: {str(e)}")
            return {}
    
    async def process_external_content(self) -> Dict[str, Any]:
        """
        Process external content from staging to live
        
        Returns:
            Dict: Processing results
        """
        try:
            # Get unprocessed external content
            staging_response = self.supabase.table("external_posts_staging").select(
                "id, content, embedding, source"
            ).is_("cluster_id", "null").limit(100).execute()
            
            if not staging_response.data:
                return {"status": "success", "message": "No external content to process", "processed": 0}
            
            # Cluster external content
            clusters = await self._create_external_clusters(staging_response.data)
            
            # Create live external posts from clusters
            live_posts_created = 0
            
            for cluster_id, post_ids in clusters.items():
                # Update staging posts with cluster ID
                for post_id in post_ids:
                    self.supabase.table("external_posts_staging").update({
                        "cluster_id": cluster_id
                    }).eq("id", post_id).execute()
                
                # Get all posts in this cluster
                cluster_posts_response = self.supabase.table("external_posts_staging").select(
                    "content, source, embedding"
                ).eq("cluster_id", cluster_id).execute()
                
                if not cluster_posts_response.data:
                    continue
                
                # Find best content in cluster
                best_content, sources, similarity_score = await self._select_best_content(cluster_posts_response.data)
                
                # Create live external post
                self.supabase.table("external_posts_live").insert({
                    "cluster_id": cluster_id,
                    "best_content": best_content,
                    "similarity_score": similarity_score,
                    "sources": sources,
                    "created_at": datetime.now().isoformat()
                }).execute()
                
                live_posts_created += 1
            
            return {
                "status": "success",
                "message": f"Processed {len(staging_response.data)} external posts into {live_posts_created} live posts",
                "processed": len(staging_response.data),
                "live_posts_created": live_posts_created
            }
            
        except Exception as e:
            logger.error(f"Error processing external content: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create_external_clusters(self, posts: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create clusters from external posts
        
        Args:
            posts: List of external posts to cluster
            
        Returns:
            Dict: Mapping of cluster IDs to post IDs
        """
        # Implementation similar to _create_clusters but with external content specifics
        return await self._create_clusters(posts)
    
    async def _select_best_content(
        self, 
        cluster_posts: List[Dict[str, Any]]
    ) -> Tuple[str, List[str], float]:
        """
        Select the best content from a cluster
        
        Args:
            cluster_posts: List of posts in the cluster
            
        Returns:
            Tuple: (best_content, sources, similarity_score)
        """
        try:
            if not cluster_posts:
                return "", [], 0.0
            
            # If only one post, use it
            if len(cluster_posts) == 1:
                return cluster_posts[0]["content"], [cluster_posts[0]["source"]], 1.0
            
            # Calculate similarity between all posts
            similarity_sum = {}
            
            for i, post in enumerate(cluster_posts):
                post_embedding = post.get("embedding")
                if not post_embedding:
                    continue
                
                similarity_sum[i] = 0.0
                
                for j, other_post in enumerate(cluster_posts):
                    if i == j:
                        continue
                    
                    other_embedding = other_post.get("embedding")
                    if not other_embedding:
                        continue
                    
                    similarity = await self.embedding_service.calculate_similarity(post_embedding, other_embedding)
                    similarity_sum[i] += similarity
            
            # Find post with highest average similarity
            best_index = max(similarity_sum, key=similarity_sum.get)
            best_post = cluster_posts[best_index]
            
            # Calculate average similarity score
            avg_similarity = similarity_sum[best_index] / (len(cluster_posts) - 1) if len(cluster_posts) > 1 else 1.0
            
            # Get unique sources
            sources = list(set(post["source"] for post in cluster_posts if "source" in post))
            
            return best_post["content"], sources, avg_similarity
            
        except Exception as e:
            logger.error(f"Error selecting best content: {str(e)}")
            return "", [], 0.0