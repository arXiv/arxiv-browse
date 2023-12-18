"""Base domain classes for browse service."""
import json
import re
from re import RegexFlag
from typing import Callable, List, Match, Optional, Tuple, Union

from arxiv import taxonomy


# arXiv ID format used from 1991 to 2007-03
RE_ARXIV_OLD_ID = re.compile(
    r'^(?P<archive>[a-z]{1,}(\-[a-z]{2,})?)(\.([a-zA-Z\-]{2,}))?\/'
    r'(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))(?P<num>\d\d\d)'
    r'(v(?P<version>[1-9]\d*))?(?P<extra>[#\/].*)?$')

# arXiv ID format used from 2007-04 to present
RE_ARXIV_NEW_ID = re.compile(
    r'^(?P<yymm>(?P<yy>\d\d)(?P<mm>\d\d))\.(?P<num>\d{4,5})'
    r'(v(?P<version>[1-9]\d*))?(?P<extra>[#\/].*)?$'
)

Sub_type = List[Tuple[str, Union[str, Callable[[Match[str]], str]],
                      int, Union[int, RegexFlag]]]
SUBSTITUTIONS: Sub_type = [
    # pattern, replacement, count, flags
    (r'\.(pdf|ps|gz|ps\.gz)$', '', 0, 0),
    (r'^/', '', 0, 0),
    (r'^arxiv:', '', 1, re.I),
    (r'//+', '/', 0, 0),
    (r'--+', '-', 0, 0),
    (r'^([^/]+)', lambda x: str.lower(x.group(0)), 1, 0),
    (r'([^a\-])(ph|ex|th|qc|mat|lat|sci)(\/|$)', r'\g<1>-\g<2>\g<3>', 1, 0)
]


class IdentifierException(Exception):
    """Error class for general arXiv identifier exceptions."""


class IdentifierIsArchiveException(IdentifierException):
    """Error class for case where supplied arXiv identifier is an archive."""


class Identifier:
    """Class for arXiv identifiers of published papers."""

    def __init__(self, arxiv_id: str) -> None:
        """Attempt to validate the provided arXiv ID.

        Parse constituent parts.
        """
        self.ids = arxiv_id
        """The ID as specified."""
        self.id: str = arxiv_id
        self.archive: Optional[str] = None
        self.filename: Optional[str] = None
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.is_old_id: Optional[bool] = None
        self.extra: Optional[str] = None

        if self.ids in taxonomy.definitions.ARCHIVES:
            raise IdentifierIsArchiveException(
                taxonomy.definitions.ARCHIVES[self.ids]['name'])

        for subtup in SUBSTITUTIONS:
            arxiv_id = re.sub(subtup[0],
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

        self.num: Optional[int] = int(id_match.group('num'))
        if self.num is None:
            raise IdentifierException('arXiv identifier is empty')
        if self.year is None:
            raise IdentifierException('year is empty')
        if self.num is not None and self.year is not None:
            if self.num == 0 \
               or (self.num > 99999 and self.year >= 2015) \
               or (self.num > 9999 and self.year < 2015) \
               or (self.num > 999 and self.is_old_id):
                raise IdentifierException(
                    f'invalid arXiv identifier {self.ids}'
                )
        self.has_version: bool = False
        self.idv: str = self.id
        if id_match.group('version'):
            self.version = int(id_match.group('version'))
            self.idv = f'{self.id}v{self.version}'
            self.has_version = True
        self.squashed = self.id.replace('/', '')
        self.squashedv = self.idv.replace('/', '')
        self.yymm: str = id_match.group('yymm')
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

    def _parse_old_id(self, match_obj: Match[str]) -> None:
        """
        Populate instance attributes parsed from old arXiv identifier.

        The old identifiers were minted from 1991 until March 2007.

        Parameters
        ----------
        match_obj : Match[str]
            A regex match on RE_ARXIV_OLD_ID

        Returns
        -------
        None

        """
        self.is_old_id = True
        self.archive = match_obj.group('archive')
        self.year = int(match_obj.group('yy')) + 1900
        self.year += 100 if int(match_obj.group('yy')) < 91 else 0

        if match_obj.group('version'):
            self.version = int(match_obj.group('version'))
        self.filename = f'{match_obj.group("yymm")}{int(match_obj.group("num")):03d}'
        self.id = f'{self.archive}/{self.filename}'

        if match_obj.group('extra'):
            self.extra = match_obj.group('extra')

    def _parse_new_id(self, match_obj: Match[str]) -> None:
        """
        Populate instance attributes from a new arXiv identifier.

        New identifiers started 2007-04 with 4-digit suffix;
        starting 2015 they have a 5-digit suffix.
        e.g. 0704.1234
             1412.0001
             1501.00001
             1711.01234

        Parameters
        ----------
        match_obj : Match[str]
            A regex match on RE_ARXIV_NEW_ID

        Returns
        -------
        None

        """
        self.is_old_id = False
        self.archive = 'arxiv'
        # NB: this works only until 2099
        self.year = int(match_obj.group('yy')) + 2000
        if self.year >= 2015:
            self.id = f'{int(match_obj.group("yymm")):04d}.{int(match_obj.group("num")):05d}'
        else:
            self.id = f'{int(match_obj.group("yymm")):04d}.{int(match_obj.group("num")):04d}'
        self.filename = self.id

        if match_obj.group('extra'):
            self.extra = match_obj.group('extra')

    def __str__(self) -> str:
        """Return the string representation of the instance in json."""
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=True)

    def __repr__(self) -> str:
        """Return the instance representation."""
        return f"Identifier(arxiv_id='{self.ids}')"

    def __eq__(self, other: object) -> bool:
        """
        Return instance equality: other should be type <= Instance.

        Note that 'other' can't be statically checked to be type Instance
        by design: https://stackoverflow.com/a/37557540/3096687

        """
        try:
            return self.__dict__ == other.__dict__
        except AttributeError:
            return False


    @staticmethod
    def is_mostly_safe(input: Optional[str]) -> bool:
        """Checks that the input could reasonably be parsed as an ID,
        fails if strange unicode, strange characters, very long etc."""
        if not input:
            return False
        if len(input) > 200:
            return False
        return bool(re.match(re.compile(r"[.\\0-9a-zA-Z-]*"), input))