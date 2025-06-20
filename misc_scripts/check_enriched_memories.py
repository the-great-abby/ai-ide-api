import asyncio
from memory import get_memorydb_session, MemoryVector

async def check_enriched_memories(limit=5):
    async with get_memorydb_session() as session:
        memories = await session.query(MemoryVector).filter(
            (MemoryVector.tags != None) | (MemoryVector.categories != None)
        ).limit(limit).all()
        print(f'Found {len(memories)} enriched memories:')
        for m in memories:
            print(f'ID: {m.id}\n  Tags: {m.tags}\n  Categories: {m.categories}\n  Content: {m.content[:100]}...\n')

if __name__ == "__main__":
    asyncio.run(check_enriched_memories()) 