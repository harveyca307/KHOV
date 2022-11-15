import asyncio
import aiohttp
import time

api_key = 'HPFXP99H9XQD6TWE'
url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol={}&apikey={}'
symbols = ['AAPL', 'GOOG', 'TSLA', 'MSFT', 'IBM']
results = []
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

start = time.perf_counter()


def get_tasks(session):
    tasks = []
    for symbol in symbols:
        tasks.append(asyncio.create_task(session.get(url.format(symbol, api_key), ssl=False)))
    return tasks


async def get_symbols():
    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(session)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())


asyncio.run(get_symbols())

end = time.perf_counter()
total_time = end - start
print(f"It took {total_time} seconds to make {len(symbols)} API calls")
