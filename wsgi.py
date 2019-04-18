"""Web Server Gateway Interface (WSGI) entry-point."""
import os

from browse.factory import create_web_app

# We need someplace to keep the flask app around between requests.
# Double underscores excludes this from * imports.
__flask_app__ = None

def application(environ, start_response):
    """WSGI application, called onece for each HTTP request.

    application() will be called once for each HTTP request. WSGI has
    no initialization lifecycle phase. This code will only get run
    with a HTTP request in the environ.

    The Flask app should be reused across requests. Creating the
    Flask app for each request showed up as a problem in 2019 where
    SQLAlchemy connection pooling seemed to be disabled because a new
    SQLAlchemy DB was created for each requsest.

    Apache httpd passes config from SetEnv directives via the request
    environ.  We currently have a use case of running apache HTTPD
    with mod_wsgi and setting environment variables for Flask apps
    with apache's SetEnv directive. SetEnv does not seem to set an OS
    environment variable that is perserved in the WSGI deamon
    process. SetEnv values are passed to WSGI application() in the
    environ agrument. 

    This will not be needed once each app is on docker+enginx.
    """

    # Copy string WSGI envrion to os.environ. This is to get apache
    # SetEnv vars.  It needs to be done before the call to
    # create_web_app() due to how config is setup from os in
    # browse/config.py.
    for key, value in environ.items():        
        if type(value) is str:
            os.environ[key] = value

    # 'global' actually means module scope, and that is exactly what
    # we want here.
    #    
    # Python docs are thin. I'm seeing this sort of thing on
    # stackoverflow: "In Python there is no such thing as absolute
    # globals automatically defined across all namespaces
    # (thankfully). As you correctly pointed out, a global is bound to
    # a namespace within a module..."    
    global __flask_app__
    if __flask_app__ is None:
        __flask_app__ = create_web_app()

    return __flask_app__(environ, start_response)
