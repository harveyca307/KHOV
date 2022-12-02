"""
Usage:
    CIP-GetProjectTasks <file_in> <file_out>
    CIP-GetProjectTasks (-h | --version)

Positional Arguments:
    <file_in>      YAML File
    <file_out>     Output file name

Options:
    -h          Show this screen
    --version   Show version information
"""
import asyncio
import logging
import os
import sys
import time

import aiohttp
import pandas as pd
import yaml
from docopt import docopt

from Utilities import DB, PySecrets, asana_tasks

APP_NAME = "CIP-GetProjectTasks"
APP_VERSION = '2.5'
LOG_FILE = APP_NAME + '.log'


def set_current_directory() -> None:
    global LOG_FILE
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)
    directory = os.path.dirname(application_path)
    LOG_FILE = os.path.join(application_path, LOG_FILE)
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
                if item['assignee'] is not None:
                    _assignee = item['assignee']['gid']
                else:
                    _assignee = None
                _due = item['due_on']
                _start = item['start_on']
                _completed = str(item['completed_at'])[0:10]
                for field in item['custom_fields']:
                    _field_name = field['name']
                    if _field_name == 'CIP-Milestone':
                        _milestone = _field_name
                        _milestone_val = field['display_value']
                    elif _field_name == "CIP-Team":
                        _team = _field_name
                        _team_val = field['display_value']
                    elif _field_name == "CIP-Actual Date":
                        _actual = _field_name
                        _actual_dt = str(field['display_value'])[0:10]
                    elif _field_name == "CIP-Line ID":
                        _line = _field_name
                        _line_id = field['display_value']
                # Only output fields with CIP-LineIDs
                if _line_id:
                    if _assignee is not None and _assignee != 'None':
                        output.append([_community, _name, _line_id, 'Assignee', _assignee])
                    if _due is not None:
                        output.append([_community, _name, _line_id, 'Due On', _due])
                    if _start is not None:
                        output.append(([_community, _name, _line_id, 'Start On', _start]))
                    if _completed is not None and _completed != 'None':
                        output.append([_community, _name, _line_id, 'Completed On', _completed])
                    if _milestone_val is not None:
                        output.append([_community, _name, _line_id, _milestone, _milestone_val])
                    if _team_val is not None:
                        output.append([_community, _name, _line_id, _team, _team_val])
                    if _actual_dt is not None and _actual_dt != 'None':
                        output.append([_community, _name, _line_id, _actual, _actual_dt])
                    if _line_id is not None:
                        output.append([_community, _name, _line_id, _line, _line_id])

    df = pd.DataFrame(output)
    if len(df) > 0:
        df.columns = ['Community', 'Task', 'LineID', 'Field', 'Value']
        df.to_csv(str(output_file), index=False)
    else:
        logging.info("No data received")


if __name__ == '__main__':
    start = time.perf_counter()
    set_current_directory()
    configure_logging()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info(f"Starting {APP_NAME}, File sent={cmd_args['<file_in>']}, Outfile={cmd_args['<file_out>']}")
    _file = str(cmd_args.get('<file_in>'))
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _token = retrieve_pat()
    _projects = retrieve_project_list(fields=_yml)
    _output = str(cmd_args.get("<file_out>"))
    asyncio.run(main(projects=_projects, pat=_token, output_file=_output))
    end = time.perf_counter()
    logging.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds")
