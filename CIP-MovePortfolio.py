"""
Usage:
    CIP-MovePortfolio <project> <existing_portfolio> <new_portfolio>
    CIP-MovePortfolio (-h | --version)

Positional Arguments:
    <project>               Project GID
    <existing_portfolio>    Existing portfolio GID
    <new_portfolio>         New portfolio GID

Options:
    -h                      Show this screen
    --version               Show version information
"""

import logging
import os
import sys
import time

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


def main(token: str, **kwargs):
    port_items = []
    project = kwargs.get("<project>")
    remove_port = kwargs.get("<existing_portfolio>")
    new_port = kwargs.get("<new_portfolio>")
    client = asana.Client.access_token(accessToken=token)
    try:
        client.portfolios.get_portfolio(remove_port)
    except asana.error.NotFoundError:
        logging.error(f"Existing portfolio: {remove_port} not found, exiting")
        sys.exit()
    try:
        client.portfolios.get_portfolio(new_port)
    except not asana.error.NotFoundError:
        logging.error(f"New portfolio: {new_port} not found")
        sys.exit()
    results = client.portfolios.get_items_for_portfolio(remove_port, opt_pretty=True)
    for result in results:
        port_items.append(result['gid'])
    if project not in port_items:
        logging.error(f"{project} not in portfolio {remove_port}")
        sys.exit()
    else:
        try:
            client.portfolios.add_item_for_portfolio(new_port, {'item': project}, opt_pretty=True)
            client.portfolios.remove_item_for_portfolio(remove_port, {'item': project}, opt_pretty=True)
            logging.info(f"Project: {project} was moved from {remove_port} to {new_port}")
        except asana.error.AsanaError as a:
            logging.error(a)


if __name__ == '__main__':
    start = time.perf_counter()
    set_current_directory()
    configure_logging()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info("Starting process")
    pat = retrieve_pat()
    try:
        main(token=pat, **cmd_args)
        end = time.perf_counter()
        logging.info(f"Process finished in {round(end - start, 2)} seconds.")
    except Exception as e:
        logging.error(e)
