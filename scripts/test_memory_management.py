#!/usr/bin/env python3
"""
Memory Management Test Suite
Tests tagging, categorization, pruning, and deduplication processes.
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_management_test")

def get_api_token() -> str:
    """Get API token for testing."""
    try:
        with open("/app/.apitoken", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error("No API token found")
        sys.exit(1)

def test_tagging_and_categorization(api_token: str) -> Dict[str, Any]:
    """Test that worker commit stories are properly tagged and categorized."""
    logger.info("🧪 Testing tagging and categorization...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Get all worker commit stories
        response = requests.get("http://api:8000/memory/nodes", headers=headers)
        response.raise_for_status()
        
        nodes = response.json()
        worker_nodes = [node for node in nodes if node.get("namespace") == "worker_commits"]
        
        logger.info(f"Found {len(worker_nodes)} worker commit stories")
        
        results = {
            "total_worker_stories": len(worker_nodes),
            "tagging_tests": [],
            "categorization_tests": [],
            "issues": []
        }
        
        # Test each worker story
        for node in worker_nodes:
            node_id = node["id"]
            meta = json.loads(node["meta"])
            
            logger.info(f"Testing node {node_id}: {meta.get('commit_hash', 'unknown')}")
            
            # Test tagging
            tags = node.get("tags", [])
            expected_tags = [
                "worker-commit", "detailed-story", "git-history", 
                "worker-system", "memory-workers"
            ]
            
            missing_tags = [tag for tag in expected_tags if tag not in tags]
            if missing_tags:
                results["issues"].append(f"Node {node_id} missing tags: {missing_tags}")
            
            results["tagging_tests"].append({
                "node_id": node_id,
                "commit_hash": meta.get("commit_hash"),
                "tags": tags,
                "missing_tags": missing_tags,
                "tag_count": len(tags)
            })
            
            # Test categorization
            categories = meta.get("categories", [])
            expected_categories = ["memory-system", "worker-system"]
            
            missing_categories = [cat for cat in expected_categories if cat not in categories]
            if missing_categories:
                results["issues"].append(f"Node {node_id} missing categories: {missing_categories}")
            
            results["categorization_tests"].append({
                "node_id": node_id,
                "commit_hash": meta.get("commit_hash"),
                "categories": categories,
                "missing_categories": missing_categories,
                "category_count": len(categories)
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing tagging and categorization: {e}")
        return {"error": str(e)}

def test_search_functionality(api_token: str) -> Dict[str, Any]:
    """Test search functionality with different queries."""
    logger.info("🔍 Testing search functionality...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        test_queries = [
            "worker",
            "memory",
            "docker",
            "similarity pruning",
            "migrations",
            "makefile"
        ]
        
        results = {
            "queries": [],
            "total_results": 0
        }
        
        for query in test_queries:
            logger.info(f"Testing search query: '{query}'")
            
            # Test RAG search
            rag_payload = {
                "question": query,
                "namespace": "worker_commits",
                "top_k": 5
            }
            
            response = requests.post(
                "http://api:8000/memory/rag_search",
                json=rag_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                rag_results = response.json()
                results["queries"].append({
                    "query": query,
                    "rag_results": len(rag_results.get("results", [])),
                    "success": True
                })
                results["total_results"] += len(rag_results.get("results", []))
            else:
                results["queries"].append({
                    "query": query,
                    "rag_results": 0,
                    "success": False,
                    "error": response.text
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing search functionality: {e}")
        return {"error": str(e)}

def test_deduplication(api_token: str) -> Dict[str, Any]:
    """Test deduplication by creating duplicate content and checking if it's detected."""
    logger.info("🔄 Testing deduplication...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Create a test story that might be similar to existing ones
        test_story = {
            "content": "This is a test worker commit story for deduplication testing.",
            "meta": json.dumps({
                "type": "test_worker_story",
                "commit_hash": "test123",
                "author": "Test Author",
                "date": "2025-06-19",
                "message": "test deduplication",
                "file_count": 1,
                "categories": ["test"],
                "tags": ["test", "deduplication"],
                "story_length": 100,
                "generated_at": datetime.now().isoformat()
            }),
            "namespace": "test_worker_commits",
            "tags": ["test", "deduplication", "worker-commit"]
        }
        
        # Create the test story
        response = requests.post(
            "http://api:8000/memory/nodes",
            json=test_story,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            created_node = response.json()
            node_id = created_node.get("id")
            
            logger.info(f"Created test node: {node_id}")
            
            # Now try to create a similar story
            similar_story = {
                "content": "This is a test worker commit story for deduplication testing.",  # Same content
                "meta": json.dumps({
                    "type": "test_worker_story",
                    "commit_hash": "test456",  # Different hash
                    "author": "Test Author",
                    "date": "2025-06-19",
                    "message": "test deduplication",
                    "file_count": 1,
                    "categories": ["test"],
                    "tags": ["test", "deduplication"],
                    "story_length": 100,
                    "generated_at": datetime.now().isoformat()
                }),
                "namespace": "test_worker_commits",
                "tags": ["test", "deduplication", "worker-commit"]
            }
            
            # Try to create the similar story
            response2 = requests.post(
                "http://api:8000/memory/nodes",
                json=similar_story,
                headers=headers,
                timeout=30
            )
            
            results = {
                "original_node_id": node_id,
                "duplicate_attempt_status": response2.status_code,
                "duplicate_attempt_response": response2.text if response2.status_code != 200 else "Success",
                "deduplication_working": response2.status_code != 200  # If it fails, deduplication might be working
            }
            
            # Clean up test nodes
            try:
                requests.delete(f"http://api:8000/memory/nodes/{node_id}", headers=headers)
                logger.info(f"Cleaned up test node: {node_id}")
            except:
                pass
            
            return results
        else:
            return {"error": f"Failed to create test node: {response.text}"}
        
    except Exception as e:
        logger.error(f"Error testing deduplication: {e}")
        return {"error": str(e)}

def test_similarity_pruning(api_token: str) -> Dict[str, Any]:
    """Test similarity pruning by checking for similar content."""
    logger.info("✂️ Testing similarity pruning...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Get all worker commit stories
        response = requests.get("http://api:8000/memory/nodes", headers=headers)
        response.raise_for_status()
        
        nodes = response.json()
        worker_nodes = [node for node in nodes if node.get("namespace") == "worker_commits"]
        
        # Check for potential duplicates or very similar content
        similarity_issues = []
        content_lengths = []
        
        for node in worker_nodes:
            content = node.get("content", "")
            content_lengths.append(len(content))
            
            # Check for exact duplicates
            for other_node in worker_nodes:
                if node["id"] != other_node["id"]:
                    other_content = other_node.get("content", "")
                    if content == other_content:
                        similarity_issues.append({
                            "type": "exact_duplicate",
                            "node1": node["id"],
                            "node2": other_node["id"]
                        })
        
        # Check for very similar content lengths (potential duplicates)
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        length_variance = sum((length - avg_length) ** 2 for length in content_lengths) / len(content_lengths) if content_lengths else 0
        
        results = {
            "total_worker_stories": len(worker_nodes),
            "similarity_issues": similarity_issues,
            "content_length_stats": {
                "average_length": avg_length,
                "variance": length_variance,
                "min_length": min(content_lengths) if content_lengths else 0,
                "max_length": max(content_lengths) if content_lengths else 0
            },
            "potential_duplicates": len(similarity_issues)
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing similarity pruning: {e}")
        return {"error": str(e)}

def test_memory_cleanup(api_token: str) -> Dict[str, Any]:
    """Test memory cleanup by checking for orphaned or invalid nodes."""
    logger.info("🧹 Testing memory cleanup...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Get all nodes
        response = requests.get("http://api:8000/memory/nodes", headers=headers)
        response.raise_for_status()
        
        nodes = response.json()
        
        cleanup_issues = []
        
        for node in nodes:
            # Check for nodes with missing required fields
            if not node.get("content"):
                cleanup_issues.append({
                    "type": "missing_content",
                    "node_id": node["id"],
                    "namespace": node.get("namespace")
                })
            
            if not node.get("meta"):
                cleanup_issues.append({
                    "type": "missing_meta",
                    "node_id": node["id"],
                    "namespace": node.get("namespace")
                })
            
            # Check for invalid JSON in meta
            try:
                meta = json.loads(node.get("meta", "{}"))
            except json.JSONDecodeError:
                cleanup_issues.append({
                    "type": "invalid_meta_json",
                    "node_id": node["id"],
                    "namespace": node.get("namespace")
                })
        
        results = {
            "total_nodes": len(nodes),
            "cleanup_issues": cleanup_issues,
            "issues_count": len(cleanup_issues)
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing memory cleanup: {e}")
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Test memory management processes")
    parser.add_argument("--test", choices=["all", "tagging", "search", "dedup", "pruning", "cleanup"], 
                       default="all", help="Which test to run")
    
    args = parser.parse_args()
    
    api_token = get_api_token()
    
    logger.info("🚀 Starting Memory Management Test Suite")
    logger.info("=" * 60)
    
    results = {}
    
    if args.test in ["all", "tagging"]:
        results["tagging"] = test_tagging_and_categorization(api_token)
    
    if args.test in ["all", "search"]:
        results["search"] = test_search_functionality(api_token)
    
    if args.test in ["all", "dedup"]:
        results["deduplication"] = test_deduplication(api_token)
    
    if args.test in ["all", "pruning"]:
        results["similarity_pruning"] = test_similarity_pruning(api_token)
    
    if args.test in ["all", "cleanup"]:
        results["memory_cleanup"] = test_memory_cleanup(api_token)
    
    # Print results
    logger.info("📊 TEST RESULTS")
    logger.info("=" * 60)
    
    for test_name, test_results in results.items():
        logger.info(f"\n🔍 {test_name.upper()} TEST RESULTS:")
        
        if "error" in test_results:
            logger.error(f"❌ {test_name} test failed: {test_results['error']}")
        else:
            logger.info(f"✅ {test_name} test completed successfully")
            
            if test_name == "tagging":
                logger.info(f"   - Total worker stories: {test_results.get('total_worker_stories', 0)}")
                logger.info(f"   - Issues found: {len(test_results.get('issues', []))}")
                
                if test_results.get('issues'):
                    for issue in test_results['issues']:
                        logger.warning(f"   ⚠️  {issue}")
            
            elif test_name == "search":
                logger.info(f"   - Total queries tested: {len(test_results.get('queries', []))}")
                logger.info(f"   - Total results found: {test_results.get('total_results', 0)}")
                
                for query_result in test_results.get('queries', []):
                    status = "✅" if query_result.get('success') else "❌"
                    logger.info(f"   {status} '{query_result['query']}': {query_result.get('rag_results', 0)} results")
            
            elif test_name == "deduplication":
                logger.info(f"   - Deduplication working: {test_results.get('deduplication_working', False)}")
                logger.info(f"   - Original node: {test_results.get('original_node_id', 'N/A')}")
            
            elif test_name == "similarity_pruning":
                logger.info(f"   - Total worker stories: {test_results.get('total_worker_stories', 0)}")
                logger.info(f"   - Potential duplicates: {test_results.get('potential_duplicates', 0)}")
                logger.info(f"   - Content length variance: {test_results.get('content_length_stats', {}).get('variance', 0):.2f}")
            
            elif test_name == "memory_cleanup":
                logger.info(f"   - Total nodes: {test_results.get('total_nodes', 0)}")
                logger.info(f"   - Cleanup issues: {test_results.get('issues_count', 0)}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Memory Management Test Suite Complete")
    
    # Save results to file
    with open("/app/test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("📄 Results saved to /app/test_results.json")

if __name__ == "__main__":
    main() 