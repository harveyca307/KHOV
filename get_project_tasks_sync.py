"""
Usage:
    CIP-GetProjectTasks <in_file> <out_file>
    CIP-GetProjectTasks (-h | --version)

Positional Arguments:
    <in_file>       YAML Community List
    <out_file>      Output file name and path

Options:
    -h              Show this screen
    --version       Show version information
"""
import logging
import os
import sys
import time

import asana
import pandas as pd
import yaml
from docopt import docopt

from Utilities import DB, PySecrets

APP_NAME = "CIP-GetProjectTasksNew"
APP_VERSION = '3.0'
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


def main(pat: str, project_list: list, outfile: str) -> None:
    assignee = None
    milestone_val = None
    milestone = None
    team_val = None
    team = None
    actual_val = None
    actual = None
    line_id = None
    work = []
    client = asana.Client.access_token(pat)
    client.options['max_retries'] = 20
    for project in project_list:
        tasks = client.tasks.get_tasks({'project': project[1]}, opt_fields={'name',
                                                                            'due_on',
                                                                            'start_on',
                                                                            'completed_at',
                                                                            'assignee',
                                                                            'custom_fields'},
                                       opt_pretty=True)
        for task in tasks:
            line_id_val = None
            name = task['name']
            if task['assignee'] is not None:
                assignee = task['assignee']['gid']
            due = task['due_on']
            start_on = task['start_on']
            completed = task['completed_at']
            for field in task['custom_fields']:
                f_name = field['name']
                f_val = field['display_value']
                if f_name == 'CIP-Milestone':
                    milestone = f_name
                    milestone_val = f_val
                elif f_name == 'CIP-Team':
                    team = f_name
                    team_val = f_val
                elif f_name == 'CIP-Actual Date':
                    actual = f_name
                    actual_val = str(f_val)[0:10]
                elif f_name == 'CIP-Line ID':
                    line_id = f_name
                    line_id_val = f_val
            if line_id_val:
                if assignee is not None and assignee != 'None':
                    work.append([project[0], name, line_id_val, 'Assignee', assignee])
                if due is not None:
                    work.append([project[0], name, line_id_val, 'Due On', due])
                if start is not None:
                    work.append([project[0], name, line_id_val, 'Start On', start_on])
                if completed is not None:
                    work.append([project[0], name, line_id_val, 'Completed At', completed])
                if milestone_val is not None:
                    work.append([project[0], name, line_id_val, milestone, milestone_val])
                if team_val is not None:
                    work.append([project[0], name, line_id_val, team, team_val])
                if actual_val is not None:
                    work.append([project[0], name, line_id_val, actual, actual_val])
                work.append([project[0], name, line_id_val, line_id, line_id_val])
    df = pd.DataFrame(work)
    if len(df) > 0:
        df.columns = ['Community', 'Task', 'LineID', 'Field', 'Value']
        df.to_csv(outfile, index=False)
    else:
        logging.info("No data received")


if __name__ == '__main__':
    start = time.perf_counter()
    set_current_directory()
    configure_logging()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info(f"Starting - File Sent: {cmd_args['<in_file>']}, Outfile: {cmd_args['<out_file>']}")
    _file = cmd_args.get("<in_file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    token = retrieve_pat()
    _projects = retrieve_project_list(fields=_yml)
    _output = cmd_args.get("<out_file>")
    main(pat=token, project_list=_projects, outfile=_output)
    end = time.perf_counter()
    logging.info(f"Finished in {round(end - start, 2)} seconds")
