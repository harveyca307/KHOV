"""
Usage:
    update_projects_async <file>
    update_projects_async (-h | --version)

Positional Arguments:
    <file>          YAML Attribute File

Options:
    -h              Show this screen
    --version       Show Version Information
"""
import asyncio
import os
import sys
import time

import aiohttp
import yaml
from docopt import docopt

from AsanaExample.asana_client import asana_client
from Utilities import DB, PySecrets
from baseLogger import logger

APP_NAME = 'CIP-UpdateProjectAttributes'
APP_VERSION = '2.0'


def get_projects(fields: dict) -> list:
    work = []
    for project in fields:
        _dict = {}
        _entries = {}
        _data = {}
        project_id = fields[project]['project_id']
        _custom_fields = fields[project]['custom_fields']
        for key, value in _custom_fields.items():
            _dict[key] = value
        _entries['custom_fields'] = _dict
        _data['data'] = _entries
        _data['data']['name'] = project
        work.append((project_id, _data))
    return work


async def main(fields: dict) -> None:
    async with aiohttp.ClientSession() as session:
        db = DB()
        secrets = PySecrets()
        results = db.retrieve_secrets(secret='pat')
        for result in results:
            pat = result.password
        token = secrets.make_public(secret=pat)
        projects = get_projects(fields=fields)

        get_project_task_items = []
        for gid, data in projects:
            get_project_task_items.append(
                asana_client(
                    "PUT", f"/projects/{gid}", session=session, token=token, data=data
                )
            )

        array_of_tasks_responses = await asyncio.gather(*get_project_task_items)
        for task in array_of_tasks_responses:
            logger.info(f"{APP_NAME} -- GID: {task['data']['gid']} Modified: {task['data']['modified_at']}")


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info("\n")
    logger.info(f"Starting process {APP_NAME}, File sent={cmd_args['<file>']}")
    _file = cmd_args.get("<file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    try:
        asyncio.run(main(fields=_yml))
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os.exit(0)
    end = time.perf_counter()
    logger.info(f"{APP_NAME} finished in {round(end-start, 4)} seconds")
