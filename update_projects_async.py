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
import logging
import os
import sys
import time

import aiohttp
import yaml
from docopt import docopt

from Utilities import DB, PySecrets, asana_client

APP_NAME = 'CIP-UpdateProjectAttributes'
APP_VERSION = '2.0'
LOG_FILE = APP_NAME + '.log'


def set_current_directory() -> None:
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)
    directory = os.path.dirname(application_path)
    os.chdir(directory)


def configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        format="%(asctime)s - " + APP_NAME + " - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # also log to stdout
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def retrieve_pat() -> str:
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _pat = secrets.make_public(secret=_pass)
    return _pat


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


async def main(projects: list, pat: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = pat

        get_project_task_items = []
        for gid, data in projects:
            get_project_task_items.append(
                asana_client(
                    "PUT", f"/projects/{gid}", session=session, token=token, data=data
                )
            )

        array_of_tasks_responses = await asyncio.gather(*get_project_task_items)
        for task in array_of_tasks_responses:
            logging.info(f"{APP_NAME} -- GID: {task['data']['gid']} Modified: {task['data']['modified_at']}")


if __name__ == '__main__':
    start = time.perf_counter()
    configure_logging()
    set_current_directory()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info(f"Starting process {APP_NAME}, File sent={cmd_args['<file>']}")
    _file = cmd_args.get("<file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _token = retrieve_pat()
    _projects = get_projects(fields=_yml)
    try:
        asyncio.run(main(projects=_projects, pat=_token))
        end = time.perf_counter()
        logging.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
    except Exception as e:
        logging.error(e)
