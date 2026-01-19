from typing import List, Dict, Any, Optional
import logging
import json
import hashlib
from datetime import datetime, timedelta
from redis.asyncio import Redis
from ..core.config import settings
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered Q&A and content generation"""
    
    def __init__(self, redis_client: Redis, embedding_service: EmbeddingService):
        self.redis = redis_client
        self.embedding_service = embedding_service
        self.cache_ttl = 3600  # 1 hour default TTL
    
    def _generate_cache_key(self, group_id: int, question: str, context_type: str = "full") -> str:
        """Generate cache key for question-answer pairs"""
        normalized_question = question.lower().strip()
        cache_input = f"{group_id}:{normalized_question}:{context_type}"
        return f"qa:{hashlib.md5(cache_input.encode()).hexdigest()}"
    
    async def get_cached_answer(self, group_id: int, question: str, context_type: str = "full") -> Optional[Dict[str, Any]]:
        """Get cached answer for a question"""
        try:
            cache_key = self._generate_cache_key(group_id, question, context_type)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached answer: {e}")
            return None
    
    async def cache_answer(self, group_id: int, question: str, answer: Dict[str, Any], context_type: str = "full", ttl: Optional[int] = None) -> bool:
        """Cache answer for a question"""
        try:
            cache_key = self._generate_cache_key(group_id, question, context_type)
            cache_ttl = ttl or self.cache_ttl
            
            await self.redis.setex(
                cache_key, 
                cache_ttl, 
                json.dumps(answer, default=str)
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache answer: {e}")
            return False
    
    async def search_relevant_content(
        self, 
        question: str, 
        group_id: int,
        community_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant content using semantic search"""
        try:
            # Perform semantic search across posts, comments, and messages
            posts = await self.embedding_service.semantic_search_posts(
                question, community_id, top_k
            )
            
            comments = await self.embedding_service.semantic_search_comments(
                question, community_id, top_k
            )
            
            messages = await self.embedding_service.semantic_search_messages(
                question, group_id, top_k
            )
            
            # Combine and rank results
            all_results = []
            all_results.extend([{'type': 'post', **post} for post in posts])
            all_results.extend([{'type': 'comment', **comment} for comment in comments])
            all_results.extend([{'type': 'message', **message} for message in messages])
            
            # Sort by relevance (assuming distance is in the results)
            all_results.sort(key=lambda x: x.get('distance', 1.0))
            
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search relevant content: {e}")
            return []
    
    async def generate_context(
        self, 
        question: str,
        relevant_content: List[Dict[str, Any]],
        max_tokens: int = 2000
    ) -> str:
        """Generate context for AI model from relevant content"""
        try:
            context_parts = []
            current_tokens = 0
            
            # Add question as context
            context_parts.append(f"Question: {question}")
            current_tokens += len(question.split())
            
            # Add relevant content, prioritizing by type and recency
            for item in relevant_content:
                if current_tokens >= max_tokens:
                    break
                
                content_text = ""
                if item['type'] == 'post':
                    content_text = f"Post: {item.get('title', '')} - {item.get('content', '')[:500]}"
                elif item['type'] == 'comment':
                    content_text = f"Comment: {item.get('content', '')[:500]}"
                elif item['type'] == 'message':
                    content_text = f"Message: {item.get('content', '')[:500]}"
                
                content_tokens = len(content_text.split())
                if current_tokens + content_tokens <= max_tokens:
                    context_parts.append(content_text)
                    current_tokens += content_tokens
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate context: {e}")
            return question
    
    async def call_ai_model(
        self, 
        prompt: str,
        model: str = "llama3-8b-8192",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Call AI model for text generation"""
        try:
            # Integrate with AI providers: Groq or OpenRouter
            
            if settings.AI_PROVIDER == "groq":
                return await self._call_groq_api(prompt, model, max_tokens, temperature)
            elif settings.AI_PROVIDER == "openrouter":
                return await self._call_openrouter_api(prompt, model, max_tokens, temperature)
            else:
                logger.error(f"Unsupported AI provider: {settings.AI_PROVIDER}")
                return None
                
                
        except Exception as e:
            logger.error(f"Failed to call AI model: {e}")
            return None
    
    async def _call_groq_api(
        self, 
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call Groq API for text generation"""
        try:
            import httpx
            
            if not settings.GROQ_API_KEY:
                logger.error("Groq API key not configured")
                return None
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
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
                "stream": False
            }
            
            # Make the API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Groq API timeout")
            return None
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    async def _call_openrouter_api(
        self, 
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call OpenRouter API for text generation"""
        try:
            import httpx
            
            if not settings.OPENROUTER_API_KEY:
                logger.error("OpenRouter API key not configured")
                return None
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://visa-platform.com",
                "X-Title": "Visa Platform AI"
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
                "stream": False
            }
            
            # Make the API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            return None
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None
    
    
    async def answer_question(
        self, 
        question: str,
        group_id: int,
        community_id: Optional[int] = None,
        use_cache: bool = True,
        context_type: str = "full"
    ) -> Dict[str, Any]:
        """Answer a question using RAG approach"""
        try:
            # Check cache first
            if use_cache:
                cached_answer = await self.get_cached_answer(group_id, question, context_type)
                if cached_answer:
                    return {
                        "answer": cached_answer["answer"],
                        "source": "cache",
                        "cached_at": cached_answer.get("timestamp"),
                        "sources": cached_answer.get("sources", [])
                    }
            
            # Search for relevant content
            relevant_content = await self.search_relevant_content(
                question, group_id, community_id, top_k=10
            )
            
            if not relevant_content:
                return {
                    "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing or ask a more specific question.",
                    "source": "no_context",
                    "sources": []
                }
            
            # Generate context
            context = await self.generate_context(question, relevant_content, max_tokens=2000)
            
            # Create prompt for AI model
            prompt = f"""Answer the following question based on the provided context. 
            If the context doesn't contain enough information to answer the question, 
            please say so and suggest what additional information might be helpful.

            Context:
            {context}

            Question: {question}

            Answer:"""
            
            # Call AI model
            answer = await self.call_ai_model(prompt, max_tokens=1000, temperature=0.7)
            
            if not answer:
                return {
                    "answer": "I'm sorry, but I couldn't generate an answer at this time. Please try again later.",
                    "source": "error",
                    "sources": []
                }
            
            # Prepare response
            response = {
                "answer": answer.strip(),
                "source": "ai_model",
                "timestamp": datetime.now().isoformat(),
                "sources": [
                    {
                        "type": item["type"],
                        "id": item["id"],
                        "content": item.get("content", "")[:200] + "..." if len(item.get("content", "")) > 200 else item.get("content", ""),
                        "created_at": item.get("created_at")
                    }
                    for item in relevant_content[:5]  # Limit to top 5 sources
                ]
            }
            
            # Cache the answer
            await self.cache_answer(group_id, question, response, context_type)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "answer": "I'm sorry, but I encountered an error while processing your question. Please try again later.",
                "source": "error",
                "sources": []
            }
    
    async def summarize_thread(
        self, 
        group_id: int,
        thread_content: List[Dict[str, Any]],
        summary_type: str = "concise"
    ) -> Optional[str]:
        """Summarize a thread of messages"""
        try:
            if not thread_content:
                return None
            
            # Prepare thread content for summarization
            thread_text = "\n\n".join([
                f"{item.get('type', 'message')}: {item.get('content', '')}"
                for item in thread_content
            ])
            
            # Create summarization prompt
            if summary_type == "concise":
                prompt = f"""Please provide a concise summary (2-3 sentences) of the following conversation thread:

                {thread_text}

                Summary:"""
            else:
                prompt = f"""Please provide a detailed summary of the following conversation thread, 
                highlighting key points, decisions, and any important information:

                {thread_text}

                Summary:"""
            
            # Call AI model for summarization
            summary = await self.call_ai_model(prompt, max_tokens=500, temperature=0.5)
            
            return summary.strip() if summary else None
            
        except Exception as e:
            logger.error(f"Failed to summarize thread: {e}")
            return None
    
    async def get_cost_estimate(self, prompt_tokens: int, response_tokens: int) -> float:
        """Estimate cost for AI model usage"""
        try:
            # Cost rates for different providers (per 1000 tokens)
            cost_rates = {
                "groq": {"prompt": 0.0005, "response": 0.0005},  # Example rates
                "openrouter": {"prompt": 0.001, "response": 0.001},
            }
            
            provider = settings.AI_PROVIDER
            rates = cost_rates.get(provider, {"prompt": 0.0, "response": 0.0})
            
            prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
            response_cost = (response_tokens / 1000) * rates["response"]
            
            return prompt_cost + response_cost
            
        except Exception as e:
            logger.error(f"Failed to estimate cost: {e}")
            return 0.0