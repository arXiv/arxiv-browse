"""Flask configuration.

Docstrings are from the `Flask configuration documentation
<http://flask.pocoo.org/docs/0.12/config/>`_.
"""
import os
import warnings
import dateutil.parser
from datetime import datetime, timedelta

APP_VERSION = '0.2.8'
"""The application version """

ON = 'yes'
OFF = 'no'

DEBUG = os.environ.get('DEBUG') == ON
"""enable/disable debug mode"""

TESTING = os.environ.get('TESTING') == ON
"""enable/disable testing mode"""

PROPAGATE_EXCEPTIONS = \
    True if os.environ.get('PROPAGATE_EXCEPTIONS') == ON else None
"""
explicitly enable or disable the propagation of exceptions. If not set or
explicitly set to None this is implicitly true if either TESTING or DEBUG is
true.
"""

PRESERVE_CONTEXT_ON_EXCEPTION = \
    True if os.environ.get('PRESERVE_CONTEXT_ON_EXCEPTION') == ON else None
"""
By default if the application is in debug mode the request context is not
popped on exceptions to enable debuggers to introspect the data. This can be
disabled by this key. You can also use this setting to force-enable it for non
debug execution which might be useful to debug production applications (but
also very risky).
"""

SECRET_KEY = os.environ.get('SECRET_KEY', 'qwert2345')
"""
the secret key
"""

SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'arxiv_browse')
"""
the name of the session cookie
"""

SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)
"""
the domain for the session cookie. If this is not set, the cookie will be valid
for all subdomains of SERVER_NAME.
"""

SESSION_COOKIE_PATH = os.environ.get('SESSION_COOKIE_PATH', None)
"""
the path for the session cookie. If this is not set the cookie will be valid
for all of APPLICATION_ROOT or if that is not set for '/'.
"""

SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY') != OFF
"""
controls if the cookie should be set with the httponly flag. Defaults to True.
"""

SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE') == ON
"""
controls if the cookie should be set with the secure flag. Defaults to False.
"""

PERMANENT_SESSION_LIFETIME = \
    int(os.environ.get('PERMANENT_SESSION_LIFETIME', '3600'))
"""
the lifetime of a permanent session as datetime.timedelta object. Starting with
Flask 0.8 this can also be an integer representing seconds.
"""

SESSION_REFRESH_EACH_REQUEST = \
    os.environ.get('SESSION_REFRESH_EACH_REQUEST') != OFF
"""
this flag controls how permanent sessions are refreshed. If set to True (which
is the default) then the cookie is refreshed each request which automatically
bumps the lifetime. If set to False a set-cookie header is only sent if the
session is modified. Non permanent sessions are not affected by this.
"""

USE_X_SENDFILE = os.environ.get('USE_X_SENDFILE') == ON
"""
enable/disable x-sendfile
"""

LOGGER_NAME = os.environ.get('LOGGER_NAME', 'browse')
"""
the name of the logger
"""

LOGGER_HANDLER_POLICY = os.environ.get('LOGGER_HANDLER_POLICY', 'always')
"""
the policy of the default logging handler. The default is 'always' which means
that the default logging handler is always active. 'debug' will only activate
logging in debug mode, 'production' will only log in production and 'never'
disables it entirely.
"""

SERVER_NAME = os.environ.get('BROWSE_SERVER_NAME', None)
"""
the name and port number of the server. Required for subdomain support (e.g.:
'myapp.dev:5000') Note that localhost does not support subdomains so setting
this to "localhost" does not help. Setting a SERVER_NAME also by default
enables URL generation without a request context but with an application
context.
"""

APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', None)
"""
If the application does not occupy a whole domain or subdomain this can be set
to the path where the application is configured to live. This is for session
cookie as path value. If domains are used, this should be None.
"""

MAX_CONTENT_LENGTH = os.environ.get('MAX_CONTENT_LENGTH', None)
"""
If set to a value in bytes, Flask will reject incoming requests with a content
length greater than this by returning a 413 status code.
"""

SEND_FILE_MAX_AGE_DEFAULT = int(
    os.environ.get('SEND_FILE_MAX_AGE_DEFAULT', 43200))
"""
Default cache control max age to use with send_static_file() (the default
static file handler) and send_file(), as datetime.timedelta or as seconds.
Override this value on a per-file basis using the get_send_file_max_age() hook
on Flask or Blueprint, respectively. Defaults to 43200 (12 hours).
"""

TRAP_HTTP_EXCEPTIONS = os.environ.get('TRAP_HTTP_EXCEPTIONS') == ON
"""
If this is set to True Flask will not execute the error handlers of HTTP
exceptions but instead treat the exception like any other and bubble it through
the exception stack. This is helpful for hairy debugging situations where you
have to find out where an HTTP exception is coming from.
"""

TRAP_BAD_REQUEST_ERRORS = os.environ.get('TRAP_BAD_REQUEST_ERRORS') == ON
"""
Werkzeug's internal data structures that deal with request specific data will
raise special key errors that are also bad request exceptions. Likewise many
operations can implicitly fail with a BadRequest exception for consistency.
Since it’s nice for debugging to know why exactly it failed this flag can be
used to debug those situations. If this config is set to True you will get a
regular traceback instead.
"""

PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
"""
The URL scheme that should be used for URL generation if no URL scheme is
available. This defaults to http.
"""

JSON_AS_ASCII = os.environ.get('JSON_AS_ASCII') == ON
"""
By default Flask serialize object to ascii-encoded JSON. If this is set to
False Flask will not encode to ASCII and output strings as-is and return
unicode strings. jsonify will automatically encode it in utf-8 then for
transport for instance.
"""

JSON_SORT_KEYS = os.environ.get('JSON_AS_ASCII') != OFF
"""
By default Flask will serialize JSON objects in a way that the keys are
ordered. This is done in order to ensure that independent of the hash seed of
the dictionary the return value will be consistent to not trash external HTTP
caches. You can override the default behavior by changing this variable.
This is not recommended but might give you a performance improvement on the
cost of cacheability.
"""

JSONIFY_PRETTYPRINT_REGULAR = os.environ.get('JSON_AS_ASCII') != OFF
"""
If this is set to True (the default) jsonify responses will be pretty printed
if they are not requested by an XMLHttpRequest object (controlled by the
X-Requested-With header).
"""

JSONIFY_MIMETYPE = os.environ.get('JSONIFY_MIMETYPE', 'application/json')
"""
MIME type used for jsonify responses.
"""

TEMPLATES_AUTO_RELOAD = os.environ.get('TEMPLATES_AUTO_RELOAD') == ON
"""
Whether to check for modifications of the template source and reload it
automatically. By default the value is None which means that Flask checks
original file only in debug mode.
"""

EXPLAIN_TEMPLATE_LOADING = os.environ.get('EXPLAIN_TEMPLATE_LOADING') == OFF
"""
If this is enabled then every attempt to load a template will write an info
message to the logger explaining the attempts to locate the template. This can
be useful to figure out why templates cannot be found or wrong templates appear
to be loaded.
"""

"""
Flask-S3 plugin settings.
See `<https://flask-s3.readthedocs.io/en/latest/>`_.
"""
FLASKS3_BUCKET_NAME = os.environ.get('FLASKS3_BUCKET_NAME', 'some_bucket')
FLASKS3_CDN_DOMAIN = os.environ.get('FLASKS3_CDN_DOMAIN', 'static.arxiv.org')
FLASKS3_USE_HTTPS = bool(int(os.environ.get('FLASKS3_USE_HTTPS', 1)))
FLASKS3_FORCE_MIMETYPE = bool(int(os.environ.get('FLASKS3_FORCE_MIMETYPE', '1')))
FLASKS3_ACTIVE = bool(int(os.environ.get('FLASKS3_ACTIVE', '0')))

# SQLAlchemy configuration
# For mysql: 'mysql://user:pass@localhost/dbname'
SQLALCHEMY_DATABASE_URI = os.environ.get('BROWSE_SQLALCHEMY_DATABASE_URI',
                                         os.environ.get('SQLALCHEMY_DATABASE_URI',
                                                        'sqlite:///../tests/data/browse.db'))
"""SQLALCHEMY_DATABASE_URI is pulled from
BROWSE_SQLALCHEMY_DATABASE_URI. If it is not there the
SQLALCHEMY_DATABASE_URI is checked. If that is not set, the SQLITE
test DB is used.

If neither of those is set and TESTING is the string 'yes', then a
SQLITE test DB is used.
"""

if os.environ.get('FLASK_ENV', False) == 'production' \
   and 'sqlite' in SQLALCHEMY_DATABASE_URI:
    warnings.warn("Using sqlite in BROWSE_SQLALCHEMY_DATABASE_URI in production environment")

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False
SQLALCHEMY_RECORD_QUERIES = False

SQLALCHEMY_POOL_SIZE = int(os.environ.get('BROWSE_SQLALCHEMY_POOL_SIZE', '10'))
"""SQLALCHEMY_POOL_SIZE is set from BROWSE_SQLALCHEMY_POOL_SIZE.

Ignored under sqlite."""

SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('BROWSE_SQLALCHEMY_MAX_OVERFLOW', '0'))
"""SQLALCHEMY_MAX_OVERFLOW is set from BROWSE_SQLALCHEMY_MAX_OVERFLOW.

Ignored under sqlite."""

# SQLALCHEMY_POOL_SIZE and SQLALCHEMY_MAX_OVERFLOW will not work with sqlite
if 'sqlite' in SQLALCHEMY_DATABASE_URI:
    SQLALCHEMY_POOL_SIZE = None
    SQLALCHEMY_MAX_OVERFLOW = None

BROWSE_DAILY_STATS_PATH = os.environ.get(
    'BROWSE_DAILY_STATS_PATH', 'tests/data/daily_stats')
"""The classic home page uses this file to get the total paper count
The file contains one line, with key "total_papers" and an integer, e.g.
total_papers 1456755."""

BROWSE_DISABLE_DATABASE = os.environ.get('BROWSE_DISABLE_DATABASE', False)
"""Disable DB queries even if other SQLAlchemy config are defined
This, for example, could be used in conjunction with the `no-write` runlevel
in the legacy infrastructure, which is a case where we know the DB is
unavailable and thus intentionally bypass any DB access."""

BROWSE_SITE_LABEL = os.environ.get('BROWSE_SITE_LABEL', 'arXiv.org')
BROWSE_SITE_HOST = os.environ.get('BROWSE_SITE_HOST', None)
"""This is similar to, but decoupled from SERVER_NAME."""

BROWSE_ANALYTICS_ENABLED = os.environ.get('BROWSE_ANALYTICS_ENABLED', False)
"""Enable/disable Matomo web analytics."""
BROWSE_ANALYTICS_BASE_URL = os.environ.get('BROWSE_ANALYTICS_BASE_URL',
                                           'https://webstats.arxiv.org/')
"""Base URL for tracker. Should include trailing slash."""
BROWSE_ANALYTICS_COOKIE_DOMAIN = \
    os.environ.get('BROWSE_ANALYTICS_COOKIE_DOMAIN', '*.arxiv.org')
"""Cookie domain for tracker."""
BROWSE_ANALYTICS_SITE_ID = os.environ.get('BROWSE_ANALYTICS_SITE_ID', '1')
"""Tracker site ID."""

BROWSE_USER_BANNER_ENABLED = bool(int(os.environ.get(
    'BROWSE_USER_BANNER_ENABLED', '0')))
"""Enable/disable user banner."""
try:
    BROWSE_USER_BANNER_START_DATE = dateutil.parser.parse(
        os.environ.get('BROWSE_USER_BANNER_START_DATE')
    ).replace(hour=0, minute=0, second=0)
except Exception:
    if BROWSE_USER_BANNER_ENABLED:
        warnings.warn("Bad value for BROWSE_USER_BANNER_START_DATE")
    BROWSE_USER_BANNER_START_DATE = datetime.now() - timedelta(days=1)

try:
    BROWSE_USER_BANNER_END_DATE = dateutil.parser.parse(
        os.environ.get('BROWSE_USER_BANNER_END_DATE')
    ).replace(hour=23, minute=59, second=59)
except Exception:
    if BROWSE_USER_BANNER_ENABLED:
        warnings.warn("Bad value for BROWSE_USER_BANNER_END_DATE")
    BROWSE_USER_BANNER_END_DATE = datetime.now() + timedelta(days=1)

DOCUMENT_LATEST_VERSIONS_PATH = os.environ.get(
    'DOCUMENT_LATEST_VERSIONS_PATH', 'tests/data/abs_files/ftp')
"""Paths to .abs and source files."""

DOCUMENT_ORIGNAL_VERSIONS_PATH = os.environ.get(
    'DOCUMENT_ORIGNAL_VERSIONS_PATH', 'tests/data/abs_files/orig')
"""Paths to .abs and source files."""

DOCUMENT_CACHE_PATH = os.environ.get(
    'DOCUMENT_CACHE_PATH', 'tests/data/cache')
"""Path to cache directory"""

SHOW_EMAIL_SECRET = os.environ.get('SHOW_EMAIL_SECRET', 'foo')
"""Used in linking to /show-email."""

CLICKTHROUGH_SECRET = os.environ.get('CLICKTHROUGH_SECRET', 'bar')
"""Used in linking to /ct."""

TRACKBACK_SECRET = os.environ.get('TRACKBACK_SECRET', 'baz')
"""Used in linking to trackbacks in /tb pages."""

LABS_BIBEXPLORER_ENABLED = os.environ.get('LABS_BIBEXPLORER_ENABLED', True)
"""arXiv Labs bibex enabled/disabled."""

# Auth settings
AUTH_SESSION_COOKIE_NAME = 'ARXIVNG_SESSION_ID'
AUTH_SESSION_COOKIE_DOMAIN = os.environ.get(
    'AUTH_SESSION_COOKIE_DOMAIN', '.arxiv.org')
AUTH_SESSION_COOKIE_SECURE = bool(
    int(os.environ.get('AUTH_SESSION_COOKIE_SECURE', '1')))
AUTH_UPDATED_SESSION_REF = True

CLASSIC_COOKIE_NAME = os.environ.get('CLASSIC_COOKIE_NAME', 'tapir_session')
CLASSIC_PERMANENT_COOKIE_NAME = os.environ.get(
    'CLASSIC_PERMANENT_COOKIE_NAME',
    'tapir_permanent'
)
CLASSIC_TRACKING_COOKIE = os.environ.get('CLASSIC_TRACKING_COOKIE', 'browser')
CLASSIC_DATABASE_URI = os.environ.get('CLASSIC_DATABASE_URI', os.environ.get(
    'BROWSE_SQLALCHEMY_DATABASE_URI', default=None))
"""If not set, legacy database integrations for auth will not be available."""
if not CLASSIC_DATABASE_URI:
    warnings.warn("No value set for CLASSIC_DATABASE_URI")
elif 'sqlite' in CLASSIC_DATABASE_URI:
    warnings.warn("Using sqlite in CLASSIC_DATABASE_URI")

CLASSIC_SESSION_HASH = os.environ.get('CLASSIC_SESSION_HASH', 'foosecret')
SESSION_DURATION = os.environ.get(
    'SESSION_DURATION',
    '36000'
)

URLS = [
    ('ui.login', '/login', os.environ.get('SERVER_NAME', 'arxiv.org'))
    # This is a temporary workaround for ARXIVNG-2063
]
"""External URLs."""
