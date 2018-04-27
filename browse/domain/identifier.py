"""Base domain classes for browse service."""
import json
import re
from typing import Match

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
    (r'([^a\-])(ph|ex|th|qc|mat|lat|sci)(\/|$)', '\g<1>-\g<2>\g<3>', 1, 0)
)


class IdentifierException(Exception):
    """Error class for general arXiv identifier exceptions."""

    pass


class Identifier(object):
    """Class for arXiv identifiers of published papers."""

    def __init__(self, arxiv_id: str) -> None:
        """Attempt to validate the provided arXiv id.

        Parse constituent parts.
        """
        # id specified
        self.ids = arxiv_id
        # TODO: recheck for mypy
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
                'invalid arXiv identifier {}'.format(self.ids)
            )

        self.num = int(id_match.group('num'))
        if self.num == 0:
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

    def _parse_old_id(self, matchobj: Match[str]) -> None:
        """Populate instance attributes parsed from old arXiv identifier.

        The old identifiers were minted from 1991 until March 2003.
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

        e.g. 1401.1234
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

    def __str__(self) -> str:
        """Return the string representation of the instance in json."""
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=True)
