"""
Usage:
    get_project_tasks
    get_project_tasks (-h | --version)

Options:
    -h                  Show this screen
    --version           Show Version Information
"""
from docopt import docopt
import asyncio
import aiohttp
import time
from Utilities.asana_client import asana_client
from Utilities import DB, PySecrets
from baseLogger import logger

APP_NAME = "CIP-GetProjectTasks"
APP_VERSION = '1.0'
WORKSPACE = '35623093886266'


async def get_projects_for_workspace() -> list:
    async with aiohttp.ClientSession() as session:
        db = DB()
        secrets = PySecrets()
        results = db.retrieve_secrets(secret='pat')
        for result in results:
            _pat = result.password
        token = secrets.make_public(secret=_pat)
        get_project_list = [asana_client(
            "GET", f"/workspaces/{WORKSPACE}/projects", session=session, token=token
        )]
        array_of_project = await asyncio.gather(*get_project_list)
    return array_of_project


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        db = DB()
        secrets = PySecrets()
        results = db.retrieve_secrets(secret='pat')
        for result in results:
            _pat = result.password
        token = secrets.make_public(secret=_pat)
        projects = await get_projects_for_workspace()
        list_of_projects = []
        for project in projects:
            for g in project['data']:
                list_of_projects.append(g['gid'])
        project_tasks = []
        for project in list_of_projects:
            project_tasks.append(
                asana_client(
                    "GET", f"/projects{project}/tasks", session=session, token=token
                )
            )
        array_of_tasks = await asyncio.gather(*project_tasks)


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info('\n')
    logger.info(f"{APP_NAME} started, for workspace {WORKSPACE}")
    asyncio.run(main())
    end = time.perf_counter()
    logger.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
