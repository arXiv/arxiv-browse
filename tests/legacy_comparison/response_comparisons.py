import requests

def compare_status(ng_url: str=None,
                   legacy_url: str=None,
                   ng_res: requests.Response =None,
                   legacy_res: requests.Response =None,
                   paperid: str=None):
    if ng_res.status_code ==200  and legacy_res.status_code == 200:
        return f'200 HTTP status for both {ng_url} and {legacy_url}'
    else:
        return f'HTTP status for {ng_url} was {ng_res.status_code} and for {legacy_url} was {legacy_res.status_code}'

