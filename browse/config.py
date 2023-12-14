"""Flask configuration.

Docstrings are from the `Flask configuration documentation
<http://flask.pocoo.org/docs/0.12/config/>`_.
"""
import os
from secrets import token_hex
import warnings

from typing import Optional, Dict, Any, List
import logging

from pydantic import SecretStr, PyObject, BaseSettings

log = logging.getLogger(__name__)


DEFAULT_DB = "sqlite:///../tests/data/browse.db"
TESTING_LATEXML_DB = 'sqlite:///../tests/data/latexmldb.db'


class Settings(BaseSettings):
    """Class for settings for arxiv-browse web app."""

    APP_VERSION: str = "0.3.4"
    """The application version """

    """
    Flask-S3 plugin settings.
    See `<https://flask-s3.readthedocs.io/en/latest/>`_.
    """
    FLASKS3_BUCKET_NAME: str = "some_bucket"
    FLASKS3_CDN_DOMAIN: str = "static.arxiv.org"
    FLASKS3_USE_HTTPS: bool = True
    FLASKS3_FORCE_MIMETYPE: bool = True
    FLASKS3_ACTIVE: bool = False

    SQLALCHEMY_DATABASE_URI: str = DEFAULT_DB
    """SQLALCHEMY_DATABASE_URI is pulled from
    BROWSE_SQLALCHEMY_DATABASE_URI. If it is not there the
    SQLALCHEMY_DATABASE_URI is checked. If that is not set, the
    default, the SQLITE test DB is used.
    """

    LATEXML_ENABLED: bool = False
    """Sets if LATEXML is enabled or not"""

    LATEXML_BUCKET: str = os.environ.get('LATEXML_BUCKET', 'latexml_arxiv_id_converted')

    LATEXML_BASE_URL: str = os.environ.get('LATEXML_BASE_URL')
    """Base GS bucket URL to find the HTML."""

    LATEXML_DB_USER: str = os.environ.get('LATEXML_DB_USER')
    """DB username for latexml DB."""

    LATEXML_DB_PASS: str = os.environ.get('LATEXML_DB_PASS')
    """DB password for latexml DB."""

    LATEXML_DB_NAME: str = os.environ.get('LATEXML_DB_NAME')
    """DB name for latexml DB."""

    LATEXML_INSTANCE_CONNECTION_NAME: str = ''
    """GCP instance connection name of managed DB.
    ex. arxiv-xyz:us-central1:my-special-db
    

    If this is set, a TLS protected GCP connection will be used to connect to
    the latexml db. See
    https://cloud.google.com/sql/docs/postgres/connect-connectors#python_1"""
    

    LATEXML_IP_TYPE: str = 'PUBLIC_IP'
    """If the GCP connection is public or private"""

    SQLALCHEMY_BINDS: Dict[str, Any] = {
        'latexml': f"postgresql+pg8000://{LATEXML_DB_USER}:{LATEXML_DB_PASS}@/{LATEXML_DB_NAME}?unix_sock=/cloudsql/{LATEXML_INSTANCE_CONNECTION_NAME}/.s.PGSQL.5432"
    }
    """ For the database tracking html conversion metadata """

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = False

    SQLALCHEMY_POOL_SIZE: Optional[int] = 10
    """SQLALCHEMY_POOL_SIZE is set from BROWSE_SQLALCHEMY_POOL_SIZE.
    Ignored under sqlite."""

    SQLALCHEMY_MAX_OVERFLOW: Optional[int] = 0
    """SQLALCHEMY_MAX_OVERFLOW is set from BROWSE_SQLALCHEMY_MAX_OVERFLOW.
    Ignored under sqlite."""

    BROWSE_DISABLE_DATABASE: bool = False
    """Disable DB queries even if other SQLAlchemy config are defined
    This, for example, could be used in conjunction with the
    `no-write` runlevel in the legacy infrastructure, which is a case
    where we know the DB is unavailable and thus intentionally bypass
    any DB access."""

    BROWSE_DAILY_STATS_PATH: str = "tests/data/daily_stats"
    """The classic home page uses this file to get the total paper count
    The file contains one line, with key "total_papers" and an integer, e.g.
    total_papers 1456755."""

    BROWSE_SITE_LABEL: str = "arXiv.org"

    BROWSE_ANALYTICS_ENABLED: bool = bool(int(os.environ.get("BROWSE_ANALYTICS_ENABLED", "0")))
    """Enable/disable web analytics, ie: Pendo, Piwik, geoip."""

    BROWSE_USER_BANNER_ENABLED: bool = bool(int(os.environ.get("BROWSE_USER_BANNER_ENABLED", "0")))
    """Enable/disable the user banner, the full width one, above the Cornell logo."""

    BROWSE_MINIMAL_BANNER_ENABLED: bool = bool(int(os.environ.get("BROWSE_MINIMAL_BANNER_ENABLED", "0")))
    """Enable/disable the banner to the right of the Cornell logo, before the donate button."""

    BROWSE_SPECIAL_MESSAGE_ENABLED: bool = bool(int(os.environ.get("BROWSE_SPECIAL_MESSAGE_ENABLED", "0")))
    """Enable/disable the cloud list item, in the arXiv News section, in home/special-message.html"""

    ############################## Services ##############################
    DOCUMENT_LISTING_SERVICE: PyObject = 'browse.services.listing.fs_listing'  # type: ignore
    """What implementation to use for the listing service.

    Accepted values are
    - `browse.services.listing.fs_listing`: Listing from legacy listing files. Needs to
      have DOCUMENT_LISTING_PATH set.
    - `browse.services.listing.db_listing`: Listing from DB. Slow and lacks data for
       before 2010.
    - `browse.services.listing.fake`: A totally fake set of listings for testing.
    """

    DOCUMENT_LISTING_PATH: str = 'tests/data/abs_files/ftp'
    """Path to get listing files from.

    This can start with gs:// to use Google Storage.
    Ex gs://arxiv-production-data/ftp."""


    DOCUMENT_ABSTRACT_SERVICE: PyObject = 'browse.services.documents.fs_docs'  # type: ignore
    """Implementation to use for abstracts.

    Accepted values are:
    - `browse.services.documents.fs_docs`: DocMetadata using .abs files. Used in
       produciton since 2019. If set DOCUMENT_LATEST_VERSIONS_PATH,
       DOCUMENT_ORIGNAL_VERSIONS_PATH and DOCUMENT_CACHE_PATH need to be set.
    - `browse.services.documents.db_docs`: DocMetadata using the database.
    """

    DOCUMENT_LATEST_VERSIONS_PATH: str = "tests/data/abs_files/ftp"
    """Paths to .abs and source files.

        This can start with gs:// to use Google Storage."""
    DOCUMENT_ORIGNAL_VERSIONS_PATH: str = "tests/data/abs_files/orig"
    """Paths to .abs and source files.

        This can start with gs:// to use Google Storage.
    """

    DOCUMENT_CACHE_PATH: str =  "tests/data/cache"
    """Path to cache directory"""

    PREV_NEXT_SERVICE: PyObject = 'browse.services.prevnext.fsprevnext'  # type: ignore
    """Implementation of the prev/next service used for those features on the abs page.

    Currently the only value is `browse.services.prevnext.fsprevnext` This uses
       DOCUMENT_LATEST_VERSIONS_PATH and DOCUMENT_ORIGNAL_VERSIONS_PATH.
    """


    DISSEMINATION_STORAGE_PREFIX: str = "./tests/data/abs_files/"
    """Storage prefix to use. Ex gs://arxiv-production-data

    If it is a GS bucket it must be just gs://{BUCKET_NAME} and not have
    any key parts. ex 'gs://arxiv-production-data'

    Use something like `/cache/` for a file system. Use something like
    `./testing/data/` for testing data. Must end with a /
    """

    ######################### End of Services ###########################

    SHOW_EMAIL_SECRET: SecretStr = SecretStr(token_hex(10))
    """Used in linking to /show-email.

    Set to be random by default to avoid leaking in misconfigured apps."""
    CLICKTHROUGH_SECRET: SecretStr = SecretStr(token_hex(10))
    """Used in linking to /ct.

    Set to be random by default to avoid leaking in misconfigured apps."""
    TRACKBACK_SECRET: SecretStr = SecretStr(token_hex(10))
    """Used in linking to trackbacks in /tb pages

    Set to be random by default to avoid leaking in misconfigured apps."""

    # Labs settings
    LABS_ENABLED: bool = True
    """arXiv Labs global enable/disable."""
    LABS_BIBEXPLORER_ENABLED: bool = True
    """arXiv Labs Bibliographic Explorer enable/disable."""
    LABS_CORE_RECOMMENDER_ENABLED: bool = False
    """CORE Recommender enabled/disabled."""

    # Auth settings These set settings of the arxiv-auth package.
    AUTH_SESSION_COOKIE_NAME: str = "ARXIVNG_SESSION_ID"
    AUTH_SESSION_COOKIE_DOMAIN: str = ".arxiv.org"
    AUTH_SESSION_COOKIE_SECURE: bool = True
    AUTH_UPDATED_SESSION_REF: bool = True

    CLASSIC_COOKIE_NAME: str = "tapir_session"
    CLASSIC_PERMANENT_COOKIE_NAME: str = "tapir_permanent"

    CLASSIC_SESSION_HASH: SecretStr = SecretStr(token_hex(10))
    SESSION_DURATION: int = 36000

    ARXIV_BUSINESS_TZ: str = 'US/Eastern'
    """
    Timezone of the arxiv business offices.
    """

    FS_TZ: str = "US/Eastern"
    """
    Timezone of the filesystems used for abs, src and other files.

    This should be stirng that can be used with `zoneinfo.ZoneInfo`.

    If this is at a cloud provider is likley to be "UTC". On Cornell VM's it is
    "US/Eastern".
    """

    """XXXXXXXXXXXXXXX Some flask specific configs XXXXXXXXXXXX"""

    TESTING: bool = True
    """enable/disable testing mode. Enable testing mode. Exceptions are
    propagated rather than handled by the the app’s error
    handlers. Extensions may also change their behavior to facilitate
    easier testing. You should enable this in your own tests."""

    TEMPLATES_AUTO_RELOAD: Optional[bool] = None
    """Enable template auto reload in flask.

    Whether to check for modifications of the template source and reload it
    automatically. By default the value is None which means that Flask checks
    original file only in debug mode.
    """


    SECRET_KEY: str = "qwert2345"

    SESSION_COOKIE_NAME: str = "arxiv_browse"

    SESSION_COOKIE_DOMAIN: Optional[str] = None
    """
    the domain for the session cookie. If this is not set, the cookie will be valid
    for all subdomains of SERVER_NAME.
    """

    SESSION_COOKIE_PATH: Optional[str] = None
    """
    the path for the session cookie. If this is not set the cookie will be valid
    for all of APPLICATION_ROOT or if that is not set for '/'.
    """

    SESSION_COOKIE_HTTPONLY: bool = True
    """
    controls if the cookie should be set with the httponly flag. Defaults to True.
    """

    SESSION_COOKIE_SECURE: bool = True
    """
    controls if the cookie should be set with the secure flag. Defaults to False.
    """

    PERMANENT_SESSION_LIFETIME: int = 3600
    """
    the lifetime of a permanent session as datetime.timedelta object. Starting with
    Flask 0.8 this can also be an integer representing seconds.
    """

    SESSION_REFRESH_EACH_REQUEST: bool = True
    """
    this flag controls how permanent sessions are refreshed. If set to True (which
    is the default) then the cookie is refreshed each request which automatically
    bumps the lifetime. If set to False a set-cookie header is only sent if the
    session is modified. Non permanent sessions are not affected by this.
    """

    USE_X_SENDFILE: bool = False
    """enable/disable x-sendfile"""

    LOGGER_NAME: str = "browse"
    """the name of the logger"""

    LOGGER_HANDLER_POLICY: str = "always"
    """
    the policy of the default logging handler. The default is 'always' which means
    that the default logging handler is always active. 'debug' will only activate
    logging in debug mode, 'production' will only log in production and 'never'
    disables it entirely.
    """

    SERVER_NAME: Optional[str] = None
    """
    the name and port number of the server. Required for subdomain support (e.g.:
    'myapp.dev:5000') Note that localhost does not support subdomains so setting
    this to "localhost" does not help. Setting a SERVER_NAME also by default
    enables URL generation without a request context but with an application
    context.

    If this is set and the Host header of a request does not match the SERVER_NAME,
    then Flask will respond with a 404. Test with
    curl http://127.0.0.1:5000/ -sv -H "Host: subdomain.arxiv.org"
    """

    APPLICATION_ROOT: Optional[str] = None
    """
    If the application does not occupy a whole domain or subdomain this can be set
    to the path where the application is configured to live. This is for session
    cookie as path value. If domains are used, this should be None.
    """

    MAX_CONTENT_LENGTH: Optional[int] = None
    """
    If set to a value in bytes, Flask will reject incoming requests with a content
    length greater than this by returning a 413 status code.
    """

    SEND_FILE_MAX_AGE_DEFAULT: int = 43200
    """
    Default cache control max age to use with send_static_file() (the default
    static file handler) and send_file(), as datetime.timedelta or as seconds.
    Override this value on a per-file basis using the get_send_file_max_age() hook
    on Flask or Blueprint, respectively. Defaults to 43200 (12 hours).
    """

    TRAP_HTTP_EXCEPTIONS: bool = True
    """
    If this is set to True Flask will not execute the error handlers of HTTP
    exceptions but instead treat the exception like any other and bubble it through
    the exception stack. This is helpful for hairy debugging situations where you
    have to find out where an HTTP exception is coming from.
    """

    TRAP_BAD_REQUEST_ERRORS: bool = True
    """
    Werkzeug's internal data structures that deal with request specific data will
    raise special key errors that are also bad request exceptions. Likewise many
    operations can implicitly fail with a BadRequest exception for consistency.
    Since it’s nice for debugging to know why exactly it failed this flag can be
    used to debug those situations. If this config is set to True you will get a
    regular traceback instead.
    """

    PREFERRED_URL_SCHEME: str = "http"
    """
    The URL scheme that should be used for URL generation if no URL scheme is
    available. This defaults to http.
    """

    JSON_AS_ASCII: bool = True
    """
    By default Flask serialize object to ascii-encoded JSON. If this is set to
    False Flask will not encode to ASCII and output strings as-is and return
    unicode strings. jsonify will automatically encode it in utf-8 then for
    transport for instance.
    """

    JSON_SORT_KEYS: bool = True
    """
    By default Flask will serialize JSON objects in a way that the keys are
    ordered. This is done in order to ensure that independent of the hash seed of
    the dictionary the return value will be consistent to not trash external HTTP
    caches. You can override the default behavior by changing this variable.
    This is not recommended but might give you a performance improvement on the
    cost of cacheability.
    """

    JSONIFY_PRETTYPRINT_REGULAR: bool = True
    """
    If this is set to True (the default) jsonify responses will be pretty printed
    if they are not requested by an XMLHttpRequest object (controlled by the
    X-Requested-With header).
    """

    JSONIFY_MIMETYPE: str = "application/json"
    """MIME type used for jsonify responses."""

    EXPLAIN_TEMPLATE_LOADING: bool = False
    """
    If this is enabled then every attempt to load a template will write an info
    message to the logger explaining the attempts to locate the template. This can
    be useful to figure out why templates cannot be found or wrong templates appear
    to be loaded.
    """

    class Config:
        """Additional pydantic config of these settings."""

        fields = {
            'SQLALCHEMY_DATABASE_URI': {
                'env': ['BROWSE_SQLALCHEMY_DATABASE_URI', 'CLASSIC_DATABASE_URI']
            }
        }

    def check(self) -> None:
        """A check and fix up of a settings object."""
        if 'sqlite' in self.SQLALCHEMY_DATABASE_URI:
            if not self.TESTING:
                log.warning(f"using SQLite DB at {self.SQLALCHEMY_DATABASE_URI}")
            self.SQLALCHEMY_MAX_OVERFLOW = None
            self.SQLALCHEMY_POOL_SIZE = None

        if (os.environ.get("FLASK_ENV", False) == "production"
                and "sqlite" in self.SQLALCHEMY_DATABASE_URI):
            warnings.warn(
                "Using sqlite in BROWSE_SQLALCHEMY_DATABASE_URI in production environment"
            )

        if self.DOCUMENT_ORIGNAL_VERSIONS_PATH.startswith("gs://") and \
           self.DOCUMENT_LATEST_VERSIONS_PATH.startswith("gs://"):
           self.FS_TZ = "UTC"
           log.warning("Switching FS_TZ to UTC since DOCUMENT_LATEST_VERSIONS_PATH "
                       "and DOCUMENT_ORIGINAL_VERSIONS_PATH are Google Storage")
           if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
               log.warning("GOOGLE_APPLICATION_CREDENTIALS is set")
           else:
               log.warning("GOOGLE_APPLICATION_CREDENTIALS is not set")

        if ("fs_docs" in str(type(self.DOCUMENT_ABSTRACT_SERVICE)) and
            "fs_listing" in str(type(self.DOCUMENT_LISTING_PATH)) and
            self.DOCUMENT_LATEST_VERSIONS_PATH != self.DOCUMENT_LISTING_PATH):
            log.warning(f"Unexpected: using FS listings and abs sevice but FS don't match. "
                        "latest abs at {self.DOCUMENT_LATEST_VERSIONS_PATH} "
                        f"but listings at {self.DOCUMENT_LISTING_PATH}")
