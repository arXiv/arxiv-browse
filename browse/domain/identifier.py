"""Base domain classes for browse service."""
import json
import re
from typing import Match
from arxiv import taxonomy

# arXiv ID format used from 1991 to 2007-03
RE_ARXIV_OLD_ID = re.compile(
    r'^(?P<archive>[a-z]{1,}(\-[a-z]{2,})?)(\.([a-zA-Z\-]{2,}))?\/'
    r'(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))(?P<num>\d\d\d)'
    r'(v(?P<version>[1-9]\d*))?([#\/].*)?$')

# arXiv ID format used from 2007-04 to present
RE_ARXIV_NEW_ID = re.compile(
    r'^(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))\.(?P<num>\d{4,5})'
    r'(v(?P<version>[1-9]\d*))?([#\/].*)?$'
)

SUBSTITUTIONS = (
    # pattern, replacement, count, flags
    (r'\.(pdf|ps|gz|ps\.gz)$', '', 0, 0),
    (r'^/', '', 0, 0),
    (r'^arxiv:', '', 1, re.I),
    (r'//+', '/', 0, 0),
    (r'--+', '-', 0, 0),
    (r'^([^/]+)', lambda x: str.lower(x.group(0)), 1, 0),
    (r'([^a\-])(ph|ex|th|qc|mat|lat|sci)(\/|$)', r'\g<1>-\g<2>\g<3>', 1, 0)
)


class IdentifierException(Exception):
    """Error class for general arXiv identifier exceptions."""

    pass


class IdentifierIsArchiveException(IdentifierException):
    """Error class for case where supplied arXiv identifier is an archive."""

    pass


class Identifier(object):
    """Class for arXiv identifiers of published papers."""

    def __init__(self, arxiv_id: str) -> None:
        """Attempt to validate the provided arXiv ID.

        Parse constituent parts.
        """
        self.ids = arxiv_id
        """The ID as specified."""
        self.id = None
        self.archive = None
        self.filename = None
        self.year = None
        self.month = None
        self.is_old_id = None

        if self.ids in taxonomy.ARCHIVES:
            raise IdentifierIsArchiveException(
                taxonomy.ARCHIVES[self.ids]['name'])

        for subtup in SUBSTITUTIONS:
            arxiv_id = re.sub(subtup[0],  # type: ignore
                              subtup[1],
                              arxiv_id,
                              count=subtup[2],
                              flags=subtup[3])

        self.version = 0
        parse_actions = ((RE_ARXIV_OLD_ID, self._parse_old_id),
                         (RE_ARXIV_NEW_ID, self._parse_new_id))

        id_match = None
        for regex, parse_action in parse_actions:
            id_match = re.match(regex, arxiv_id)
            if id_match:
                parse_action(id_match)
                break

        if not id_match:
            raise IdentifierException(
                f'invalid arXiv identifier {self.ids}'
            )

        self.num = int(id_match.group('num'))
        if self.num == 0 \
           or (self.num > 99999 and self.year >= 2015) \
           or (self.num > 9999 and self.year < 2015) \
           or (self.num > 999 and self.is_old_id):
            raise IdentifierException(
                'invalid arXiv identifier {}'.format(self.ids)
            )
        if id_match.group('version'):
            self.version = int(id_match.group('version'))
            self.idv = f'{self.id}v{self.version}'
            self.has_version = True
        else:
            self.has_version = False
            self.idv = self.id
        self.squashed = self.id.replace('/', '')
        self.squashedv = self.idv.replace('/', '')
        self.yymm = id_match.group('yymm')
        self.month = int(id_match.group('mm'))
        if self.month > 12 or self.month < 1:
            raise IdentifierException(
                f'invalid arXiv identifier {self.ids}'
            )
        if self.is_old_id:
            if self.year < 1991 or self.year > 2007 \
               or (self.year == 2007 and self.month > 3):
                raise IdentifierException(
                    f'invalid arXiv identifier {self.ids}'
                )
        else:
            if self.year < 2007 or (self.year == 2007 and self.month < 4):
                raise IdentifierException(
                    f'invalid arXiv identifier {self.ids}'
                )

    def _parse_old_id(self, matchobj: Match[str]) -> None:
        """Populate instance attributes parsed from old arXiv identifier.

        The old identifiers were minted from 1991 until March 2007.
        """
        self.is_old_id = True
        self.archive = matchobj.group('archive')
        self.year = int(matchobj.group('yy')) + 1900
        self.year += 100 if int(matchobj.group('yy')) < 91 else 0

        if matchobj.group('version'):
            self.version = int(matchobj.group('version'))
        self.filename = '{}{:03d}'.format(
            matchobj.group('yymm'),
            int(matchobj.group('num')))
        self.id = f'{self.archive}/{self.filename}'

    def _parse_new_id(self, matchobj: Match[str]) -> None:
        """Populate instance attributes from a new arXiv identifier.

        New identifiers started 2007-04 with 4-digit suffix;
        starting 2015 they have a 5-digit suffix.
        e.g. 0704.1234
             1412.0001
             1501.00001
             1711.01234
        """
        self.is_old_id = False
        self.archive = 'arxiv'
        # NB: this works only until 2099
        self.year = int(matchobj.group('yy')) + 2000
        if self.year >= 2015:
            self.id = '{:04d}.{:05d}'.format(
                int(matchobj.group('yymm')),
                int(matchobj.group('num')))
        else:
            self.id = '{:04d}.{:04d}'.format(
                int(matchobj.group('yymm')),
                int(matchobj.group('num')))
        self.filename = self.id

    def next_id(self):
        """Get the next Identifier in the sequence."""
        next_id = None
        new_year = self.year
        new_month = self.month
        new_num = self.num + 1
        if (self.is_old_id and new_num > 999) \
           or (not self.is_old_id and self.year < 2015 and new_num > 9999) \
           or (not self.is_old_id and self.year >= 2015 and new_num > 99999):
            new_num = 1
            new_month = new_month + 1
            if new_month > 12:
                new_month = 1
                new_year = new_year + 1

        if self.is_old_id:
            next_id = '{}/{:02d}{:02d}{:03d}'.format(
                self.archive, new_year % 100, new_month, new_num)
        else:
            if new_year >= 2015:
                next_id = '{:02d}{:02d}.{:05d}'.format(
                    new_year % 100, new_month, new_num)
            else:
                next_id = '{:02d}{:02d}.{:04d}'.format(
                    new_year % 100, new_month, new_num)
        try:
            return Identifier(arxiv_id=next_id)
        except IdentifierException:
            return None

    def next_yymm_id(self):
        """Get the first identifier for the next month."""
        next_yymm_id = None
        new_year = self.year
        new_month = self.month + 1
        new_num = 1
        if new_month > 12:
            new_month = 1
            new_year = new_year + 1
        if self.is_old_id:
            next_yymm_id = '{}/{:02d}{:02d}{:03d}'.format(
                self.archive, new_year % 100, new_month, new_num)
        elif new_year >= 2015:
            next_yymm_id = '{:02d}{:02d}.{:05d}'.format(
                new_year % 100, new_month, new_num)
        else:
            next_yymm_id = '{:02d}{:02d}.{:04d}'.format(
                new_year % 100, new_month, new_num)

        try:
            return Identifier(arxiv_id=next_yymm_id)
        except IdentifierException:
            return None

    def previous_id(self):
        """Get the previous Identifier in the sequence."""
        previous_id = None
        new_year = self.year
        new_month = self.month
        new_num = self.num - 1
        if new_num == 0:
            new_month = new_month - 1
            if new_month == 0:
                new_month = 12
                new_year = new_year - 1

        if self.is_old_id:
            if new_num == 0:
                new_num = 999
            previous_id = '{}/{:02d}{:02d}{:03d}'.format(
                self.archive, new_year % 100, new_month, new_num)
        else:
            if new_year >= 2015:
                if new_num == 0:
                    new_num = 99999
                previous_id = '{:02d}{:02d}.{:05d}'.format(
                    new_year % 100, new_month, new_num)
            else:
                if new_num == 0:
                    new_num = 9999
                previous_id = '{:02d}{:02d}.{:04d}'.format(
                    new_year % 100, new_month, new_num)
        try:
            return Identifier(arxiv_id=previous_id)
        except IdentifierException:
            return None

    def __str__(self) -> str:
        """Return the string representation of the instance in json."""
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=True)

    def __repr__(self):
        """Return the instance representation."""
        return f"Identifier(arxiv_id='{self.ids}')"

    def __eq__(self, other):
        """Return instance equality."""
        return self.__dict__ == other.__dict__
