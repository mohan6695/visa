#!/usr/bin/env python3
"""
Background Worker for Processing Embedding Jobs

This script follows the Supabase "Automatic Embeddings" pattern:
1. Fetches unprocessed jobs from embedding_jobs table
2. Joins with posts to get title + short_excerpt
3. Generates embeddings using Ollama
4. Updates posts.embedding column
5. Marks jobs as processed

Usage:
    python -m backend.scripts.embedding_worker [--batch-size 100] [--interval 5]
"""

import asyncio
import sys
import os
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('embedding_worker')


class EmbeddingWorker:
    """Background worker for processing embedding jobs"""
    
    def __init__(
        self,
        batch_size: int = 100,
        max_retries: int = 3,
        ollama_base_url: str = None,
        embedding_model: str = None
    ):
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        # Ollama settings
        self.ollama_base_url = ollama_base_url or getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.embedding_model = embedding_model or getattr(settings, 'OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
        
        # Database setup
        database_url = getattr(settings, 'SUPABASE_DATABASE_URL', None) or \
                       getattr(settings, 'DATABASE_URL', 'postgresql://localhost/visa')
        
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # HTTP session for Ollama
        self._http_session = None
        
    def _get_http_session(self):
        """Get or create HTTP session for Ollama requests"""
        if self._http_session is None:
            import requests
            self._http_session = requests.Session()
        return self._http_session
    
    def test_ollama_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            session = self._get_http_session()
            response = session.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"Ollama connected. Available models: {[m.get('name') for m in models]}")
                return True
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text content using Ollama"""
        try:
            import requests
            
            # Clean text - limit to reasonable length
            cleaned_text = ' '.join(str(text).split()[:500])
            
            session = self._get_http_session()
            response = session.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": cleaned_text
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding')
                if embedding:
                    return embedding
                else:
                    logger.error(f"Unexpected Ollama response: {result}")
                    return None
            else:
                logger.error(f"Ollama embedding failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def fetch_pending_jobs(self, session, limit: int = 100) -> List[Dict]:
        """Fetch pending embedding jobs from the database"""
        try:
            query = text("""
                SELECT ej.id as job_id, ej.post_id, p.title, p.short_excerpt
                FROM embedding_jobs ej
                JOIN posts p ON ej.post_id = p.id
                WHERE ej.processed = false
                AND ej.retry_count < :max_retries
                AND (ej.error IS NULL OR ej.retry_count < 2)
                ORDER BY ej.created_at ASC
                LIMIT :limit
            """)
            
            result = session.execute(query, {'max_retries': self.max_retries, 'limit': limit})
            rows = result.fetchall()
            
            return [
                {
                    'job_id': row.job_id,
                    'post_id': row.post_id,
                    'title': row.title,
                    'short_excerpt': row.short_excerpt
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to fetch pending jobs: {e}")
            return []
    
    def process_jobs(self, jobs: List[Dict]) -> tuple:
        """Process a batch of embedding jobs"""
        processed_count = 0
        failed_count = 0
        
        for job in jobs:
            try:
                # Combine title and short_excerpt for embedding
                combined_text = f"{job['title'] or ''}\n\n{job['short_excerpt'] or ''}"
                combined_text = combined_text.strip()
                
                if not combined_text:
                    logger.warning(f"Job {job['job_id']}: No text to embed, skipping")
                    continue
                
                # Generate embedding
                embedding = self.generate_embedding(combined_text)
                
                if embedding:
                    # Update post embedding
                    update_query = text("""
                        UPDATE posts 
                        SET embedding = :embedding::vector, updated_at = now()
                        WHERE id = :post_id
                    """)
                    
                    self.engine.execute(update_query, {
                        'embedding': str(embedding),
                        'post_id': job['post_id']
                    })
                    
                    # Mark job as processed
                    mark_processed_query = text("""
                        UPDATE embedding_jobs 
                        SET processed = true, processed_at = now()
                        WHERE id = :job_id
                    """)
                    
                    self.engine.execute(mark_processed_query, {'job_id': job['job_id']})
                    
                    processed_count += 1
                    logger.info(f"Processed job {job['job_id']} for post {job['post_id']}")
                else:
                    # Mark as failed with error
                    self._mark_job_failed(session=None, job_id=job['job_id'], error="Embedding generation failed")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process job {job['job_id']}: {e}")
                self._mark_job_failed(session=None, job_id=job['job_id'], error=str(e))
                failed_count += 1
        
        return processed_count, failed_count
    
    def _mark_job_failed(self, session, job_id: int, error: str):
        """Mark a job as failed and increment retry count"""
        try:
            query = text("""
                UPDATE embedding_jobs 
                SET error = :error, retry_count = retry_count + 1
                WHERE id = :job_id
            """)
            self.engine.execute(query, {'error': error[:500], 'job_id': job_id})
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
    
    def run_batch(self) -> Dict[str, int]:
        """Run one batch of embedding job processing"""
        session = self.SessionLocal()
        try:
            # Fetch pending jobs
            jobs = self.fetch_pending_jobs(session, self.batch_size)
            
            if not jobs:
                logger.debug("No pending embedding jobs found")
                return {'processed': 0, 'failed': 0, 'total': 0}
            
            logger.info(f"Found {len(jobs)} pending embedding jobs")
            
            # Process jobs
            processed_count, failed_count = self.process_jobs(jobs)
            
            # Commit all changes
            session.commit()
            
            return {
                'processed': processed_count,
                'failed': failed_count,
                'total': len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error in run_batch: {e}")
            session.rollback()
            return {'processed': 0, 'failed': 0, 'total': 0, 'error': str(e)}
        finally:
            session.close()
    
    def run_continuously(self, interval: int = 5):
        """Run the worker continuously with the specified interval"""
        logger.info(f"Starting embedding worker with batch_size={self.batch_size}, interval={interval}s")
        
        # Test Ollama connection first
        if not self.test_ollama_connection():
            logger.warning("Ollama not available, worker will retry on each batch")
        
        while True:
            try:
                result = self.run_batch()
                if result['total'] > 0:
                    logger.info(f"Batch complete: {result['processed']} processed, {result['failed']} failed")
            except KeyboardInterrupt:
                logger.info("Embedding worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
            
            # Wait before next iteration
            time.sleep(interval)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Embedding Job Worker')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of jobs to process per batch')
    parser.add_argument('--interval', type=int, default=5, help='Seconds between batches')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts per job')
    parser.add_argument('--once', action='store_true', help='Run only one batch and exit')
    parser.add_argument('--ollama-url', type=str, default=None, help='Ollama base URL')
    parser.add_argument('--model', type=str, default=None, help='Embedding model name')
    
    args = parser.parse_args()
    
    worker = EmbeddingWorker(
        batch_size=args.batch_size,
        max_retries=args.max_retries,
        ollama_base_url=args.ollama_url,
        embedding_model=args.model
    )
    
    if args.once:
        result = worker.run_batch()
        print(f"Batch result: {result}")
    else:
        worker.run_continuously(interval=args.interval)


if __name__ == '__main__':
    main()
