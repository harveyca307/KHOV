"""
Usage:
    temp_delete
    temp_delete (-h | --version)

Options:
    -h          Show this screen
    --version   Show version information
"""

from TM1py import TM1Service
from datetime import datetime
from docopt import docopt
import pandas as pd

APP_NAME = "temp_delete"
APP_VERSION = "1.0"

conn = {
    'address': 'PA',
    'port': 17471,
    'ssl': False,
    'user': 'admin',
    'password': 'apple',
    'session_context': APP_NAME
}


def main():
    with TM1Service(**conn) as tm1:
        fromstamp = datetime(year=2022, month=8, day=17, hour=16, minute=0, second=0)
        tostamp = datetime(year=2022, month=8, day=17, hour=16, minute=59, second=0)
        entries = tm1.server.get_transaction_log_entries(since=fromstamp, until=tostamp)

        df = pd.DataFrame(entries)
        df.to_csv('chad.csv', index=False)


if __name__ == "__main__":
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    main()
