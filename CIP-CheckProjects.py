"""
Usage:
    CIP-CheckProjects <file>
    CIP-CheckProjects (-h | --version)

Positional Arguments:
    <file>      YAML File

Options:
    -h          Show this screen
    --version   Show version information
"""
from docopt import docopt
import yaml
import os
import sys
import asana
from asana.error import NotFoundError
import logging
import time
from Utilities import DB, PySecrets

APP_NAME = 'CIP-CheckProjects'
APP_VERSION = '1.0'
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
    # Also log to stdout
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def retrieve_pat() -> str:
    _pat = None
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _pat = secrets.make_public(secret=_pass)
    return _pat


def main(token: str, projects: dict):
    client = asana.Client.access_token(token)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    for project in projects:
        try:
            results = client.projects.get_project(projects[project])
            if results['name'] != project:
                logging.error(f"Project: {project} has been renamed to {results['name']}")
        except NotFoundError:
            logging.error(f"Project: {project} - GID: {projects[project]} not found")


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    set_current_directory()
    configure_logging()
    logging.info("Starting process")
    pat = retrieve_pat()
    _file = cmd_args.get("<file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    try:
        main(token=pat, projects=_yml)
        end = time.perf_counter()
        logging.info(f"Process finished in {round(end - start, 2)} seconds")
    except Exception as e:
        logging.error(e)
