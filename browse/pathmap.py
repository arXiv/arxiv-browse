# type: ignore
"""Makes GCP path map string.

For use with gcloud compute url-maps add-path-matcher

See https://cloud.google.com/load-balancing/docs/url-map
"""

import sys

from browse.factory import create_web_app


backend_service = sys.argv[1]

app = create_web_app()


def mappingline(rule):
    hasParam = '<' in rule.rule
    if hasParam:
        path = rule.rule.split('<')[0] + "*"
    else:
        path = rule.rule

    return f"{path}={backend_service}"


with app.app_context():
    lines = [mappingline(path) for path in app.url_map.iter_rules()]
    print(','.join(lines))
