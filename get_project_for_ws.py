import asana
from Utilities import DB, PySecrets
import pandas as pd

db = DB()
secrets = PySecrets()
WORKSPACE = '35623093886266'

creds = db.retrieve_secrets(secret='pat')
for entry in creds:
    _user = entry.username
    _pass = entry.password

pat = secrets.make_public(secret=_pass)

client = asana.Client.access_token(pat)
client.LOG_ASANA_CHANGE_WARNINGS = False

results = client.projects.get_projects({'workspace': WORKSPACE}, opt_pretty=True)

for result in results:
    print(result)
