import json
import asyncio
import aiohttp
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def asana_tasks(method, url, session, **kwargs):
    """
    method, url, aiohttp session, [token, params, data]

    client that automates certain actions around making async requests to asana.

    """
    backoff_seconds = 0.520
    retryError = 429
    attempt = 0
    _gid = url[10:26]

    base_url = "https://app.asana.com/api/1.0"
    full_url = base_url + url

    if "data" in kwargs:
        data = json.dumps(kwargs["data"])
    else:
        data = {}

    if "params" in kwargs:
        params = kwargs["params"]
    else:
        params = {}

    headers = {"Authorization": "Bearer " + kwargs["token"]}

    result = False

    while ((retryError == 429) or (retryError == 500)) and (attempt < 10):
        # pause execution before trying again

        if attempt == 6:
            print("Hitting rate limits. slowing down calls...")

        if attempt == 8:
            print("Thanks for your patience. still slow.")

        try:
            response = await session.request(
                method,
                url=full_url,
                data=data,
                params=params,
                headers=headers,
                raise_for_status=False,
            )
            retryError = response.status

            if retryError >= 400:
                if (response.status != 429) and (response.status != 500):
                    error_json = await response.json()
                    print(error_json["errors"][0]["message"])
                    print("HTTP Error: ", response.status)
                    return error_json
            else:
                response_content = await response.json()
                response_content['community'] = _gid

                return response_content

        except aiohttp.client_exceptions.ClientResponseError as e:
            if (response.status != 429) and (response.status != 500):
                print("HTTP Error: ", response.status)
                error_json = await response.json()
                print(error_json["errors"][0]["message"])
                return error_json

        # Exponential backoff in seconds = constant * attempt^2
        retry_time = backoff_seconds * attempt * attempt

        print(
            f"The script is hitting rate limits (too many calls/minute). "
            f"Waiting for {retry_time} seconds before continuing"
        )
        await asyncio.sleep(retry_time)
        attempt += 1

    if attempt >= 10:
        print("Too many requests hit rate limits - timed out")

    return result
