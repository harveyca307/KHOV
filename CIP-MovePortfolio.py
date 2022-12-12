"""
Usage:
    CIP-MovePortfolio <file> <out_file>
    CIP-MovePortfolio (-h | --version)

Positional Arguments:
    <file>      YAML File
    <out_file>  Path and filename to create

Options:
    -h          Show this screen
    --version   Show version information
"""

import logging
import os
import sys
import time
import yaml
import pandas as pd

import asana
from asana.error import AsanaError
from docopt import docopt

from Utilities import DB, PySecrets

APP_NAME = 'CIP-MovePortfolio'
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


def main(token: str, moves: dict, outfile: str):
    port_items = []
    movements = []
    client = asana.Client.access_token(accessToken=token)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    for move in moves:
        for item in moves[move]:
            if item['Action'] == 'Add':
                try:
                    results = client.projects.get_project(str(item['Project']))
                except asana.error.NotFoundError:
                    logging.error(f"{move}: {item['Project']} does not exist")
                    sys.exit()
                port = str(item['Portfolio'])
                try:
                    results = client.portfolios.get_portfolio(port)
                    results = client.portfolios.get_items_for_portfolio(port, opt_pretty=True)
                    for result in results:
                        port_items.append(result['gid'])
                    if item['Project'] not in port_items:
                        client.portfolios.add_item_for_portfolio(port, {'item': str(item['Project'])}, opt_pretty=True)
                        movements.append(f"{move}: {item['Project']} was added to Portfolio: {item['Portfolio']}")
                except asana.error.NotFoundError:
                    logging.error(f"{move}: Target Portfolio {port} does not exist")
            if item['Action'] == 'Delete':
                try:
                    results = client.projects.get_project(str(item['Project']))
                except asana.error.NotFoundError:
                    logging.error(f"{move}: {item['Project']} does not exist")
                    sys.exit()
                try:
                    results = client.portfolios.get_portfolio(str(item['Portfolio']))
                    results = client.portfolios.get_items_for_portfolio(str(item['Portfolio']), opt_pretty=True)
                    port_items = []
                    for result in results:
                        port_items.append(result['gid'])
                    if item['Project'] in port_items:
                        client.portfolios.remove_item_for_portfolio(str(item['Portfolio']),
                                                                    {'item': str(item['Project'])})
                        movements.append(f"{move}: {item['Project']} was removed from Portfolio: {item['Portfolio']}")
                except asana.error.NotFoundError:
                    logging.error(f"{move}: Removal portfolio {str(item['Portfolio'])} does not exist")

    df = pd.DataFrame(movements)
    df.to_csv(outfile, index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    set_current_directory()
    configure_logging()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info("Starting process")
    pat = retrieve_pat()
    _file = cmd_args.get("<file>")
    _outfile = cmd_args.get("<out_file>")
    with open(_file, 'r') as stream:
        _yml = yaml.load(stream, Loader=yaml.FullLoader)
    try:
        main(token=pat, moves=_yml, outfile=_outfile)
        end = time.perf_counter()
        logging.info(f"Finished process in {round(end - start, 1)} seconds")
    except Exception as e:
        logging.error(e)
