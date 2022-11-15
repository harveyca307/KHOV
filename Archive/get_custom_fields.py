import asana
from Utilities import DB, PySecrets
import pandas as pd
import numpy as np


db = DB()
secrets = PySecrets()
WORKSPACE = '35623093886266'

results = db.retrieve_secrets('pat')
for result in results:
    _user = result.username
    _pass = result.password

username = secrets.make_public(secret=_user)
pat = secrets.make_public(secret=_pass)

client = asana.Client.access_token(pat)
client.LOG_ASANA_CHANGE_WARNINGS = False

result = client.custom_fields.get_custom_fields_for_workspace(WORKSPACE, opt_fields={'gid', 'name'},
                                                              opt_pretty=True)
df = pd.json_normalize(result)
df['name'].replace('', np.nan, inplace=True)
df.dropna(subset='name', inplace=True)
df.to_csv('custom_fields.csv', index=False)
