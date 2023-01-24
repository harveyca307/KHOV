"""
Usage:
    GetUsers <file>
    GetUsers (-h | --version)

Positional Arguments:
    <file>      Full path of file to create

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
from docopt import docopt

from Utilities import DB, PySecrets

APP_NAME = 'CIP-GetUsers'
APP_VERSION = '1.1'
LOG_FILE = APP_NAME + '.log'

WORKSPACE = '35623093886266'


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


def main(file: str, pat: str) -> None:
    user_list = []
    client = asana.Client.access_token(pat)
    results = client.users.get_users({'workspace': WORKSPACE}, opt_fields={'name', 'gid', 'email'})
    for result in results:
        user_list.append([result['gid'], result['name'], result['email']])
    df = pd.DataFrame(user_list)
    df.columns = ['GID', 'Name', 'Email']
    df.to_csv(file, index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    configure_logging()
    set_current_directory()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logging.info(f"{APP_NAME} started")
    _file = cmd_args.get("<file>")
    _token = retrieve_pat()
    main(file=_file, pat=_token)
    end = time.perf_counter()
    logging.info(f"{APP_NAME} finished in {round(end - start, 2)} seconds.")
