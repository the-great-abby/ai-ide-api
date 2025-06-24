#!/usr/bin/env python3
"""
Test script for memory enrichment edge creation functionality.

This script demonstrates how the enhanced memory enrichment worker
creates edges between related memory nodes, transforming isolated
memories into a connected knowledge graph.
"""

import asyncio
import json
import sys
import os

# Add the current directory to the path so we can import the worker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_enrichment_worker import process_enrichment_job

async def test_edge_creation():
    """Test the edge creation functionality with a sample job."""
    
    print("🧪 Testing Memory Enrichment Edge Creation")
    print("=" * 50)
    
    # Test job configuration
    test_job = {
        "scope": "all",
        "dry_run": True,  # Start with dry run for safety
        "similarity_threshold": 0.85,
        "max_tags": 5,
        "batch_size": 10,
        "create_edges": True,
        "edge_types": ["tag_based", "content_ref"]
    }
    
    print(f"📋 Job Configuration:")
    print(json.dumps(test_job, indent=2))
    print()
    
    print("🚀 Running enrichment job with edge creation...")
    print("(This will show what would be created without making changes)")
    print()
    
    try:
        # Run the enrichment job
        result = await process_enrichment_job(test_job)
        
        print("✅ Enrichment job completed!")
        print("📊 Results:")
        print(f"   - Processed: {result.get('processed', 0)} memories")
        print(f"   - Errors: {result.get('errors', 0)}")
        print(f"   - Batches: {result.get('batches', 0)}")
        print(f"   - Edges Created: {result.get('edges_created', 0)}")
        print(f"   - Edges Skipped: {result.get('edges_skipped', 0)}")
        print(f"   - Edge Errors: {result.get('edge_errors', 0)}")
        print(f"   - Duration: {result.get('duration', 0):.2f}s")
        
        if result.get('status') == 'success':
            print("\n🎉 Test completed successfully!")
            print("\n💡 To run with actual changes (not dry run):")
            print("   test_job['dry_run'] = False")
            print("   await process_enrichment_job(test_job)")
        else:
            print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point."""
    print("🧪 Memory Enrichment Edge Creation Test")
    print("This test demonstrates the new edge creation functionality.")
    print()
    
    # Run the test
    asyncio.run(test_edge_creation())

if __name__ == "__main__":
    main() 