"""Service to of functions related to articles."""

import re
from typing import Union, Literal, Optional

from arxiv.identifier import Identifier


from arxiv_dissemination.services.object_store import FileObj, ObjectStore

from .key_patterns import abs_path_current_parent, abs_path_orig_parent, ps_cache_pdf_path, current_pdf_path, previous_pdf_path, abs_path_orig, abs_path_current, Formats

import logging
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


Conditions = Literal["WITHDRAWN", # Where the version is a WDR
                     "ARTICLE_NOT_FOUND", # Where there is no article
                     "VERSION_NOT_FOUND", # Where the article exists but the version does not
                     "UNAVAIABLE", # Where the PDF unexpectedly does not exist
                     ]

AbsConditions = Literal["ARTICLE_NOT_FOUND",
                        "VERSION_NOT_FOUND",
                        "NO_ID"]

# From arxiv/browse/services/util/formats.py
VALID_SOURCE_EXTENSIONS = [
    '.tar.gz',
    '.pdf',
    '.ps.gz',
    '.gz',
    '.dvi.gz',
    '.html.gz',
]


v_regex = re.compile(r'.*v(\d+)')

def _path_to_version(path: FileObj):
    mtch = v_regex.search(path.name)
    if mtch:
        return int(mtch.group(1))
    else:
        return 0

class ArticleStore():
    def __init__(self, objstore: ObjectStore):
        self.objstore: ObjectStore = objstore

    def current_version(self, arxiv_id:Identifier) -> Optional[int]:
        """Gets the version number of the latest versoin of `arxiv_id`

        Returns None if there is no article witht this ID."""
        orgprefix =f"{abs_path_orig_parent(arxiv_id)}/{arxiv_id.filename}"
        abs_versions = list(self.objstore.list(orgprefix))
        if abs_versions:
            return max(map(_path_to_version, abs_versions)) + 1

        currprefix=abs_path_current(arxiv_id)
        if self.objstore.to_obj(currprefix).exists():
            return 1
        else:
            logger.debug(f"No current_version, since no objects found in {self.objstore} at {orgprefix} and {currprefix}")
            return None  # article does not exist

    def abs_for_id(self, arxiv_id: Identifier, version=0, current=0, any=False) -> Union[FileObj, AbsConditions]:
        first_version = (version != 0 and version == 1) or arxiv_id.version == 1
        if current or not arxiv_id.has_version or first_version:
            abs = self.objstore.to_obj(abs_path_current(arxiv_id))
            if abs.exists():
                return abs
            else:
                return "ARTICLE_NOT_FOUND" # should always be a current abs file

        version = version or arxiv_id.version
        abs = self.objstore.to_obj(abs_path_orig(arxiv_id, version=version))
        if abs.exists():
            return abs

        # All that is left is if a version is desired and that version is the one in ftp.
        # The version in ftp is one higher than the highest version in orig.
        abs = self.objstore.to_obj(abs_path_orig(arxiv_id, version=arxiv_id.version-1))
        if abs.exists():
            return abs
        else:
            return "VERSION_NOT_FOUND" # ambitious? what if the article doens't exist?


    def dissemination_for_id(self, format: Formats, arxiv_id: Identifier) -> Union[Conditions, FileObj]:
        """Gets FileObj for an `Identifier` with or without a version."""
        if format != "pdf":
            raise Exception("Only PDF is currently supported")

        if not arxiv_id.has_version:
            return self.dissemination_for_id_current(format, arxiv_id)
        
        ps_cache_pdf = self.objstore.to_obj(ps_cache_pdf_path(format, arxiv_id))
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        non_current_pdf=self.objstore.to_obj(previous_pdf_path(arxiv_id))
        if non_current_pdf.exists():
            return non_current_pdf

        current_pdf = self.objstore.to_obj(current_pdf_path(arxiv_id))
        if current_pdf.exists():
            return current_pdf

        abs = self.abs_for_id(arxiv_id)
        if abs in ["ARTICLE_NOT_FOUND", "VERSION_NOT_FOUND"]:
            return abs            
        if self.is_withdrawn(arxiv_id):
            return "WITHDRAWN"
        else:
            logger.debug("no file found for %s, tried %s", arxiv_id.idv,
                         [str(ps_cache_pdf), str(non_current_pdf), str(current_pdf)])
            return "UNAVAIABLE"

    def dissemination_for_id_current(self, format: Formats, arxiv_id: Identifier) -> Union[Conditions, FileObj]:
        """Gets PDF FileObj for most current version for `Identifier`."""
        version = self.current_version(arxiv_id)
        if not version:
            logger.debug("No current version found for article %s, therfore does not exist", arxiv_id.id)
            return "ARTICLE_NOT_FOUND"
        
        ps_cache_pdf = self.objstore.to_obj(ps_cache_pdf_path(format, arxiv_id, version))
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        current_pdf = self.objstore.to_obj(current_pdf_path(arxiv_id))
        if current_pdf.exists():
            return current_pdf

        abs = self.abs_for_id(arxiv_id)
        if abs in ["ARTICLE_NOT_FOUND", "VERSION_NOT_FOUND"]:
            return abs            
        if self.is_withdrawn(arxiv_id):
            return "WITHDRAWN"
        else:
            logger.debug("no file found for %s, tried %s", arxiv_id.idv,
                         [str(ps_cache_pdf), str(current_pdf)])
            return "UNAVAIABLE"


    def is_withdrawn(self, arxiv_id: Identifier, known_current=False) -> bool:
        """Is a version is withdrawn?

        This will be the case if there is no source for a version"""

        if not arxiv_id.has_version:
            raise Exception("Must pass version to is_withdrawn")

        if not known_current:
            current_v = self.current_version(arxiv_id)
            known_current = arxiv_id.version == current_v
            
        if known_current:
            pattern = f"{abs_path_current_parent(arxiv_id)}/{arxiv_id.filename}"
        else:
            pattern = f"{abs_path_orig_parent(arxiv_id)}/{arxiv_id.filename}v{arxiv_id.version}"

        items = list(self.objstore.list(pattern))
        if len(items) > 16:
            logger.warning("list of matches to is_withdrawn was %d, unexpectedly large", len(items))
            return True #really strange but don't get into the case of handling a huge list

        # does any obj key match with any extension?
        return bool(any(map(lambda item: any(map(lambda ext: item.name.endswith(ext), VALID_SOURCE_EXTENSIONS)), items)))
