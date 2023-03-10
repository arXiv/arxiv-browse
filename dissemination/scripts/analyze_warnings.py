"""Compare to legacy, the warnings in a json file as downloaded from
GCP log explorer.

Run as

   python scripts/analyze_warnings.py 404_log_export_from_GCP.json

If you take the GCP log explorer and get all the WARNING log lines from the
cloud run service, you can run them though this script.

It will give a summary by status with examples.

Then it will take all the 404 responses and try to get the from
export.arxiv.org. The response from GCP will be compared with the ones
from export to let you know if they are real 404s, missing from the
sync, withdrawn (aka no_author_source) or unavailable.

"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
import requests

print(f"* Analysis of {sys.argv[1]}")
with open(sys.argv[1]) as fh:
    data = json.load(fh)

print(f"Number of rows: {len(data)}")

bystatus = defaultdict(list)
for row in data:
    bystatus[row['httpRequest']['status']].append(row)

for key in bystatus:
    print(f"{key}: {len(bystatus[key])} responses")

for key in bystatus:
    print(f"Examples of {key} responses")
    for row in bystatus[key][0:3]:
        print(" - "+ row['httpRequest']['requestUrl'])

ENSURE_UA = 'periodic-rebuild'

print("Checking if 404s exist on legacy")
session = requests.Session()
session.headers = headers = {
    'User-Agent': ENSURE_UA,
    'Accept': '*/*'
}

responses = {}
for row in bystatus[404]:
    url = row['httpRequest']['requestUrl'].replace('download.', 'export.')
    resp = session.get(url, allow_redirects=True)
    is_pdf = bool('pdf' in resp.headers['content-type'])
    unavailable = bool('PDF unavailable for' in resp.text)
    no_author_source = bool('The author has provided no source' in resp.text)
    print(f"{url}: {resp.status_code} is_pdf: {is_pdf} content-type: {resp.headers['content-type']} unavailable: {unavailable}")

    responses[url] = dict(status_code = int(resp.status_code),
                          is_pdf = is_pdf,
                          unavailable = unavailable,
                          no_author_source= no_author_source,
                          )



with open(Path('404_analysis.json'),'w') as fh:
    json.dump(responses, fh, indent=2)


non200 = [item for item in responses.values() if item['status_code'] != 200]
unavailable = [item for item in responses.values() if item['status_code'] == 200 and item['unavailable']]

print(f"resonse from legacy was non-200: {len(non200)}")
print(f"resonse from legacy was 200 but pdf was unavailable: {len(unavailable)}")


print("DONE\n")
