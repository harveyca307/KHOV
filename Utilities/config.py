from configparser import ConfigParser
from baseLogger import application_path
from Utilities import DB, PySecrets


def get_config() -> dict:
    config = ConfigParser()
    config.read(f"{application_path}\config.ini")
    _base_url = config.get('base_url')
    _user = config.get('user')

    db = DB()
    results = db.retrieve_secrets(secret='khov')
    for result in results:
        _user = result.username
        _pass = result.password

    secret = PySecrets()
    username = secret.make_public(secret=_user)
    password = secret.make_public(secret=_pass)

    config = {
        'base_url': _base_url,
        'user': username,
        'password': password,
        'ssl': True
        'verify': True,
        'async_requests_mode': True
    }

