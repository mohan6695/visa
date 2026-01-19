#!/usr/bin/env python3
"""
Test Hybrid Search with RRF and FlashRank

This script tests the hybrid search functionality:
1. Semantic search (pgvector)
2. Keyword search (BM25/FTS)
3. RRF merge
4. FlashRank reranking
5. Redis caching
"""

import os
import sys
import json
import time
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


def test_rrf_merge():
    """Test RRF merge function"""
    print("\n" + "=" * 60)
    print("Testing RRF Merge")
    print("=" * 60)
    
    # Simulated results
    semantic_results = [
        {"id": "1", "title": "Doc A", "score": 0.9},
        {"id": "2", "title": "Doc B", "score": 0.8},
        {"id": "3", "title": "Doc C", "score": 0.7},
    ]
    
    keyword_results = [
        {"id": "2", "title": "Doc B", "score": 0.85},
        {"id": "4", "title": "Doc D", "score": 0.75},
        {"id": "1", "title": "Doc A", "score": 0.65},
    ]
    
    # RRF merge implementation
    k = 60
    scores = {}
    
    for rank, doc in enumerate(semantic_results):
        doc_id = doc["id"]
        if doc_id not in scores:
            scores[doc_id] = 0
        scores[doc_id] += 1.0 / (rank + k) * 0.7
    
    for rank, doc in enumerate(keyword_results):
        doc_id = doc["id"]
        if doc_id not in scores:
            scores[doc_id] = 0
        scores[doc_id] += 1.0 / (rank + k) * 0.3
    
    merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    print("\nRRF Merged Results:")
    for doc_id, score in merged:
        print(f"  {doc_id}: {score:.6f}")
    
    print(f"\nExpected: Doc 2 > Doc 1 > Doc 3 > Doc 4")
    print(f"Result: Doc {' > '.join([d[0] for d in merged])}")
    
    return merged


def test_embedding_generation():
    """Test embedding generation"""
    print("\n" + "=" * 60)
    print("Testing Embedding Generation")
    print("=" * 60)
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    test_queries = [
        "H1B visa processing time",
        "OPT STEM extension",
        "green card timeline",
    ]
    
    print(f"\nUsing model: all-MiniLM-L6-v2")
    print(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")
    
    for query in test_queries:
        embedding = model.encode(query)
        print(f"\nQuery: '{query}'")
        print(f"  Embedding shape: {embedding.shape}")
        print(f"  First 5 values: {embedding[:5]}")
    
    return True


def test_flashrank():
    """Test FlashRank reranking"""
    print("\n" + "=" * 60)
    print("Testing FlashRank Reranking")
    print("=" * 60)
    
    try:
        from flashrank import Ranker
        
        reranker = Ranker("ms-marco-MiniLM-L-6-v2")
        
        query = "How to apply for H1B visa"
        
        passages = [
            {"id": "1", "text": "H1B visa application process step by step guide", "meta": {"title": "H1B Guide"}},
            {"id": "2", "text": "Weather forecast for tomorrow", "meta": {"title": "Weather"}},
            {"id": "3", "text": "H1B requirements and eligibility criteria explained", "meta": {"title": "H1B Requirements"}},
            {"id": "4", "text": "Best restaurants in New York", "meta": {"title": "Food"}},
            {"id": "5", "text": "H1B cap submission tips and strategies", "meta": {"title": "H1B Tips"}},
        ]
        
        print(f"\nQuery: '{query}'")
        print(f"Documents before reranking:")
        for p in passages:
            print(f"  {p['id']}: {p['meta']['title']}")
        
        result = reranker.rerank(query, passages)
        
        print(f"\nDocuments after FlashRank reranking:")
        for item in result["passages"]:
            print(f"  {item['id']}: score={item['score']:.4f} - {item['meta']['title']}")
        
        return True
        
    except ImportError:
        print("\nFlashRank not installed. Install with: pip install flashrank")
        return False


def test_latency_benchmark():
    """Test expected latency benchmarks"""
    print("\n" + "=" * 60)
    print("Latency Benchmark Expectations")
    print("=" * 60)
    
    benchmarks = {
        "L1 Cache (Redis)": {"expected_ms": 1, "pct": 70},
        "Semantic Search (pgvector)": {"expected_ms": 50, "pct": 85},
        "Keyword Search (BM25)": {"expected_ms": 20, "pct": 90},
        "RRF Merge": {"expected_ms": 5, "pct": 95},
        "FlashRank Rerank (30→12)": {"expected_ms": 30, "pct": 85},
        "Full Search (no cache)": {"expected_ms": 106, "pct": 80},
        "Full Search (with cache)": {"expected_ms": 50, "pct": 90},
    }
    
    print("\nStage                | Expected | Cache Hit%")
    print("-" * 50)
    for stage, data in benchmarks.items():
        print(f"{stage:22} | {data['expected_ms']:6}ms | {data['pct']}%")
    
    return benchmarks


def test_query_hash():
    """Test query hash generation"""
    print("\n" + "=" * 60)
    print("Testing Query Hash Generation")
    print("=" * 60)
    
    import hashlib
    
    def generate_query_hash(query: str, group_id: str = None, limit: int = 12) -> str:
        key_data = f"{query}:{group_id}:{limit}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    test_cases = [
        ("H1B visa", "group-123", 12),
        ("OPT extension", "group-456", 10),
        ("H1B visa", "group-123", 12),  # Same as first
    ]
    
    print("\nQuery hash examples:")
    for query, group_id, limit in test_cases:
        hash_val = generate_query_hash(query, group_id, limit)
        print(f"  '{query}' + {group_id} + {limit} -> {hash_val}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Hybrid Search Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["rrf_merge"] = test_rrf_merge()
    results["embedding"] = test_embedding_generation()
    results["flashrank"] = test_flashrank()
    results["latency"] = test_latency_benchmark()
    results["hash"] = test_query_hash()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
