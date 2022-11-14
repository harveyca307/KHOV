import asana
from Utilities import DB, PySecrets
import pandas as pd

db = DB()
secrets = PySecrets()
WORKSPACE = '35623093886266'
PROJECT = "1203157790092145"

creds = db.retrieve_secrets(secret='pat')
for entry in creds:
    _user = entry.username
    _pass = entry.password

pat = secrets.make_public(secret=_pass)

client = asana.Client.access_token(pat)
client.LOG_ASANA_CHANGE_WARNINGS = False

results = client.tasks.get_tasks(project=PROJECT, opt_fields={'gid', 'name', 'due_on', 'custom_fields'},
                                 opt_pretty=True)

tasks = list()
for result in results:
    for cf in result['custom_fields']:
        if cf['name'].startswith("CIP"):
            tasks.append([PROJECT, result['gid'],
                          result['name'],
                          result['due_on'],
                          cf['gid'],
                          cf['name'],
                          cf['display_value']])
df = pd.DataFrame(tasks)
df.columns = ['Project GID',
              'Task GID',
              'Task Name',
              'Due On',
              'Custom Field GID',
              'Custom Field Name',
              'Custom Field Value']
df.to_csv('Warren_task.csv', index=False)
