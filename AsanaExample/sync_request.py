import requests
import os
import time

api_key = 'HPFXP99H9XQD6TWE'
url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={}&interval=5min&apikey={}'
symbols = ['AAPL', 'GOOG', 'TSLA', 'MSFT', 'IBM']
results = []

start = time.perf_counter()
for symbol in symbols:
    print(f"Working on symbol {symbol}")
    response = requests.get(url.format(symbol, api_key))
    results.append(response.json())
end = time.perf_counter()
total_time = end - start
print(f"It took {total_time} seconds to make {len(symbols)} API calls")