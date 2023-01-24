"""
Usage:
    CIP-Audit <outfile>
    CIP-Audit (-h | --version)

Positional Arguments:
    <outfile>   File to output

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

WORKSPACE = '35623093886266'
APP_NAME = 'CIP-Audit'
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
        level=logging.INFO
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def retrieve_pat() -> str:
    _pat = None
    _pass = None
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _pat = secrets.make_public(_pass)
    return _pat


def main(token: str, file: str) -> None:
    logs = []
    client = asana.Client.access_token(token)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    logging.info("Retrieving Audit Logs")
    results = client.audit_log_api.get_audit_log_events(WORKSPACE, opt_pretty=True)
    for result in results:
        logs.append(result)
    df = pd.DataFrame(logs)
    df.to_csv(file, index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version {APP_VERSION}")
    set_current_directory()
    configure_logging()
    logging.info(f"Starting process.  Creating file {cmd_args['<outfile>']}")
    pat = retrieve_pat()
    _file = cmd_args.get("<outfile>")
    try:
        main(token=pat, file=_file)
    except Exception as e:
        logging.error(str(e))
    finally:
        end = time.perf_counter()
        logging.info(f"Process finished in {round(end - start, 2)} seconds")
