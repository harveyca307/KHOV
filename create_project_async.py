"""
Usage:
    create_project_async <file>
    create_project_async (-h | --version)

Positional Arguments:
    <file>          YAML File

Options:
    -h              Show this screen
    --version       Show Version Information

"""
import asyncio
import time

import aiohttp
import yaml
from TM1py import TM1Service
from TM1py.Exceptions import TM1pyException
from docopt import docopt

from AsanaExample.asana_client import asana_client
from Utilities import DB, PySecrets
from baseLogger import logger

APP_NAME = 'CIP-CreateProject'
APP_VERSION = '1.0'


def get_confing(_dict: dict) -> dict:
    _user = None
    _pass = None
    db = DB()
    secrets = PySecrets()
    base_url = _dict['Config']['base_url']
    instance = _dict['Config']['instance']
    results = db.retrieve_secrets(secret=instance)
    for result in results:
        _user = result.username
        _pass = result.password
    username = secrets.make_public(secret=_user)
    password = secrets.make_public(secret=_pass)
    config = {
        'base_url': base_url,
        'user': username,
        'password': password,
        'ssl': True,
        'verify': True,
        'async_requests_mode': True,
        'session_context': APP_NAME
    }
    return config


def read_yml(_dict: str) -> dict:
    work = []
    community_work = {'data': {}}
    for community in _dict['Projects']:
        _template = _dict['Projects'][community]['template']
        _team = _dict['Projects'][community]['team']
        _start = _dict['Projects'][community]['start_date']
        community_work['data']['name'] = community
        community_work['data']['public'] = False
        community_work['data']['team'] = _team
        community_work['data']['requested_dates'] = [{'gid': '1', 'value': _start}]
        work.append((_template, community_work))
    return work


async def main(projects: dict, config: dict) -> None:
    async with aiohttp.ClientSession() as session:
        db = DB()
        secrets = PySecrets()
        results = db.retrieve_secrets('pat')
        for result in results:
            _pat = result.password
        token = secrets.make_public(secret=_pat)

        _projects = read_yml(_dict=projects)

        tasks = []
        for template, community in _projects:
            tasks.append(
                asana_client(
                    "POST", f"/project_templates/{template}/instantiateProject", session=session, token=token,
                    data=community
                )
            )
        array_of_tasks_responses = await asyncio.gather(*tasks)
        for task in array_of_tasks_responses:
            logger.info(f"{APP_NAME} - created '{task['data']['new_project']['name']}' with GID "
                        f"{task['data']['new_project']['gid']}")
            _name = task['data']['new_project']['name']
            _tm1_obj = projects['Projects'][_name]['tm1_object']
            print(task['data']['new_project']['gid'], projects['Projects'][_name]['tm1_object'])
            cellset = {(_tm1_obj, "CIP Asana Project GID"): task['data']['new_project']['gid']}
            try:
                with TM1Service(**config) as tm1:
                    logger.info(f"Updating TM1 Attributes for {_name}, GID: {task['data']['new_project']['gid']}")
                    tm1.cubes.cells.write_values('}ElementAttributes_Org', cellset)
            except TM1pyException as t:
                logger.info(f"{APP_NAME} {t}")


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_NAME}")
    logger.info("\n")
    logger.info(f"{APP_NAME} started")
    _file = cmd_args.get("<file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _config = get_confing(_yml)
    asyncio.run(main(projects=_yml, config=_config))
    end = time.perf_counter()
    logger.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
