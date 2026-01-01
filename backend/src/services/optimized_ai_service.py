from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import hashlib
import time
import asyncio
from datetime import datetime, timedelta
from redis.asyncio import Redis
from ..core.config import settings
from ..services.embedding_service import EmbeddingService
from ..core.redis import CacheService, AICacheService

logger = logging.getLogger(__name__)

class OptimizedAIService:
    """
    Optimized service for AI-powered Q&A and content generation
    with enhanced caching and performance optimizations
    """
    
    def __init__(self, redis_client: Redis, embedding_service: EmbeddingService):
        self.redis = redis_client
        self.embedding_service = embedding_service
        self.cache_service = CacheService()
        self.ai_cache = AICacheService()
        
        # Cache configuration
        self.cache_ttl = 7200  # 2 hours default TTL
        self.cache_ttl_short = 3600  # 1 hour for less stable content
        self.semantic_threshold = 0.92  # Threshold for semantic similarity in cache
        
        # Performance metrics
        self.total_requests = 0
        self.cache_hits = 0
        self.llm_calls = 0
        self.avg_response_time = 0
    
    async def _generate_semantic_hash(self, text: str) -> str:
        """Generate a semantic hash for the text using embeddings"""
        try:
            # Get embedding for the text
            embedding = await self.embedding_service.get_embedding(text)
            if not embedding:
                # Fallback to regular hash if embedding fails
                return hashlib.md5(text.encode()).hexdigest()
            
            # Create a simplified representation of the embedding
            # This creates a more stable hash that can match semantically similar questions
            simplified = []
            for i, val in enumerate(embedding):
                if i % 8 == 0:  # Take every 8th value for simplicity
                    # Round to 2 decimal places and convert to string
                    simplified.append(str(round(val, 2)))
            
            # Join and hash the simplified representation
            return hashlib.md5("_".join(simplified).encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to generate semantic hash: {e}")
            # Fallback to regular hash
            return hashlib.md5(text.encode()).hexdigest()
    
    async def get_cached_answer(
        self, 
        question: str, 
        group_id: str,
        context_type: str = "full"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached answer for a question using semantic matching
        
        Args:
            question: The question to find in cache
            group_id: Group ID for context
            context_type: Type of context used (full, summary, etc.)
            
        Returns:
            Optional[Dict]: Cached answer or None if not found
        """
        try:
            # Normalize question
            normalized_question = question.lower().strip()
            
            # Generate semantic hash
            semantic_hash = await self._generate_semantic_hash(normalized_question)
            
            # Try exact cache match first
            cache_key = self.ai_cache.generate_qa_cache_key(group_id, normalized_question, context_type)
            cached_data = await self.cache_service.get_cache(self.redis, cache_key)
            
            if cached_data:
                self.cache_hits += 1
                logger.info(f"Exact cache hit for question: {normalized_question[:30]}...")
                return cached_data
            
            # Try semantic cache match
            semantic_cache_key = f"semantic:{group_id}:{semantic_hash}:{context_type}"
            semantic_cached_data = await self.cache_service.get_cache(self.redis, semantic_cache_key)
            
            if semantic_cached_data:
                # Verify semantic similarity with original question
                original_question = semantic_cached_data.get("original_question", "")
                if original_question:
                    similarity = await self._check_semantic_similarity(
                        normalized_question, original_question
                    )
                    
                    if similarity >= self.semantic_threshold:
                        self.cache_hits += 1
                        logger.info(f"Semantic cache hit for question: {normalized_question[:30]}... (similarity: {similarity:.2f})")
                        return semantic_cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached answer: {e}")
            return None
    
    async def _check_semantic_similarity(self, text1: str, text2: str) -> float:
        """Check semantic similarity between two texts"""
        try:
            # Get embeddings
            embedding1 = await self.embedding_service.get_embedding(text1)
            embedding2 = await self.embedding_service.get_embedding(text2)
            
            if not embedding1 or not embedding2:
                return 0.0
            
            # Calculate cosine similarity
            similarity = await self.embedding_service.calculate_similarity(embedding1, embedding2)
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to check semantic similarity: {e}")
            return 0.0
    
    async def cache_answer(
        self, 
        question: str, 
        answer: Dict[str, Any], 
        group_id: str,
        context_type: str = "full", 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache answer for a question with semantic indexing
        
        Args:
            question: The question being answered
            answer: The answer data to cache
            group_id: Group ID for context
            context_type: Type of context used
            ttl: Optional custom TTL in seconds
            
        Returns:
            bool: True if caching was successful
        """
        try:
            # Normalize question
            normalized_question = question.lower().strip()
            
            # Add original question to the cached data
            answer["original_question"] = normalized_question
            
            # Generate semantic hash
            semantic_hash = await self._generate_semantic_hash(normalized_question)
            
            # Set cache TTL
            cache_ttl = ttl or self.cache_ttl
            
            # Cache with exact key
            cache_key = self.ai_cache.generate_qa_cache_key(group_id, normalized_question, context_type)
            await self.cache_service.set_cache(self.redis, cache_key, answer, cache_ttl)
            
            # Cache with semantic key
            semantic_cache_key = f"semantic:{group_id}:{semantic_hash}:{context_type}"
            await self.cache_service.set_cache(self.redis, semantic_cache_key, answer, cache_ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache answer: {e}")
            return False
    
    async def search_relevant_content(
        self, 
        question: str, 
        group_id: str,
        community_id: Optional[str] = None,
        is_premium: bool = False,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant content using semantic search with optimized performance
        
        Args:
            question: The question to search for
            group_id: Group ID to search within
            community_id: Optional community ID
            is_premium: Whether the user has premium access
            top_k: Number of results to return
            
        Returns:
            List[Dict]: Relevant content items
        """
        try:
            # Check cache first
            cache_key = f"search_results:{group_id}:{hashlib.md5(question.encode()).hexdigest()}:{top_k}"
            cached_results = await self.cache_service.get_cache(self.redis, cache_key)
            
            if cached_results:
                logger.info(f"Cache hit for search: {question[:30]}...")
                return cached_results
            
            # Get embedding for the question
            question_embedding = await self.embedding_service.get_embedding(question)
            
            # Perform parallel searches for better performance
            search_tasks = []
            
            # Search posts
            search_tasks.append(
                self.embedding_service.search_posts(
                    question_embedding, 
                    question,
                    group_id, 
                    is_premium,
                    top_k
                )
            )
            
            # Search comments
            search_tasks.append(
                self.embedding_service.search_comments(
                    question_embedding,
                    question,
                    group_id,
                    is_premium,
                    top_k
                )
            )
            
            # If premium user, also search external content
            if is_premium:
                search_tasks.append(
                    self.embedding_service.search_external_content(
                        question_embedding,
                        question,
                        top_k
                    )
                )
            
            # Execute all searches in parallel
            results = await asyncio.gather(*search_tasks)
            
            # Combine and process results
            all_results = []
            for result_set in results:
                if result_set:
                    all_results.extend(result_set)
            
            # Sort by relevance
            all_results.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)
            
            # Take top results
            top_results = all_results[:top_k]
            
            # Cache results
            await self.cache_service.set_cache(
                self.redis, 
                cache_key, 
                top_results, 
                self.cache_ttl_short
            )
            
            return top_results
            
        except Exception as e:
            logger.error(f"Failed to search relevant content: {e}")
            return []
    
    async def generate_optimized_context(
        self, 
        question: str,
        relevant_content: List[Dict[str, Any]],
        max_tokens: int = 3000
    ) -> str:
        """
        Generate optimized context for AI model from relevant content
        
        Args:
            question: The question being asked
            relevant_content: List of relevant content items
            max_tokens: Maximum tokens for context
            
        Returns:
            str: Optimized context for the AI model
        """
        try:
            if not relevant_content:
                return f"Question: {question}\n\nNo relevant context found."
            
            # Estimate token count (rough approximation)
            def estimate_tokens(text: str) -> int:
                return len(text.split())
            
            context_parts = []
            current_tokens = 0
            
            # Add question as context
            context_parts.append(f"Question: {question}")
            current_tokens += estimate_tokens(question)
            
            # Sort content by relevance and recency
            sorted_content = sorted(
                relevant_content, 
                key=lambda x: (x.get('similarity', 0.0), x.get('created_at', '')), 
                reverse=True
            )
            
            # Process each content item
            for item in sorted_content:
                if current_tokens >= max_tokens:
                    break
                
                content_type = item.get('type', 'unknown')
                content_text = item.get('content', '')
                title = item.get('title', '')
                similarity = item.get('similarity', 0.0)
                
                # Skip low-relevance content
                if similarity < 0.5:
                    continue
                
                # Format based on content type
                if content_type == 'post':
                    if title:
                        formatted_text = f"Post: {title}\n{content_text[:800]}"
                    else:
                        formatted_text = f"Post: {content_text[:800]}"
                elif content_type == 'comment':
                    formatted_text = f"Comment: {content_text[:500]}"
                elif content_type == 'external':
                    formatted_text = f"External Content: {content_text[:800]}"
                else:
                    formatted_text = f"{content_type.capitalize()}: {content_text[:500]}"
                
                # Add source information
                if 'id' in item:
                    formatted_text += f"\nSource ID: {item['id']}"
                
                # Add to context if it fits
                tokens = estimate_tokens(formatted_text)
                if current_tokens + tokens <= max_tokens:
                    context_parts.append(formatted_text)
                    current_tokens += tokens
                else:
                    # If it doesn't fit entirely, truncate
                    available_tokens = max_tokens - current_tokens
                    words = formatted_text.split()
                    truncated_text = " ".join(words[:available_tokens])
                    context_parts.append(truncated_text)
                    current_tokens += available_tokens
                    break
            
            # Join all parts with clear separation
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate context: {e}")
            return f"Question: {question}\n\nError generating context."
    
    async def call_groq_api(
        self, 
        prompt: str,
        model: str = "llama-3.1-70b-versatile",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Call Groq API with optimized settings and metrics tracking
        
        Args:
            prompt: The prompt to send to the model
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stream: Whether to stream the response
            
        Returns:
            Tuple[Optional[str], Dict[str, Any]]: (Response text, Metrics)
        """
        try:
            import httpx
            
            start_time = time.time()
            self.llm_calls += 1
            
            if not settings.groq_api_key:
                logger.error("Groq API key not configured")
                return None, {"error": "API key not configured", "latency": 0}
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }
            
            # Make the API call with timeout
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.groq_api_url,
                    headers=headers,
                    json=payload
                )
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Update average response time
                self.avg_response_time = (
                    (self.avg_response_time * (self.llm_calls - 1) + latency) / self.llm_calls
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract metrics
                    metrics = {
                        "latency": latency,
                        "model": model,
                        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                        "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                    }
                    
                    # Log performance metrics
                    logger.info(
                        f"Groq API call: latency={latency:.2f}s, "
                        f"tokens={metrics['total_tokens']}, "
                        f"model={model}"
                    )
                    
                    return data["choices"][0]["message"]["content"].strip(), metrics
                else:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return None, {
                        "error": f"API error: {response.status_code}",
                        "latency": latency
                    }
                    
        except httpx.TimeoutException:
            end_time = time.time()
            logger.error("Groq API timeout")
            return None, {"error": "API timeout", "latency": end_time - start_time}
        except Exception as e:
            end_time = time.time()
            logger.error(f"Groq API error: {e}")
            return None, {"error": str(e), "latency": end_time - start_time}
    
    async def answer_question(
        self, 
        question: str,
        group_id: str,
        user_id: str,
        is_premium: bool = False,
        use_cache: bool = True,
        context_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG approach with optimized performance
        
        Args:
            question: The question to answer
            group_id: Group ID for context
            user_id: User ID asking the question
            is_premium: Whether the user has premium access
            use_cache: Whether to use cache
            context_type: Type of context to use
            
        Returns:
            Dict[str, Any]: Answer data with metrics
        """
        try:
            start_time = time.time()
            self.total_requests += 1
            
            # Check cache first if enabled
            if use_cache:
                cached_answer = await self.get_cached_answer(question, group_id, context_type)
                if cached_answer:
                    # Add cache metrics
                    cached_answer["metrics"] = {
                        "source": "cache",
                        "latency": time.time() - start_time,
                        "cache_hit": True
                    }
                    return cached_answer
            
            # Search for relevant content
            relevant_content = await self.search_relevant_content(
                question, group_id, None, is_premium, top_k=10
            )
            
            if not relevant_content:
                no_context_response = {
                    "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing or ask a more specific question.",
                    "source": "no_context",
                    "sources": [],
                    "metrics": {
                        "latency": time.time() - start_time,
                        "cache_hit": False,
                        "content_found": False
                    }
                }
                return no_context_response
            
            # Generate optimized context
            context = await self.generate_optimized_context(question, relevant_content, max_tokens=3000)
            
            # Create prompt for AI model
            prompt = f"""You are an expert visa and immigration assistant. Answer the following question based on the provided context.
            If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.
            Always provide accurate information and cite your sources when possible.

            {context}

            Answer:"""
            
            # Call AI model
            answer_text, metrics = await self.call_groq_api(
                prompt, 
                model="llama-3.1-70b-versatile",  # Using Llama 3.1 70B for best quality
                max_tokens=1000, 
                temperature=0.7
            )
            
            if not answer_text:
                error_response = {
                    "answer": "I'm sorry, but I couldn't generate an answer at this time. Please try again later.",
                    "source": "error",
                    "sources": [],
                    "metrics": {
                        "latency": time.time() - start_time,
                        "cache_hit": False,
                        "error": metrics.get("error", "Unknown error")
                    }
                }
                return error_response
            
            # Prepare response
            response = {
                "answer": answer_text.strip(),
                "source": "ai_model",
                "timestamp": datetime.now().isoformat(),
                "sources": [
                    {
                        "type": item.get("type", "unknown"),
                        "id": item.get("id", ""),
                        "content": item.get("content", "")[:200] + "..." if len(item.get("content", "")) > 200 else item.get("content", ""),
                        "created_at": item.get("created_at", ""),
                        "similarity": item.get("similarity", 0.0)
                    }
                    for item in relevant_content[:5]  # Limit to top 5 sources
                ],
                "metrics": {
                    "latency": time.time() - start_time,
                    "model": "llama-3.1-70b-versatile",
                    "prompt_tokens": metrics.get("prompt_tokens", 0),
                    "completion_tokens": metrics.get("completion_tokens", 0),
                    "total_tokens": metrics.get("total_tokens", 0),
                    "cache_hit": False
                }
            }
            
            # Cache the answer
            await self.cache_answer(question, response, group_id, context_type)
            
            # Log performance
            logger.info(
                f"Question answered: latency={time.time() - start_time:.2f}s, "
                f"tokens={metrics.get('total_tokens', 0)}, "
                f"cache_hit=False"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            end_time = time.time()
            return {
                "answer": "I'm sorry, but I encountered an error while processing your question. Please try again later.",
                "source": "error",
                "sources": [],
                "metrics": {
                    "latency": end_time - start_time,
                    "cache_hit": False,
                    "error": str(e)
                }
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the AI service"""
        try:
            cache_hit_rate = (self.cache_hits / self.total_requests) * 100 if self.total_requests > 0 else 0
            
            return {
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": f"{cache_hit_rate:.2f}%",
                "llm_calls": self.llm_calls,
                "avg_response_time": f"{self.avg_response_time:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }