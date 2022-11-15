"""
Usage:
    get_project_tasks_async <file>
    get_project_tasks_async (-h | --version)

Positional Arguments:
    <file>      YAML File

Options:
    -h          Show this screen
    --version   Show version information
"""
import asyncio
import os
import time

import aiohttp
import pandas as pd
import yaml
from TM1py import TM1Service
from TM1py.Exceptions import TM1pyException
from docopt import docopt

from Utilities import asana_client, DB, PySecrets
from baseLogger import logger, application_path

APP_NAME = "CIP-GetProjectTasks"
APP_VERSION = '1.0'


def retrieve_pat() -> str:
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _pat = secrets.make_public(secret=_pass)
    return _pat


def retrieve_project_list(fields: dict) -> list:
    work = []
    for project in fields['Projects']:
        work.append((project, fields['Projects'][project]))
    return work


def get_tm1_config(conf: dict) -> dict:
    _base_url = conf.get('base_url')
    _instance = conf.get('instance')
    _user = None
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret=_instance)
    for result in results:
        _user = result.username
        _pass = result.password
    username = secrets.make_public(secret=_user)
    password = secrets.make_public(secret=_pass)
    _return = {
        'base_url': _base_url,
        'user': username,
        'namespace': 'LDAP',
        'password': password,
        'ssl': True,
        'verify': True,
        'async_requests_mode': True
    }
    return _return


async def main(projects: list, pat: str, config: dict):
    async with aiohttp.ClientSession() as session:
        token = pat

        task_items = []
        for community, gid in projects:
            task_items.append(
                asana_client(
                    "GET", f"/projects/{gid}/tasks", session=session, token=token, params="opt_fields=name,"
                                                                                          "due_on,"
                                                                                          "start_on,"
                                                                                          "custom_fields,"
                                                                                          "projects"
                )
            )

        array_of_responses = await asyncio.gather(*task_items)
        output = []
        for response in array_of_responses:
            for item in response['data']:
                _name = item['name']
                _due = item['due_on']
                _start = item['start_on']
                _gid = item['gid']
                _community = item['projects']
                _milestone_val = item['custom_fields'][0]['display_value']
                _team_val = item['custom_fields'][1]['display_value']
                _actual_dt = item['custom_fields'][2]['display_value']
                _line_id = item['custom_fields'][3]['display_value']
                output.append([_community[0]['gid'], _name, _due, _start, _milestone_val, _team_val, _actual_dt,
                               _line_id])
    df = pd.DataFrame(output)
    df.columns = ['Community', 'Name', 'Due On', 'Start On', 'CIP-Milestone', 'CIP-Team', 'CIP-Actual Date',
                  'CIP-Line ID']
    df.to_csv(os.path.join(application_path, 'test.csv'), index=False)
    try:
        with TM1Service(**config) as tm1:
            print(tm1.server.get_product_version())
    except TM1pyException as t:
        logger.info(f"{APP_NAME} - {t}")


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info("\n")
    logger.info(f"Starting {APP_NAME}, File sent={cmd_args['<file>']}")
    _file = cmd_args.get('<file>')
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _token = retrieve_pat()
    _projects = retrieve_project_list(fields=_yml)
    _config = get_tm1_config(conf=_yml['Config'])
    try:
        asyncio.run(main(projects=_projects, pat=_token, config=_config))
    except KeyboardInterrupt:
        pass
    end = time.perf_counter()
    logger.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
