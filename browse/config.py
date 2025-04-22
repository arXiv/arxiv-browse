"""Flask configuration."""
import os
from secrets import token_hex
import warnings

from typing import Optional
import logging

import arxiv.config as arxiv_base
from pydantic import SecretStr, PyObject

log = logging.getLogger(__name__)


DAY = 60 * 60 * 24 # one day of seconds

class Settings(arxiv_base.Settings):
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

    LATEXML_ENABLED: bool = False
    """Sets if LATEXML is enabled or not"""

    LATEXML_BASE_URL: str = ''
    """Base GS bucket URL to find the HTML."""

    LATEXML_BUCKET: str = './test/data'

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_RECORD_QUERIES: bool = False

    SQLALCHEMY_POOL_SIZE: Optional[int] = 10
    """Ignored under sqlite."""

    SQLALCHEMY_MAX_OVERFLOW: Optional[int] = 0
    """Ignored under sqlite."""

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

    ABS_CACHE_MAX_AGE: int = 365 * DAY
    """Abs page cache in seconds.

    The cache-control: max-age to set for /abs pages. Max for this in the RFC is one year."""

    FILE_CACHE_MAX_AGE: int = 365 * DAY
    """PDF, src, e-print cache in seconds.

    The cache-control: max-age to set for /pdf /src /e-print /html pages. Max
    for this in the RFC is one year.
    """
    """"========================= Services ========================="""
    DOCUMENT_LISTING_SERVICE: PyObject = 'browse.services.listing.db_listing'  # type: ignore
    """What implementation to use for the listing service.

    Accepted values are
    - `browse.services.listing.fs_listing`: Listing from legacy listing files. Needs to
      have DOCUMENT_LISTING_PATH set.
    - `browse.services.listing.db_listing`: Listing from legacy listing files with new bits from database. Needs to
      have DOCUMENT_LISTING_PATH set.
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
       production since 2019. If set ABS_PATH_ROOT needs to be set.
    - `browse.services.documents.db_docs`: DocMetadata using the database.
    """

    ABS_PATH_ROOT: str = "tests/data/abs_files/"
    """Paths to .abs files.

    This can start with gs:// to use Google Storage.
    """

    SOURCE_STORAGE_PREFIX: str = "tests/data/abs_files/"
    """Paths to source files.
    
    This can start with gs:// to use Google Storage. Ex
    `gs://arxiv-production-data`. Use with `/data/` for a file system.
    """

    DISSEMINATION_STORAGE_PREFIX: str = "./tests/data/abs_files/"
    """Storage prefix to use. Ex gs://arxiv-production-data

    If it is a GS bucket it must be just gs://{BUCKET_NAME} and not have
    any key parts. ex 'gs://arxiv-production-data'

    Use something like `/cache/` for a file system. Use something like
    `./testing/data/` for testing data. Must end with a /
    """

    REASONS_FILE_PATH: str = "DEFAULT"
    """Full path to `reasons.json` file.

    This can be a gs object like `gs://arxiv-production-data/reasons.json`.
    It can also be a local file like `tests/data/reasons.json`.
    This can be the special value "DEFAULT" which will look for `DISSEMINATION_STORAGE_PREFIX/reasons.json`."""

    GENPDF_API_URL: str = ""
    """URL of the genpdf API. https://genpdf-api.arxiv.org"""

    GENPDF_SERVICE_URL: str = ""
    """URL of the genpdf service URL. This is the original service URL on the cloud run."""

    GENPDF_API_TIMEOUT: int = 590
    """Time ouf for the genpdf API access"""

    GENPDF_API_STORAGE_PREFIX: str = "./tests/data/abs_files"
    """Where genpdf stores the PDFs. It is likely the local file system does not work here but
    it is plausible to match the gs bucket with local file system, esp. for testing.
    For production, it would be:
    GENPDF_API_STORAGE_PREFIX: str = "gs://arxiv-production-data"
    """

    ARXIV_LOG_DATA_INCONSTANCY_ERRORS: bool = True
    """It to log error messages during a PDF or other data request when a paper's metadata does
    not match what is on the data filesystem. Ex. a paper version is source type PDF-only
    but there is no src PDF file."""

    """========================= End of Services ========================="""

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

    FS_TZ: str = "US/Eastern"
    """
    Timezone of the filesystems used for abs, src and other files.

    This should be string that can be used with `zoneinfo.ZoneInfo`.

    If this is at a cloud provider is likely to be "UTC". On Cornell VM's it is
    "US/Eastern".
    """

    """========================= Some flask specific configs ========================="""

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

    def check(self) -> None:
        """A check and fix up of a settings object."""
        if 'sqlite' in self.CLASSIC_DB_URI:
            if not self.TESTING:
                log.warning(f"using SQLite DB at {self.CLASSIC_DB_URI}")
            self.SQLALCHEMY_MAX_OVERFLOW = None
            self.SQLALCHEMY_POOL_SIZE = None

        if (os.environ.get("FLASK_ENV", False) == "production"
                and "sqlite" in self.CLASSIC_DB_URI):
            warnings.warn(
                "Using sqlite in CLASSIC_DB_URI in production environment"
            )

        if self.ABS_PATH_ROOT.startswith("gs://"):
            self.FS_TZ = "UTC"
            log.warning("Switching FS_TZ to UTC since ABS_PATH_ROOT is Google Storage")
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
                log.warning("GOOGLE_APPLICATION_CREDENTIALS is set")
            else:
                log.warning("GOOGLE_APPLICATION_CREDENTIALS is not set")
