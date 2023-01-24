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
import logging
import os
import sys
import time

import aiohttp
import yaml
from TM1py import TM1Service
from TM1py.Exceptions import TM1pyException
from docopt import docopt

from Utilities import DB, PySecrets
from Utilities.asana_client import asana_client

APP_NAME = 'CIP-CreateProject'
APP_VERSION = '1.0'
LOG_FILE = APP_NAME + '.log'


def retrieve_pat() -> str:
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _pat = secrets.make_public(secret=_pass)
    return _pat


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
        'namespace': 'LDAP',
        'ssl': True,
        'verify': True,
        'async_requests_mode': True,
        'session_context': APP_NAME
    }
    return config


def read_yml(_dict: str) -> tuple:
    work = []
    _tm1_objs = {}
    for community in _dict['Projects']:
        community_work = {'data': {}}
        _template = _dict['Projects'][community]['template']
        _team = _dict['Projects'][community]['team']
        _start = _dict['Projects'][community]['start_date']
        community_work['data']['name'] = community
        community_work['data']['public'] = False
        community_work['data']['team'] = _team
        community_work['data']['requested_dates'] = [{'gid': '1', 'value': _start}]
        work.append((_template, community_work))
        _tm1_objs[community] = _dict['Projects'][community]['tm1_object']
    return work, _tm1_objs


async def main(projects: dict, config: dict, token: str, tm1_elements: dict) -> None:
    async with aiohttp.ClientSession() as session:

        tasks = []
        for template, community in projects:
            tasks.append(
                asana_client(
                    "POST", f"/project_templates/{template}/instantiateProject", session=session, token=token,
                    data=community
                )
            )
        array_of_tasks_responses = await asyncio.gather(*tasks)
        for task in array_of_tasks_responses:
            logging.info(f"{APP_NAME} - created '{task['data']['new_project']['name']}' with GID "
                         f"{task['data']['new_project']['gid']}")
            _name = task['data']['new_project']['name']
            _tm1_obj = tm1_elements[_name]
            cellset = {(_tm1_obj, "CIP Project GID"): task['data']['new_project']['gid']}
            try:
                with TM1Service(**config) as tm1:
                    logging.info(f"Updating TM1 entries for {_name}, GID: {task['data']['new_project']['gid']}")
                    tm1.cubes.cells.write_values('CIP Org Property', cellset)
                    logging.info(f"{APP_NAME} updated PA with GID {task['data']['new_project']['gid']}")
            except TM1pyException as t:
                logging.info(f"{APP_NAME} {t}")


if __name__ == '__main__':
    start = time.perf_counter()
    configure_logging()
    set_current_directory()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_NAME}")
    logging.info(f"{APP_NAME} started")
    _file = cmd_args.get("<file>")

    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _config = get_confing(_yml)
    pat = retrieve_pat()
    _projects, tm1_obs = read_yml(_dict=_yml)
    asyncio.run(main(projects=_projects, config=_config, token=pat, tm1_elements=tm1_obs))
    end = time.perf_counter()
    logging.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
