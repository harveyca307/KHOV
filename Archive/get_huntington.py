import asana
import asana.error as ae
import pandas as pd

from Utilities import DB, PySecrets
from baseLogger import logger

PROJECT_ID = '1203157790092137'
PORTFOLIO = '1203018768403493'

db = DB()
secrets = PySecrets()

_pat = None
results = db.retrieve_secrets(secret='pat')
for result in results:
    _user = result.username
    _pat = result.password

pat = secrets.make_public(secret=_pat)

client = asana.Client.access_token(pat)
client.LOG_ASANA_CHANGE_WARNINGS = False

try:
    # Look to see if portfolio exists
    result = client.portfolios.get_portfolio(PORTFOLIO)
    # Loop through Portfolio items to create list of projects
    ports = []
    for result in client.portfolios.get_items_for_portfolio(PORTFOLIO, opt_fields={'gid'}, opt_pretty=True):
        ports.append(result['gid'])
    # Check for Portfolio membership
    if PROJECT_ID not in ports:
        raise ValueError

    # Get Project and Associated Custom fields
    results = client.projects.get_project(PROJECT_ID, opt_fields="custom_fields", opt_pretty=True)
    lst = []
    for result in results['custom_fields']:
        gid = result.get('gid')
        name = result.get('name')
        opts = result.get('enum_options')
        if opts and name.strip().startswith('CIP'):
            for o in opts:
                lst.append([gid, name, o['gid'], o['color'], o['name']])
    df = pd.DataFrame(lst)
    df.columns = ['Custom Field GID', 'Custom Field Name', 'Option GID', 'Option Color', 'Option Value']
    df.to_csv('customs.csv', index=False)
    # fields = []
    # for result in results['custom_fields']:
    #     if result['name'].strip().startswith('CIP'):
    #         gid = result.get('gid')
    #         name = result.get('name')
    #         value = result.get('display_value')
    #         fields.append([gid, name, value])
    # df = pd.DataFrame(fields)
    # df.columns = ['GID', 'Name', 'Value']
    # logger.info(f"Fields retrieved: {df}")
    # df.to_csv('Huntington_Knolls_CustomFieldValues.csv', index=False)
except ae.ForbiddenError:
    logger.info(f"No access to {PROJECT_ID}")
except ae.NotFoundError:
    logger.info(f"{PROJECT_ID} does not exist")
except ValueError:
    logger.info(f"{PROJECT_ID} does not belong to Portfolio: {PORTFOLIO}")
