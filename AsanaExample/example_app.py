import os
import asyncio
import aiohttp
import sys
from Utilities import DB, PySecrets
from baseLogger import logger

from Utilities.asana_client import asana_client


async def main():
    # define the and HTTP async sessions
    async with aiohttp.ClientSession() as session:

        project_gids = [('1203157790092137', {'data': {'custom_fields': {'1203191009110006': '1203191009110010', '1203064325052098': '1203064325052099', '1203141614850471': None, '1203064649552811': None, '1203064570776952': None, '1203064587488958': None, '1203064655704252': None, '1203064685013448': None, '1203064591904241': None, '1203064692994019': None, '1203064592660529': '40.0', '1203064660490479': '61', '1203064661029768': 'FE_O02-0052'}}})]
        db = DB()
        secrets = PySecrets()
        results = db.retrieve_secrets(secret='pat')
        for result in results:
            _pat = result.password
        token = secrets.make_public(secret=_pat)  # os.getenv("SERVICE_ACCT")

        # create an array of async tasks
        get_project_items_tasks = []
        for gid, data in project_gids:
            get_project_items_tasks.append(
                asana_client(
                    "PUT", f"/projects/{gid}", session, token=token, data=data
                )
            )

        array_of_task_responses = await asyncio.gather(*get_project_items_tasks)
        # print(array_of_task_responses)
        for task in array_of_task_responses:
            logger.info(task)

    return


# if this file is run directly via Python:
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted - goodbye")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
