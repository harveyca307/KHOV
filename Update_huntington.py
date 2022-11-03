import asana
import asana.error as ae

from Utilities import DB, PySecrets
from baseLogger import logger

PROJECT_ID = '1203157790092137'

db = DB()
secrets = PySecrets()

_pat = None
entries = db.retrieve_secrets(secret='pat')
for entry in entries:
    _pat = entry.password

pat = secrets.make_public(secret=_pat)

client = asana.Client.access_token(pat)
client.LOG_ASANA_CHANGE_WARNINGS = False

try:
    client.projects.update_project(PROJECT_ID, {"custom_fields": {"1203191009110006": "1203191009110009",
                                                                  "1203064325052098": "1203064325052099",
                                                                  "1203141614850471": "30 Market"}},
                                   opt_pretyy=True)
except ae.AsanaError as e:
    print(e)
