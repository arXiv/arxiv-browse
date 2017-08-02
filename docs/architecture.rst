Browse Application
******************

The browse application provides reader-facing views onto arXiv documents and
their metadata. "Browse" functionality encompasses the abstract page, content
views (e.g. PDF, HTML), and views onto the classification hierarchy.

The abstract page provides metadata about an arXiv document/version, links to
document content, and links to resources related to that document. In the
Classic arXiv system, the abstract page is provided at arxiv.org/abs/[arxiv id]
by a Perl controller abs.pl. The eventual goal is provide the abstract page, and
other browse-related views, via a stand-alone web application that is decoupled
from other parts of the system (e.g. deployed on separate hardware, with its own
secondary data store).

The development strategy for this component is to incrementally migrate the
abstract view out of the existing Classic web application first by servicing the
existing endpoint from behind the current web server using the existing
database, and then incrementally migrating to new data stores and
infrastructure. This depends on adherence to a core set of architectural
constraints that allow the layers of the application to evolve independently.

The architecture described below is a starting point for further engineering,
and should evolve as the the application is implemented.

Stage 1: Abstract View
======================

This phase involves replacing the current abs.pl controller with a Python/Flask
application. This new application will run behind the existing Apache webserver,
via mod_wsgi. At the end of phase 1, abs.pl will be replaced with the
Python/Flask application and the view provided to the browser will be nearly
identical to the existing abstract page, with the addition of cited references.

.. _figure-ng-components-browse-phase1:

.. figure:: diagrams/ng-components-browse-phase1.png
   :target: diagrams/ng-components-browse-phase1.png

   Main components of the browse application in phase 1.

The service layer will provide access to the existing network filesystem and
relational database via a more abstract API. This will involve identifying the
database and filesystem resources that are used to generate the current abs
page, and writing components that provide read access to those resources.

Document Service Layer
----------------------

The document service layer separates the web application controllers from the
specific maneuvers needed to wrangle the data needed to generate user-facing
views. In order to integrate sensibly with Flask, we separate this part of
the application into two parts: a ``DocumentServiceSession`` class that
encapsulates IO operations (including database sessions), and a
``DocumentService`` class that is responsible for associating a specific
``DocumentServiceSession`` instances with a specific application and its
attendant configuration.

This component must be implemented such that the lower part can be altered (e.g.
a new database backend, a different ORM library) without impacting the API
exposed to the rest of the application. API methods must only accept and return
"native" Python data types.

.. _figure-ng-classes-browse-phase1-service:

.. figure:: diagrams/ng-classes-browse-phase1-service.png
   :target: diagrams/ng-classes-browse-phase1-service.png

   Example architecture of the document service layer component. This is merely
   a rough indication of how the component could be implemented.


``DocumentService``
^^^^^^^^^^^^^^^^^^^

The ``DocumentService`` component is a class that implements the Flask
extension pattern. See `this example
<http://flask.pocoo.org/docs/0.12/extensiondev/#the-extension-code>`_. The
class should have the following methods:

``__init__(self, app=None)``
    Sets ``self.app`` to the passed Flask app instance, and calls ``init_app``.

``init_app(self, app)``
    Sets defaults for relevant configuration variables on the Flask app
    instance. This should include the database URL (see
    `<https://www.12factor.net/backing-services>`_), which includes
    authentication details.

``get_session(self)``
    Retrieve configuration variables from the app instance, instantiate
    a database connection (e.g. see `<http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#creating-a-session>`_),
    and check that appropriate access to the filesystem is available. It should
    return an instance of a ``DocumentServiceSession`` which provides the
    appropriate read methods.

In addition, a property called ``session`` should provide access to the
appropriate ``DocumentServiceSession`` instance using the `Flask application
context stack <http://flask.pocoo.org/docs/0.12/appcontext/>`_. For example:

.. code-block:: python

   from flask import _app_ctx_stack as stack


   class DocumentService(object):
       ...

       @property
       def session(self):
           ctx = stack.top
           if ctx is not None:
               if not hasattr(ctx, 'document_session'):
                   ctx.document_session = self.get_session()
               return ctx.document_session
           return self.get_session()     # No application context.


``DocumentServiceSession``
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``DocumentServiceSession`` class is the glue between the application and
the data sources that back the abstract page. It uses a combination of
filesystem operations and SQL queries to retrieve relevant data for use by
the controller backing the main ``abs`` route.

In order to decouple the lower-level implementation details from its
higher-level behavior, ``DocumentServiceSession`` must only expose/return
native Python data types.

Similarly, any exceptions raised by lower-level packages (e.g. SQLAlchemy)
should be handled internally; exceptions **may** be propagated upward, but
**must** be re-instantiated as either native Python exceptions or subclasses of
those exceptions provided in the same namespace as the
``DocumentServiceSession`` class. For example::

   from sqlalchemy.orm.exc import ConcurrentModificationError


   class DocumentServiceSession(object):
       ...
       def read(self, ....):
           ...
           try:
              ...
           except ConcurrentModificationError as e:
              raise IOError('Consistency problems: %s' % e) from e


An ORM abstraction (e.g. via SQLAlchemy) may be used to perform SQL queries.
Any "model" classes must be available to the ``DocumentServiceSession``
class (e.g. in the same module).


Application Factory & Configuration
-----------------------------------

The configuration module (``config.py``) should define any relevant Flask
configuration parameters, plus any additional parameters for database
connections, logging, etc. See `<http://flask.pocoo.org/docs/0.12/config/>`_.

The browse application should include a module called ``factory`` containing an
application factory function called ``create_web_app`` (see
`Application Factories
<http://flask.pocoo.org/docs/0.12/patterns/appfactories/>`_). That function
should instantiate the Flask WSGI application, load the application
configuration, register any `blueprints
<http://flask.pocoo.org/docs/0.12/blueprints/#blueprints>`_, and return the
Flask application object.

For example:

.. code-block:: python

   def create_web_app():
       """Initialize an instance of the web application."""
       from browse.routes import rest

       app = Flask('browse', static_folder='web/static',
                   template_folder='web/templates')
       app.config.from_pyfile('config.py')
       app.register_blueprint(rest.blueprint)
       return app


The WSGI module called by Apache should be a Python script called
``browse.wsgi``, located at the root of the project. It should define a single
function called ``application`` that calls ``factory.create_web_app``. In
order to populate the application's runtime environment with configuration
parameters, it should set those parameters in ``os.environ`` using the values
passed by mod_wsgi. For example:

.. code-block:: python

   from reflink.factory import create_web_app
   import os


   def application(environ, start_response):
        for key, value in environ.items():
            os.environ[key] = str(value)
        return create_web_app()(environ, start_response)


Routes
------
The routes module should be used to define the blueprint(s) for the
application. That module is responsible for passing relevant parameters
from the request context to controllers, and rendering/serializing data
returned by the controllers for return to clients. In order to facilitate
unit tests significant business logic should reside in the controller
module, **not** in the routes module.

For example:

.. code-block:: python

   from flask import Blueprint, render_template
   from browse.controllers import retrieve_document_metadata
   blueprint = Blueprint('browse', __name__, url_prefix='')


   @blueprint.route('/abs/<string:document_id>', methods=['GET'])
   def abs(document_id: str):
       ...
       document_metadata, status = retrieve_document_metadata(document_id)
       return render_template('abs.html', **document_metadata), status


Controllers
-----------
Controllers should be implemented in a separate module. These can be classes
or functions that handle request parameters from the routes, and return data
needed to build responses/views.

Since we are using the Flask factory pattern, the ``current_app`` proxy object
should be used to access the application instance. For example, to instantiate
the ``DocumentService``. For example:

.. code-block:: python

   from flask import current_app
   from browse.services import DocumentService
   from browse import status


   def retrieve_document_metadata(document_id: str) -> Tuple[dict, int]:
       ...
       try:
           service = DocumentService(current_app)
       except RuntimeError:   # Raised when there is no application context.
           service = DocumentService()
       ...
       try:
           session = service.session
       except IOError as e:    # Service layer raises only native exceptions.
            return {
                'explanation': 'Could not access the database.'
            }, status.HTTP_500_INTERNAL_SERVER_ERROR


In the example above, the controller returns both a data payload and an HTTP
status code (int).

Layout
------
The following layout would be consistent with the constraints described above.

.. code-block:: bash

   .
   ├── README.md
   ├── browse.wsgi
   ├── browse
   │   ├── __init__.py
   │   ├── factory.py
   │   ├── config.py
   │   ├── routes.py
   │   ├── controllers.py
   │   └── services
   │       ├── __init__.py
   │       ├── sql.py
   │       └── filesystem.py
   ├── requirements.txt
   ├── templates
   │   └── abs.html
   └── tests
       ├── __init__.py
       ├── test_controllers.py
       └── test_document_service.py


This is only a rough guide, and should be modified as needed.
