"""
Usage:
    update_project_fields <file>
    update_project_fields (-h | --version)

Positional Arguments:
    <file>      <YAML File>

Options:
    -h          Show this screen
    --version   Show version information
"""

from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

import asana
import asana.error as ae
import yaml
from docopt import docopt

from Utilities import DB, PySecrets
from baseLogger import logger

APP_NAME = "CIP-UpdateProjectFields"
APP_VERSION = '1.0'


def update_proj(pat: str, project_id: str, project: str, custom_fields: dict) -> None:
    logger.info(f"{APP_NAME} - Updating Project: {project}:{project_id} custom_fields: {custom_fields}")
    client = asana.Client.access_token(pat)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    try:
        client.projects.update_project(project_id, custom_fields)
    except ae.AsanaError as e:
        logger.info(e)


def main(fields: dict) -> None:
    db = DB()
    secrets = PySecrets()

    _pat = None
    entries = db.retrieve_secrets(secret='pat')
    for entry in entries:
        _pat = entry.password

    pat = secrets.make_public(secret=_pat)

    jobs = []
    _dict = {}
    _args = dict()
    for project in fields:
        _entries = dict()
        _project = fields[project]['project_id']
        _cust = fields[project]["custom_fields"]
        for key, value in _cust.items():
            _dict[key] = value
        _entries['custom_fields'] = _dict
        process = multiprocessing.Process(target=update_proj, args=(pat, _project, project, _entries))
        process.start()


if __name__ == "__main__":
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info("\n")
    logger.info(f"Starting process {APP_NAME}, File sent: {cmd_args['<file>']}")
    _file = cmd_args.get("<file>")
    stream = open(_file, 'r')
    _yml = yaml.load(stream, Loader=yaml.FullLoader)
    main(fields=_yml)
    stream.close()
