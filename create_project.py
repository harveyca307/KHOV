"""
Usage:
    create_project <file>
    create_project (-h | --version)

Arguments:
    <file>      YAML Instruction File

Options:
    -h          Show this screen
    --version   Show Version Information
"""

import asana
import yaml
from TM1py import TM1Service
from TM1py.Exceptions import TM1pyException
from docopt import docopt

from Utilities import DB, PySecrets
from baseLogger import logger

APP_NAME = "PyCreateProject"
APP_VERSION = "1.0"


def get_config(_dict: dict) -> dict:
    _user = ''
    _password = ''
    db = DB()
    secrets = PySecrets()
    base_url = _dict['Config']['base_url']
    instance = _dict['Config']['instance']
    results = db.retrieve_secrets(secret=instance)
    for result in results:
        _user = result.username
        _password = result.password
    user = secrets.make_public(secret=_user)
    password = secrets.make_public(secret=_password)
    config = {
        'base_url': base_url,
        'user': user,
        'password': password,
        'ssl': True,
        'verify': True,
        'async_requests_mode': True,
        'session_context': APP_NAME
    }
    return config


def create_project(_dict: dict, config: dict) -> None:
    _pat = ''
    db = DB()
    secrets = PySecrets()
    results = db.retrieve_secrets(secret='pat')
    for result in results:
        _user = result.username
        _pat = result.password
    pat = secrets.make_public(secret=_pat)
    _name = _dict['Project']['name']
    _workspace = _dict['Project']['workspace_id']
    _team = _dict['Project']['team_id']
    _template = _dict['Project']['project_id']
    _tm1_obj = _dict['Project']['tm1_object']
    _prj = {'name': _name, 'workspace': _workspace, 'team': _team, 'public': True}
    client = asana.Client.access_token(pat)
    client.LOG_ASANA_CHANGE_WARNINGS = False
    logger.info(f"Creating {_prj} in Asana")
    result = client.projects.duplicate_project(_template, _prj, opt_pretty=True)
    cellset = {(_tm1_obj, 'CIP Asana Project GID'): result['new_project']['gid']}
    try:
        with TM1Service(**config) as tm1:
            logger.info(f"Updating TM1 Attributes for {_name}, GID: {result['new_project']['gid']}")
            tm1.cubes.cells.write_values('}ElementAttributes_Org', cellset)
    except TM1pyException as e:
        logger.info(e)


if __name__ == "__main__":
    cmd_args = docopt(__doc__, version=f"{APP_NAME}, Version: {APP_VERSION}")
    logger.info(f"Starting process: {APP_NAME}.  Arguments received from CMD: {cmd_args}")
    _file = cmd_args.get("<file>")
    stream = open(_file, 'r')
    _yml = yaml.load(stream, Loader=yaml.FullLoader)
    _config = get_config(_dict=_yml)
    create_project(_dict=_yml, config=_config)
    stream.close()
    logger.info("Process complete")
