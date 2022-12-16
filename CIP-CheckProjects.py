"""
Usage:
    CIP-CheckProjects <file> <out_file>
    CIP-CheckProjects (-h | --version)

Positional Arguments:
    <file>      YAML File
    <out_file>  Path and name of CSV to output

Options:
    -h          Show this screen
    --version   Show version information
"""
import logging
import os
import sys
import time

import asana
import pandas as pd
import yaml
from asana.error import NotFoundError
from docopt import docopt

from Utilities import DB, PySecrets

APP_NAME = 'CIP-CheckProjects'
APP_VERSION = '2.0'
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


def main(token: str, projects: dict, out_file: str):
    communities = []
    client = asana.Client.access_token(token)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    logging.info("Beginning check")
    for project in projects:
        try:
            results = client.projects.get_project(projects[project])
            if results['name'] != project:
                communities.append(['Name Change', projects[project], project])
            else:
                communities.append(['Found', projects[project], project])
        except NotFoundError:
            communities.append(['Not Found', projects[project], project])
    logging.info("Check complete")
    df = pd.DataFrame(communities)
    df.columns = ['Status', 'GID', 'Name']
    df.to_csv(out_file, index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    set_current_directory()
    configure_logging()
    logging.info(f"Starting process.  Creating file '{cmd_args['<out_file>']}'")
    pat = retrieve_pat()
    _file = cmd_args.get("<file>")
    _outfile = cmd_args.get("<out_file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    try:
        main(token=pat, projects=_yml, out_file=_outfile)
        end = time.perf_counter()
        logging.info(f"Process finished in {round(end - start, 2)} seconds")
    except Exception as e:
        logging.error(e)
        logging.info(f"Process produced errors")
