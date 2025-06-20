import asyncio
from db import MemorySessionLocal, MemoryVector

def check_enriched_memories(limit=5):
    with MemorySessionLocal() as session:
        memories = session.query(MemoryVector).filter(
            (MemoryVector.tags != None) | (MemoryVector.categories != None)
        ).limit(limit).all()
        print(f'Found {len(memories)} enriched memories:')
        for m in memories:
            print(f'ID: {m.id}')
            print(f'  Tags: {m.tags}')
            print(f'  Categories: {m.categories}')
            print(f'  Content: {m.content[:100]}...')
            print()

if __name__ == "__main__":
    check_enriched_memories() 