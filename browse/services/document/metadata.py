"""Parse fields from a single arXiv abstract (.abs) file."""
import json
import re


class ArXivAbsError(Exception):
    """Error class for general arXiv .abs errors."""

    pass


class ArXivAbsParsingError(ArXivAbsError):
    """Error class for arXiv .abs file parsing errors."""

    pass


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
                  'license', 'copyright']:
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
