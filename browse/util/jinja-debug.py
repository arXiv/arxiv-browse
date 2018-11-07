
import pprint
from sys import version_info

from jinja2 import nodes
from jinja2.defaults import BLOCK_START_STRING, \
     BLOCK_END_STRING, VARIABLE_START_STRING, VARIABLE_END_STRING, \
     COMMENT_START_STRING, COMMENT_END_STRING, LINE_STATEMENT_PREFIX, \
     LINE_COMMENT_PREFIX, TRIM_BLOCKS, NEWLINE_SEQUENCE, \
     KEEP_TRAILING_NEWLINE, LSTRIP_BLOCKS
from jinja2.environment import Environment
from jinja2.nodes import ContextReference
from jinja2.runtime import concat
from jinja2.exceptions import TemplateAssertionError, TemplateSyntaxError
from jinja2.ext import Extension
from jinja2.utils import contextfunction, import_string, Markup
from jinja2._compat import with_metaclass, string_types, iteritems
from markupsafe import escape


class DebugExtension(Extension):
    """
    A ``{% debug %}`` tag that dumps the available variables, filters and tests.
    Typical usage like this:
    .. codeblock:: html
        <pre>{% debug %}</pre>
    produces output like this:
    ``
        {'context': {'_': <function _gettext_alias at 0x7f9ceabde488>,
                 'csrf_token': <SimpleLazyObject: 'lfPE7al...q3bykS4txKfb3'>,
                 'cycler': <class 'jinja2.utils.Cycler'>,
                 ...
                 'view': <polls.views_auth.Login object at 0x7f9cea2cbe48>},
        'filters': ['abs', 'add', 'addslashes', 'attr', 'batch', 'bootstrap',
                 'bootstrap_classes', 'bootstrap_horizontal',
                 'bootstrap_inline', ... 'yesno'],
        'tests': ['callable', 'checkbox_field', 'defined', 'divisibleby',
               'escaped', 'even', 'iterable', 'lower', 'mapping',
               'multiple_checkbox_field', ... 'string', 'undefined', 'upper']}
    ``
    """
    tags = set(['debug'])

    def __init__(self, environment):
        super(DebugExtension, self).__init__(environment)

    def parse(self, parser):
        lineno = parser.stream.expect('name:debug').lineno
        context = ContextReference()
        call = self.call_method('_render', [context], lineno=lineno)
        return nodes.Output([nodes.MarkSafe(call)])

    def _render(self, context):
        result = {
            'filters': sorted(self.environment.filters.keys()),
            'tests': sorted(self.environment.tests.keys()),
            'context': context.get_all()
        }
        #
        # We set the depth since the intent is basically to show the top few
        # names. TODO: provide user control over this?
        #
        if version_info[:2] >= (3,4):
            text = pprint.pformat(result, depth=3, compact=True)
        else:
            text = pprint.pformat(result, depth=3)
        text = escape(text)
        return text
