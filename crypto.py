"""
Usage:
    Crypto --c <secret>
    Crypto --r <secret>
    Crypto --u <secret>
    Crypto --d <secret>
Arguments:
    --c <secret>     Create Secret
    --r <secret>     Retrieve Secret
    --u <secret>     Update Secret
    --d <secret>     Delete Secret
Options:
    -h, --help  Show this screen
    -version    Show Version Information
"""
from getpass import getpass

from docopt import docopt

from Utilities import DB, PySecrets
from baseLogger import logger


def strtobool(val: str) -> bool:
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    else:
        return False


# noinspection PyTypeChecker
def main(**kwargs):
    db = DB()
    secret = PySecrets()
    if kwargs['--c']:
        sec = kwargs['--c']
        while True:
            _user = input(f"Enter username for {sec}: ")
            if not _user:
                print('Invalid entry.  Try again.')
                continue
            else:
                break
        while True:
            _pass = getpass(f"Enter password for username: {_user}: ")
            if not _pass:
                print('Invalid entry.  Try again')
                continue
            else:
                break
        user = secret.make_secret(_user)
        passw = secret.make_secret(_pass)
        db.create_secrets(secret=sec, username=user, password=passw)
    elif kwargs['--r']:
        try:
            if not db.secret_exists(kwargs['--r']):
                raise ValueError("Secret does not exist in the database")
            _user = None
            _password = None
            results = db.retrieve_secrets(kwargs['--r'])
            for result in results:
                _user = result.username
                _password = result.password
            user = secret.make_public(_user)
            password = secret.make_public(_password)
            print(f"user={user}, password={password}")
        except ValueError as v:
            print(v)
    elif kwargs['--u']:
        try:
            user = None
            _user = None
            sec = kwargs['--u']
            if not db.secret_exists(secret=sec):
                raise ValueError("Secret does not exist in the database.  Use --c")
            user_up = strtobool(input(f"Update username? (default=N): "))
            if user_up:
                while True:
                    _user = input(f"Enter username for {sec}: ")
                    if not _user:
                        print('Invalid entry.  Try again.')
                        continue
                    else:
                        break
            while True:
                _pass = getpass(f"Enter updated password: ")
                if not _pass:
                    print('Invalid entry.  Try again.')
                    continue
                else:
                    break
            if user_up:
                user = secret.make_secret(secret=_user)
            passw = secret.make_secret(secret=_pass)
            db.update_secret(secret=sec, username=user, password=passw)
        except ValueError as t:
            print(t)
    elif kwargs['--d']:
        try:
            if not db.secret_exists(kwargs['--d']):
                raise ValueError("Secret does not exist in the database")
            db.delete_secret(kwargs['--d'])
        except ValueError as v:
            print(v)


if __name__ == "__main__":
    cmd_args = docopt(__doc__, version="Crypto 1.0")
    main(**cmd_args)
    logger.info('Done')
