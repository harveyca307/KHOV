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

results = client.portfolios.get_items_for_portfolio('1203018768403499', opt_fields={'gid'}, opt_pretty=True)

df = pd.json_normalize(results)
df.to_csv('portfolio.csv.', index=False)
