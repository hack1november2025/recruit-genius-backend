import asyncio
from app.agents.job_generator.graph import create_job_generator_graph

async def test():
    print('Testing async graph creation...')
    graph = await create_job_generator_graph()
    print('✅ Async graph created successfully!')

if __name__ == "__main__":
    asyncio.run(test())
