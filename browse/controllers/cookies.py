"""Handle requests to set cookies"""

import re
from typing import Any, Dict, List, Optional, Tuple
import copy

import flask
from flask import url_for, request, make_response
from werkzeug.exceptions import InternalServerError

from arxiv import status

cookies_config = [
    {'id': 'ps',
     'name': 'xxx-ps-defaults',
     'label': 'Select preferred download format:',
     'options': [
         ['default', 'PostScript (600 dpi), PDF (default)', 1],
         ['dpi=300%26font=bitmapped', 'PostScript (300 dpi)', 0],
         ['fname=cm%26font=TypeI', 'PostScript (Type I cm)', 0],
         ['pdf', 'PDF', 0],
         ['dvi', 'DVI', 0],
         ['src', 'Source', 0]
     ],
     },
    {'id': 'mirror',
     'name': 'xxx-mirror',
     'label': 'Select download site:',
     'options': [['default', 'always local site (default)', 1], ]
     },
    {'id': 'mj',
     'name': 'arxiv_mathjax',
     'label': 'Select MathJax configuration: ',
     'options': [['enabled',  'enabled', 1],
                 ['disabled', 'disabled', 0]]
     }
]


# TODO get mirrors from somewhere
# foreach my $k (keys %map_domain) {
#  foreach my $m (split(/\|/, $map_domain{$k})) {
#    $cookie_description{mirror}{$m} = $m;
#  }
# }


# TODO implement debug parameter

def get_cookies_page(is_debug: bool) -> Any:
    """Render the cookies page.

    Parameters
    ----------

    Returns
    -------
    dict
        Search result response data.
    int
        HTTP status code.
    dict
        Headers to add to the response.

    Raises
    ------
    :class:`.InternalServerError`
        Raised when there was an unexpected problem executing the query.
    """
    debug = {'debug': '1'} if is_debug else {}
    response_data = {
        'form_url': url_for('browse.cookies', set='set', **debug),
        'cookies_config': selected_options_from_request(copy.deepcopy(cookies_config))
    }
    response_headers = {'Expires': '0',
                        'Pragma': 'no-cache'}
    return response_data, status.HTTP_200_OK, response_headers


def selected_options_from_request(configs: List[Dict[str, Any]]) -> Dict[str, str]:
    """Sets the selected value on the options for the request cookies."""
    cookies = request.cookies
    for cc in configs:
        request_value = cookies.get(cc['name'], None)
        matching_opt = next((opt for opt in cc['options']
                             if opt[0] == request_value), None)
        if(matching_opt is not None):
            matching_opt[2] = 1
    return configs


def cookies_to_set(request) -> List[Tuple[str, str]]:
    """Get cookies from the form and return them as a list of tuples."""
    cts = []
    for (id, value) in request.form.items():
        matching_conf = next(
            (conf for conf in cookies_config if conf['id'] == id), None)
        if matching_conf is not None:
            cts.append((matching_conf['name'], value))
    return cts
