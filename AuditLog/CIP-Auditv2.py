"""
Usage:
    CIP-AuditLogs <outfile> <start_at>
    CIP-AuditLogs (-h | --version)

Positional Arguments:
    <outfile>   Path and name of file to be output

Options:
    -h          Show this screen
    --version   Show version information
"""

import json
import logging
import os
import sys
import time

import pandas as pd
import requests
from docopt import docopt

from Utilities import DB, PySecrets

APP_NAME = 'CIP-Audit'
APP_VERSION = '2.0'
LOG_FILE = APP_NAME + '.log'
WORKSPACE = '35623093886266'
# Copyrite 2023 Application Consulting Group, Inc.


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


def retrieve_token() -> str:
    db = DB()
    secrets = PySecrets()
    _pass = None
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _pass = result.password
    _token = secrets.make_public(secret=_pass)
    return _token


def main(token: str, file: str, start: str) -> bool:
    base_url = f'https://app.asana.com/api/1.0/workspaces/{WORKSPACE}/audit_log_events'
    logging.info("Beginning log retrieval")
    url = base_url + f"?start_at={start}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }
    logs = []
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    for row in data['data']:
        logs.append(row)
    while data['data']:
        uri = url + f"&offset={data['next_page']['offset']}"
        response = requests.get(uri, headers=headers)
        data = json.loads(response.text)
        for row in data['data']:
            logs.append(row)
    df = pd.DataFrame(logs)
    logging.info(f"Log retrieval complete. Retrieved {len(df)} records")
    df.to_csv(file, index=False)


if __name__ == '__main__':
    start = time.perf_counter()
    set_current_directory()
    configure_logging()
    logging.info(f'{APP_NAME} Starting')
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    _file = cmd_args.get("<outfile>")
    _start = cmd_args.get("<start_at>")
    _token = retrieve_token()
    logging.info(f"Retrieving records beginning '{_start}'")
    try:
        main(token=_token, file=_file, start=_start)
    except Exception as e:
        logging.error(f"{APP_NAME} - Error: {str(e)}")
    finally:
        end = time.perf_counter()
        logging.info(f"{APP_NAME} finished.  Duration: {round(end - start, 2)} seconds")
