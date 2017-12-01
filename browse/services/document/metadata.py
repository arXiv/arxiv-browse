"""Parse fields from a single arXiv abstract (.abs) file."""
import json
import re


class ArXivAbsError(Exception):
    """Error class for general arXiv .abs errors."""

    pass


class ArXivAbsParsingError(ArXivAbsError):
    """Error class for arXiv .abs file parsing errors."""

    pass

# (recipe for later consideration)
# Base class. Uses a descriptor to set a value
# class Descriptor:
#     def __init__(self, name=None, **opts):
#         self.name = name
#         for key, value in opts.items():
#             setattr(self, key, value)
#
#     def __set__(self, instance, value):
#         instance.__dict__[self.name] = value
#
# # Decorator for applying type checking
# def Typed(expected_type, cls=None):
#     if cls is None:
#         return lambda cls: Typed(expected_type, cls)
#
#     super_set = cls.__set__
#     def __set__(self, instance, value):
#         if not isinstance(value, expected_type):
#             raise TypeError('expected ' + str(expected_type))
#         super_set(self, instance, value)
#     cls.__set__ = __set__
#     return cls


class ArXivDocMetadata(object):
    """Class for representing arXiv document metadata."""

    RE_ABS_COMPONENTS = re.compile(r'^\\\\\n', re.MULTILINE)
    RE_FROM_FIELD = re.compile(
        r'From:\s*(?P<name>[^<]+)?\s*(<(?P<email>.*)>)?')
    RE_DATE_COMPONENTS = re.compile(
        r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
        '(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')
    RE_FIELD_COMPONENTS = re.compile(
        r'^(?P<field>[-a-z\)\(]+\s*):\s*(?P<value>.*)', re.IGNORECASE)
    RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
        r'(Paper:\s+|arXiv:)(?P<paper_id>\S+)')

    def __init__(self, filename: str):
        """Init tbd."""
        # keeping simple for now -- stronger type enforcement later?
        self.initialized = False
        self.filename = filename
        self.paper_id = None
        self.abstract = None
        self.history = {}
        self.submitter = {}

        # fields that may be parsed from the key-value pairs in second main
        # component of .abs file. Key names here have been normalized and do
        # not necessarily match those in the .abs file.
        for f in ['title', 'authors', 'categories', 'comments', 'proxy',
                  'report_num', 'acm_class', 'msc_class', 'journal_ref', 'doi',
                  'license']:
            setattr(self, f, None)
        self.categories = []

        self._parse_abs_file()

    def _parse_abs_file(self):
        """Parse arXiv .abs file."""
        f = open(self.filename, 'rt')
        raw = f.read()

        # there are two main components to an .abs file that contain data,
        # but the split should always return four components
        components = self.RE_ABS_COMPONENTS.split(raw)
        if not len(components) == 4:
            raise ArXivAbsParsingError(
                'Unexpected number of components parsed from .abs file.')

        # abstract is the first main component
        self.abstract = components[2]

        # everything else is in the second main component
        prehistory, misc_fields = re.split(r'\n\n', components[1])
        id_match = self.RE_ARXIV_ID_FROM_PREHISTORY.match(prehistory)

        if not id_match:
            raise ArXivAbsParsingError(
                'Could not extract arXiv ID from prehistory component.')

        self.paper_id = id_match.group('paper_id')

        prehistory = re.sub(r'^.*\n', '', prehistory)
        dates = re.split(r'\n', prehistory)

        # submitter data
        from_match = self.RE_FROM_FIELD.match(dates.pop(0))
        if not from_match:
            raise ArXivAbsParsingError('Could not extract submitter data.')
        name = from_match.group('name')
        self.submitter['name'] = name.rstrip() if name else None
        self.submitter['email'] = from_match.group('email')

        # get the version history for this particular version of the document
        if not len(dates) >= 1:
            raise ArXivAbsParsingError('At least one date entry is expected.')
        version_count = 0
        for date in dates:
            version_count += 1
            date_match = self.RE_DATE_COMPONENTS.match(date)
            if not date_match:
                raise ArXivAbsParsingError(
                    'Could not extract date componenents from date line.')
            date = {
                'dateline': date_match.group(0),
                'date': date_match.group('date'),
                'size_kilobytes': int(date_match.group('size_kilobytes')),
                'source_type': date_match.group('source_type')
            }
            self.history['v{}'.format(version_count)] = date
        self.version = version_count

        # key-value fields
        misc_fields = misc_fields.lstrip()
        field_lines = re.split(r'\n', misc_fields)
        fields = {}
        field_name = 'unknown'
        for field_line in field_lines:
            field_match = self.RE_FIELD_COMPONENTS.match(field_line)
            if field_match:
                field_name = field_match.group(
                    'field').lower().replace('-', '_')
                re.sub(r'_no$', '_num', field_name)
                value = field_match.group('value').rstrip()
                fields[field_name] = value
            else:
                fields[field_name] += re.sub(r'^\s+', ' ', field_line)

        for key, value in fields.items():
            setattr(self, key, value)

        self.initialized = True

    def __repr__(self):
        """
        Representation of the class instance.

        Includes the filename being parsed.
        """
        return (
            '{}(filename="{}")'.format(self.__class__.__name__, self.filename)
        )

    def __str__(self):
        """Return the string epresentation of the instance in json."""
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=True)

# class ArXivItem():
#     """Central class for arXiv items (papers)."""

    # def __init__():


class ArXivIdentifier():
    """Class for arXiv identifiers."""

    # 1991 to 2007-03
    RE_ARXIV_OLD_ID = re.compile(
        r'^(?P<archive>[a-z]{1,}(\-[a-z]{2,})?)(\.([a-zA-Z\-]{2,}))?\/'
        r'(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))(?P<num>\d\d\d)'
        r'(v(?P<version>\d+))?([#\/].*)?$')

    # 2007-04 to present
    RE_ARXIV_NEW_ID = re.compile(
        r'^(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))\.(?P<num>\d{4,5})'
        r'(v(?P<version>\d+))?([#\/].*)?$'
    )

    def __init__(self, arxiv_id: str):
        """Attempt to validate the provided arXiv id.

        Parse constituent parts.
        """
        self.version = 0
        parse_actions = ((self.RE_ARXIV_OLD_ID, self._parse_old_id),
                         (self.RE_ARXIV_NEW_ID, self._parse_new_id))

        id_match = None
        for regex, parse_action in parse_actions:
            id_match = re.match(regex, arxiv_id)
            if id_match:
                parse_action(id_match)
                break

        if not id_match:
            # TODO: improve
            raise Exception('Invalid arXiv identifier')

        if id_match.group('version'):
            self.version = int(id_match.group('version'))
            self.idv = '{}v{}'.format(
                self.id, self.version)
        else:
            self.idv = self.id
        self.yymm = id_match.group('yymm')
        self.month = int(id_match.group('mm'))
        self.num = int(id_match.group('num'))

    def _parse_old_id(self, match):
        """Populate instance attributes parsed from old arXiv identifier."""
        self.is_old_id = True
        self.archive = match.group('archive')
        self.year = int(match.group('yy')) + 1900
        self.year += 100 if int(match.group('yy')) < 91 else 0

        if match.group('version'):
            self.version = int(match.group('version'))
        self.filename = '{}{:03d}'.format(
            match.group('yymm'),
            int(match.group('num')))
        self.id = '{}/{}'.format(self.archive, self.filename)
        self.is_submission = True if self.archive == 'submit' else False

    def _parse_new_id(self, match):
        """Populate instance attributes from a new arXiv identifier.

        e.g. 1711.01234
        """
        self.is_old_id = False
        self.archive = 'arxiv'
        # works only until 2099
        self.year = int(match.group('yy')) + 2000
        if self.year >= 2015:
            self.id = '{:04d}.{:05d}'.format(
                int(match.group('yymm')),
                int(match.group('num')))
        else:
            self.id = '{:04d}.{:04d}'.format(
                int(match.group('yymm')),
                int(match.group('num')))
        self.filename = self.id
        self.is_submission = False

    def __str__(self):
        """Return the string epresentation of the instance in json."""
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=True)
