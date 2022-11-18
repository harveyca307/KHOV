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
import time

import aiohttp
import pandas as pd
import yaml
from docopt import docopt

from Utilities import DB, PySecrets, asana_tasks
from baseLogger import logger

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


async def main(projects: list, pat: str, output_file: str) -> None:
    async with aiohttp.ClientSession() as session:
        token = pat

        task_items = []
        proj_dict = {}
        for community, gid in projects:
            task_items.append(
                asana_tasks(
                     "GET", f"/projects/{gid}/tasks", session=session, token=token, params="opt_fields=name,"
                                                                                           "due_on,"
                                                                                           "start_on,"
                                                                                           "completed_at,"
                                                                                           "assignee,"
                                                                                           "custom_fields"
                )
            )
            proj_dict[gid] = community

        array_of_responses = await asyncio.gather(*task_items)
        output = []
        for response in array_of_responses:
            _community = response['community']
            _community = proj_dict[_community]
            for item in response['data']:
                _name = item['name']
                _assignee = item['assignee']['gid']
                _due = item['due_on']
                _start = item['start_on']
                _completed = str(item['completed_at'])[0:10]
                _milestone = item['custom_fields'][0]['name']
                _milestone_val = item['custom_fields'][0]['display_value']
                _team = item['custom_fields'][1]['name']
                _team_val = item['custom_fields'][1]['display_value']
                _actual = item['custom_fields'][2]['name']
                _actual_dt = str(item['custom_fields'][2]['display_value'])[0:10]
                _line = item['custom_fields'][3]['name']
                _line_id = item['custom_fields'][3]['display_value']
                if _assignee is not None and _assignee != 'None':
                    output.append([_community, _name, 'Assignee', _assignee])
                if _due is not None:
                    output.append([_community, _name, 'Due On', _due])
                if _start is not None:
                    output.append(([_community, _name, 'Start On', _start]))
                if _completed is not None and _completed != 'None':
                    output.append([_community, _name, 'Completed On', _completed])
                if _milestone_val is not None:
                    output.append([_community, _name, _milestone, _milestone_val])
                if _team_val is not None:
                    output.append([_community, _name, _team, _team_val])
                if _actual_dt is not None and _actual_dt != 'None':
                    output.append([_community, _name, _actual, _actual_dt])
                if _line_id is not None:
                    output.append([_community, _name, _line, _line_id])

    df = pd.DataFrame(output)
    df.columns = ['Community', 'Task', 'Field', 'Value']
    df.to_csv(output_file, index=False)


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
    _output = fr"{_yml['Config']['output_directory']}"
    try:
        asyncio.run(main(projects=_projects, pat=_token, output_file=_output))
    except KeyboardInterrupt:
        pass
    end = time.perf_counter()
    logger.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
