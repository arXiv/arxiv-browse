from typing import Dict, Tuple, Any
from werkzeug.datastructures import ImmutableMultiDict

from flask import request
import re

from datetime import timedelta

COOKIE_NAME = 'user-OpenURL'
COOKIE_PATH = '/'
COOKIE_EXPIRY_YEARS = 10

def _get_form_items (form_items: ImmutableMultiDict) -> Dict[str, str]:
    # Raise error if form_items[...] is not there
    res = {}

    res['baseURL'] = _remove_whitespace(form_items['baseURL'])
    res['icon'] = _remove_whitespace(form_items['icon'])
    if res['icon'] == f'{res["baseURL"]}/sfx.gif':
        del res['icon']
    if not res['baseURL']:
        del res['baseURL']
    res['newWindow'] = form_items['newWindow']
    res['version'] = form_items['version']
    if res['version'] == 'both':
        del res['version']
    res['Action'] = form_items['Action']

    return res

def _remove_whitespace (s: str) -> str:
    return ''.join(s.split()) # Remove all whitespace

def _build_cookie (values: Dict[str, str]) -> str: 
    return '&'.join([f'{k}={v}' for k,v in values.items()])

def _parse_cookie (value: str) -> Dict[str, str]:
    return dict([tuple(pair.split('=')) for pair in value.split('&')])

def _get_display_values ():
    default_vals = {'cookieExists': False,
                    'baseURL': '[no OpenURL linking service]',
                    'icon': '[not set]', 
                    'newWindow': '[not set]', 
                    'version': 'both',
                    'expiry': COOKIE_EXPIRY_YEARS}
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie is not None:
        default_vals['cookieExists'] = True
        cookie_vals = _parse_cookie(cookie)
        return {k: cookie_vals.get(k) or v for k, v in default_vals.items()}
    return default_vals

def make_openurl_cookie () -> Dict[str, str]:
    values = _get_form_items(request.form)        

    if values['Action'] == 'Delete cookie':
        return {
            'key': COOKIE_NAME,
            'path': COOKIE_PATH,
            'expires': 0
        }
    
    return {
        'key': COOKIE_NAME,
        'path': COOKIE_PATH,
        'value': _build_cookie(values),
        'max_age': timedelta(days=(COOKIE_EXPIRY_YEARS * 365))
    }

def get_openurl_page () -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    return _get_display_values(), 200, {}

    


