"""PrevNext service to get paper IDs as if from a sequence."""

from typing import Optional, List

from browse.services.anypath import to_anypath

from browse.domain.identifier import Identifier, IdentifierException
from browse.services.documents.fs_implementation.legacy_fs_paths import FSDocMetaPaths

from browse.services import fs_check

from .prevnext_base import PrevNextService, PrevNextResult


class FSPrevNext(PrevNextService):
    """File based `PrevNextService`.

    This can handle both local files and Google Storage.
    """
    latest_versions_path: str
    original_versions_path: str


    def __init__(self,
                 latest_versions_path: str,
                 original_versions_path: str) -> None:
        """File based prev next service.

        Parameters
        ----------
        latest_versions_path : str
            Path to the latest version abs files. Ex. `/data/ftp` This can start
            with gs:// to use Google Storage. Ex
            `gs://arxiv-production-data/ftp`
        original_versions_path : str
            Path to the older versions of abs files. Ex `/data/orig` This can
            start with gs:// to use Google
            Storage. Ex. `gs://arxiv-production-data/orig`
        """

        self.fs_paths = FSDocMetaPaths(latest_versions_path, original_versions_path)

    def prevnext(self, arxiv_id: Identifier, context: Optional[str]) -> PrevNextResult:
        """Prev Next using FS.

        Hybrid approach per ARXIVNG-2080. This is a bit of a stop gap solution.

        There should be a better way to do this.  The difficulty is that
        the new IDs lack any category context so it is much more work
        to find the next ID in a category.  It maybe necesssary to go
        to the DB to find the next ID in a archive or category
        context.
        """

        if arxiv_id.is_old_id or context == 'arxiv' or not context:
            return PrevNextResult(previous_id=self.get_previous_id(arxiv_id),
                                  next_id=self.get_next_id(arxiv_id))
        else:
            return PrevNextResult(usecontroller=True)


    def get_next_id(self, identifier: Identifier) -> Optional['Identifier']:
        """Get the next identifier in sequence if it exists in the abs FS.

        Under certain conditions this is called to generate the "next" link
        in the "browse context" portion of the abs page rendering.
        These conditions are dependent on the identifier and context; it
        emulates legacy functionality. It is recommended to deprecate
        this function once the /prevnext route is fixed (or replaced) to
        handle old identifiers correctly.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The next identifier in sequence that exists in the repository.
        """
        next_id = _next_id(identifier)
        if not next_id:
            return None

        if self.fs_paths.get_abs_file(next_id):
            return next_id

        next_yymm_id = _next_yymm_id(identifier)
        if not next_yymm_id:
            return None

        if next_yymm_id and self.fs_paths.get_abs_file(next_yymm_id):
            return next_yymm_id

        return None

    def get_previous_id(self, identifier: Identifier) -> Optional[Identifier]:
        """Get previous identifier in sequence if it exists in repository.

        Under certain conditions this is called to generate the "previous" link
        in the "browse context" portion of the abs page rendering.
        These conditions are dependent on the identifier and context; it
        emulates legacy functionality. It is recommended to deprecate
        this function once the /prevnext route is fixed (or replaced) to
        handle old identifiers correctly.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The previous identifier in sequence that exists in the repository.
        """
        previous_id = _previous_id(identifier)
        if not previous_id:
            return None

        if identifier.year == previous_id.year \
           and identifier.month == previous_id.month:
            return previous_id

        path = to_anypath(self.fs_paths.get_parent_path(previous_id))
        if not path.is_dir():
            return None

        max_id = max(path.glob("*.abs"))  # TODO slow with a large directory of abs files
        if not max_id:
            return None

        try:
            if previous_id.is_old_id:
                short_id = Identifier(
                    arxiv_id=f'{previous_id.archive}/{max_id.stem}')
            else:
                short_id = Identifier(arxiv_id=max_id.stem)
            return short_id
        except IdentifierException:
            return None

        return None

    def service_status(self)->List[str]:
        probs = fs_check(self.fs_paths.latest_versions_path)
        probs.extend(fs_check(self.fs_paths.original_versions_path))
        return ["FSPrevNext: {prob}" for prob in probs]





def _next_id(identifier: Identifier) -> Optional['Identifier']:
    """Get next consecutive Identifier relative to the provided Identifier.

    Parameters
    ----------
    identifier : :class:`Identifier`

    Returns
    -------
    :class:`Identifier`
        The next Indentifier in sequence
    """
    next_id = None
    if identifier.year is not None and \
            identifier.month is not None and \
            identifier.num is not None:
        new_year = identifier.year
        new_month = identifier.month
        new_num = identifier.num + 1
        if (identifier.is_old_id and new_num > 999) \
           or (not identifier.is_old_id
               and identifier.year < 2015
               and new_num > 9999) \
           or (not identifier.is_old_id
               and identifier.year >= 2015 and new_num > 99999):
            new_num = 1
            new_month = new_month + 1
            if new_month > 12:
                new_month = 1
                new_year = new_year + 1

        if identifier.is_old_id:
            next_id = '{}/{:02d}{:02d}{:03d}'.format(
                identifier.archive, new_year % 100, new_month, new_num)
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
    else:
        return None


def _next_yymm_id(identifier: Identifier) -> Optional[Identifier]:
    """Get the first identifier for the next month.

    This does not access any data, it just gets the first ID of the next month.
    """
    next_yymm_id = None
    if identifier.year is not None and \
            identifier.month is not None:
        new_year = identifier.year
        new_month = identifier.month + 1
        new_num = 1
        if new_month > 12:
            new_month = 1
            new_year = new_year + 1
        if identifier.is_old_id:
            next_yymm_id = '{}/{:02d}{:02d}{:03d}'.format(
                identifier.archive, new_year % 100, new_month, new_num)
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
    else:
        return None


def _previous_id(identifier: Identifier) -> Optional['Identifier']:
    """Get previous consecutive Identifier relative to provided Identifier.

    This does not access any data, it just gets the previous ID taking into
    account months, years and format changes.

    Parameters
    ----------
    identifier : :class:`Identifier`

    Returns
    -------
    :class:`Identifier`
        The previous Indentifier in sequence
    """
    previous_id = None
    if identifier.year is not None and \
            identifier.month is not None and \
            identifier.num is not None:
        new_year = identifier.year
        new_month = identifier.month
        new_num = identifier.num - 1
        if new_num == 0:
            new_month = new_month - 1
            if new_month == 0:
                new_month = 12
                new_year = new_year - 1

        if identifier.is_old_id:
            if new_num == 0:
                new_num = 999
            previous_id = '{}/{:02d}{:02d}{:03d}'.format(
                identifier.archive, new_year % 100, new_month, new_num)
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
    else:
        return None
