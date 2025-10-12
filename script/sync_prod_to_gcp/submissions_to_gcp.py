"""
submissions_to_gcp.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
check the files exist on CIT and uploads them to GCP bucket.


publish_types = [ cross | jref | new | rep | wdr ]
See https://arxiv-org.atlassian.net/wiki/spaces/AD/pages/608403503/arXiv+Announce+Types
for the description of each type.

gist:

  * new: new published
  * rep: Version added to the published
  * wdr: The version is withdrawn
  * cross: This is how a paper is announced in its secondary categories.
  * jref: metadata update

New publish "new":
  * sync the /ftp files and ensure only current version files exist
    - if /ftp exists, this is a problem... Version should be 1, and there is no previous files.
      It there is any file (object) exists, the request is rejected.
      Human needs to decide what to do with the object under /ftp.

Replacement - "rep"
  For each announced paper ID it will:
  * All of files in /ftp - paper ID are moved to /orig prior to copying new version.
  * sync the /ftp files and ensure only current version files exist
    - if /ftp for the paper ID has any obsolete submission, it is removed.
  * sync the abs and source files to /orig if needed
    - If TeX source it will build the PDF on a CIT web node and sync those to ps_cache
    - If HTML source it will build the HTML and sync those to the ps_cache
  As the /ftp objects moved to /orig, it *should* NOT be copied as this behavior is same as the
  current publishing process.

Withdraw - "wdr":
  For each announced paper ID it will:
  * All of files in /ftp - paper ID are moved to /orig.
  * No sync from the /ftp.
  * sync the abs and source files to /orig if needed
    - If TeX source it will build the PDF on a CIT web node and sync those to ps_cache
    - If HTML source it will build the HTML and sync those to the ps_cache
  As the /ftp objects moved to /orig, it *should* NOT be copied as this behavior is same as the
  current publishing process.

Metadata update and category chanege- "jref", "cross":
  For each announced paper ID it will:
  * /ftp - .abs, submmission gets updated
  * /ps_cache gets update
  
  In some sense, this is similar to "new" except it applies to the last version 


The "upload to GCP bucket" part is from existing sync_published_to_gcp.

As a matter of fact, this borrows the most of heavy lifting part from sync_published_to_gcp.py.

The published submission queue provides the submission source file extension which is used to
upload the legacy system submissions to the GCP bucket.

See test/test_submissions_to_gcp.py for the inner working.
"""
from __future__ import annotations
import argparse
import re
import shlex
import signal
import subprocess
import sys
import typing
from datetime import timedelta, datetime, timezone
from urllib.parse import unquote
from time import gmtime, sleep
from pathlib import Path
import requests
from dataclasses import dataclass
from functools import reduce

import json
import os
import logging.handlers
import logging
import threading
import gzip
import tarfile

from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient
from google.cloud.storage import Client as StorageClient, Bucket, Blob
from google.cloud.storage.retry import DEFAULT_RETRY as STORAGE_RETRY
from requests.exceptions import RetryError, ReadTimeout

from identifier import Identifier

global WEBNODE_REQUEST_COUNT
WEBNODE_REQUEST_COUNT = 0

TIMEOUTS = {"PDF_TIMEOUT": 30, "HTML_TIMEOUT": 30}
def PDF_TIMEOUT():
    return TIMEOUTS["PDF_TIMEOUT"]

def HTML_TIMEOUT():
    return TIMEOUTS["HTML_TIMEOUT"]


logging.basicConfig(level=logging.INFO, format='%(message)s (%(threadName)s)')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
import sync_published_to_gcp
sync_published_to_gcp.logger = logger

from sync_published_to_gcp import ORIG_PREFIX, FTP_PREFIX, PS_CACHE_PREFIX, upload, \
    path_to_bucket_key, ArxivSyncJsonFormatter, CONCURRENCY_PER_WEBNODE, ensure_pdf, \
    LOG_FORMAT_KWARGS, ensure_html

ERROR_STATE_DIR = "/tmp/sync-to-gcp"

try:
    os.makedirs(ERROR_STATE_DIR, exist_ok=True)
except:
    pass


class IgnoredSubmission(Exception):
    """Signal for ignored submissions"""
    pass

class RemovedSubmission(Exception):
    """Signal for removed submissions"""
    pass

class MissingGeneratedFile(Exception):
    """Signal for PDF not existing on CIT webnode"""
    pass

class InvalidVersion(Exception):
    """Version string is invalid"""
    pass

class BrokenSubmission(Exception):
    """Something is very wrong"""
    pass

class ThreadLocalData:
    def __init__(self):
        self._local = threading.local()

    @property
    def storage(self):
        """The storage client object is created per thread."""
        if not hasattr(self._local, 'storage'):
            # Initialize the Storage instance for the current thread
            self._local.storage = StorageClient()

        return self._local.storage

    @property
    def session(self):
        """The storage client object is created per thread."""
        if not hasattr(self._local, 'session'):
             # Initialize the Storage instance for the current thread
             self._local.session = requests.Session()
        return self._local.session


thread_data = ThreadLocalData()

# Took this from parse_abs.py
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')


def parse_publish_date(dateline: str) -> dict:
    """Pick off the publish metadata and return it as a dict."""
    parsed = RE_DATE_COMPONENTS.match(dateline)
    if parsed:
        version_string = parsed.group('version')
        return {
            "version": int(version_string[1:]) if version_string else 1,
            "date": parsed.group('date'),
            "size_kilobytes": parsed.group('size_kilobytes'),
            "source_type":  parsed.group('source_type')
        }
    return {}


def md5_sum(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    md5_value = subprocess.run(['md5sum', file_path], stdout=subprocess.PIPE)
    return md5_value.stdout.decode('utf-8').strip()

#
# source_flags in database
# null
# ''
# 1
# S
# 1S
# S1
# A
# 1B
# B
# AS
#
# source_format in database
# null
# ''
# pdftex
# tex
# pdf
# withdrawn
# docx
# invalid
# ps
# html
#

# abs source flags
# D -> pdftex
# H -> html
# I -> withdrawn
# P -> PS
# X -> docx


@dataclass
class SourceFlag:
    """Represents arXiv article source file type."""

    code: str
    """Internal code for the source type."""

    __slots__ = ['code']

    @property
    def ignore(self) -> bool:
        """Withdarawn.

        All files auto ignore. No paper available.
        """
        return self.code is not None and 'I' in self.code

    @property
    def source_encrypted(self)->bool:
        """Source is encrypted and should not be made available."""
        return self.code is not None and 'S' in self.code

    @property
    def ps_only(self)->bool:
        """Multi-file PS submission.

        It is not necessary to indicate P with single file PS since in
        this case the source file has .ps.gz extension.
        """
        return self.code is not None and 'P' in self.code

    @property
    def pdflatex(self)->bool:
        """A TeX submission that must be processed with PDFlatex."""
        return self.code is not None and 'D' in self.code

    @property
    def html(self)->bool:
        """Multi-file HTML submission."""
        return self.code is not None and 'H' in self.code

    @property
    def includes_ancillary_files(self)->bool:
        """Submission includes ancillary files in the /anc directory."""
        return self.code is not None and 'A' in self.code

    @property
    def dc_pilot_data(self)->bool:
        """Submission has associated data in the DC pilot system."""
        return self.code is not None and 'B' in self.code

    @property
    def docx(self)->bool:
        """Submission in Microsoft DOCX (Office Open XML) format."""
        return self.code is not None and 'X' in self.code

    @property
    def odf(self)->bool:
        """Submission in Open Document Format."""
        return self.code is not None and 'O' in self.code

    @property
    def pdf_only(self)->bool:
        """PDF only submission with .tar.gz package.

        (likely because of anc files)
        """
        return self.code is not None and 'F' in self.code

    @property
    def cannot_pdf(self) -> bool:
        """Is this version unable to produce a PDF?

        Does not take into account withdarawn.
        """
        return self.code is not None and self.html or self.odf or self.docx

    @property
    def is_single_file(self) -> bool:
        """Is the source for this version a single file?"""
        return self.code is not None and '1' in self.code

#
# 'tex', 'pdftex', 'html', 'ps', 'pdf', 'docx', 'odf'

flag_to_source_format = {
    'D': 'pdftex',
    'H': 'html',
    'I': 'withdrawn',
    'O': 'odf',
    'P': 'ps',
    'X': 'docx'
}

src_ext_to_source_format = {
    '.html.gz': 'html',
    '.ps.gz': 'ps',
    '.pdf': 'pdf',
    '.gz': {'pdftex': 'pdftex', None: 'tex'},
    None: 'tex',
}


class SubmissionFilesState:
    """
    Given the paper ID, version, publish type and would-be src_ext, generate the desired
    file state for the submission.
    This includes the published, and (version - 1) state if it's appropriate.

    If the submission file type is uncertain, it tries to "guess" from the files on the CIT.

    Once the expectation is decided, it then maps the CIT file path to the GCP blob path.
    """
    tex_submisson_exts: typing.List[str] = [".tar.gz", ".gz"]
    submission_exts: typing.List[str] = [".ps.gz", ".tar.gz", ".gz", ".pdf", ".html.gz"]


    xid: Identifier      # paper id (aka arXiv ID)
    vxid: Identifier     # versioned paper id (aka versioned arXiv ID)
    src_ext: str         # publishing file format
    source_format: str   # submission source format (html, tex, pdf, etc.)
    source_flags: str
    single_source: bool
    archive: str         # old-style
    publish_type: str
    version: str         # from the publish event
    log_extra: dict
    submission_source: typing.Optional[str]
    published_versions: typing.List[dict]
    cache_upload: bool

    _top_levels: dict

    _extras: typing.List[dict]

    def __init__(self, arxiv_id_str: str, version: str, publish_type: str, src_ext: str,
                 source_format: str, log_extra: dict, cache_upload=True):
        try:
            if int(version) <= 0:
                raise InvalidVersion(f"{version} is invalid")
        except:
            raise InvalidVersion(f"{version} is invalid")
        self.xid = Identifier(arxiv_id_str)  # arXiv paper ID (xid)
        # since I can pick up the latest version from .abs, I may not need to set this at all.
        self.version = 1
        try:
            self.version = int(version)  # published submission version from event
        except ValueError:
            pass
        # versioned ID (Versioned XID)
        self.vxid = self.xid if self.xid.has_version else Identifier(f"{arxiv_id_str}v{version}")
        self.publish_type = publish_type
        self.src_ext = src_ext
        self.log_extra = log_extra
        self.source_format = source_format
        self.source_flags = ""
        self.submission_source = None
        self.single_source = False
        self._extras = []
        self.published_versions = []  # This is the versions from existing .abs on file system
        self.cache_upload = cache_upload

        self.ext_candidates = SubmissionFilesState.submission_exts.copy()
        if src_ext:
            if src_ext in self.ext_candidates[1:]:
                self.ext_candidates.remove(src_ext)
            self.ext_candidates.insert(0, src_ext)

        self.archive = 'arxiv' if not self.xid.is_old_id else self.xid.archive

        self.prev_version = 1
        try:
            self.prev_version = max(1, int(self.version) - 1)
        except:
            pass

        self._top_levels = {}
        pass

    @property
    def latest_dir(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}"

    @property
    def gz_source(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}/{self.xid.filename}.gz"

    @property
    def tgz_source(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}/{self.xid.filename}.tar.gz"

    @property
    def ps_cache_pdf_file(self):
        return f"{PS_CACHE_PREFIX}{self.vxid.archive}/pdf/{self.vxid.yymm}/{os.path.basename(self.vxid.idv)}.pdf"

    @property
    def html_root_dir(self):
        # cannot ues self
        return f"{PS_CACHE_PREFIX}{self.vxid.archive}/html/{self.vxid.yymm}/{os.path.basename(self.vxid.idv)}"

    def html_files(self, files: typing.List[str]):
        # cannot ues self
        root_dir = self.html_root_dir
        return [os.path.join(root_dir, filename) for filename in files]

    @property
    def versioned_parent(self):
        return f"{ORIG_PREFIX}{self.archive}/papers/{self.xid.yymm}"

    def source_path(self, dotext: str):
        return f"{self.latest_dir}/{self.xid.filename}{dotext}"

    def prev_source_path(self, dotext: str):
        return f"{self.versioned_parent}/{self.xid.filename}v{self.prev_version}{dotext}"

    def set_published_versions(self, datelines: typing.List[str]):
        self.published_versions = [parse_publish_date(dateline) for dateline in datelines]

    def get_version_metadata(self, version: typing.Union[str, int]) -> dict:
        if isinstance(version, str):
            version = int(version)
        published = [entry for entry in self.published_versions if entry["version"] == version]
        return published[0] if published else {}

    def update_metadata(self):
        """
        Read the .abs file and update the metadata.

        The way source_format, source_flags are used is chaotic.
        """

        # If somehow there is no src_ext specified, find it out from the CIT's files
        if not self.src_ext:
            for ext in self.ext_candidates:
                src_path = self.source_path(ext)
                if os.path.exists(src_path):
                    self.src_ext = ext
                    break

        abs_path = self.source_path(".abs")
        dates = []
        try:
            with open(abs_path, "rb") as abs_fd:
                abstract = abs_fd.read()
                for line in abstract.split(b'\n'):
                    try:
                        sline = line.decode('utf-8')
                        if sline == "":
                            break
                        if sline.startswith("Date"):
                            dates.append(sline)
                    except UnicodeDecodeError:
                        # Don't care the non- uft-8 lines as date line is a generated text.
                        pass

        except FileNotFoundError as exc:
            msg = f"abs file {abs_path} does not exist"
            logger.warning(msg)
            raise BrokenSubmission(msg) from exc

        except Exception as exc:
            msg = f"Error with {abs_path}"
            logger.warning(msg, exc_info=True)
            raise BrokenSubmission(msg) from exc

        if dates:
            self.set_published_versions(dates)

            published = self.get_version_metadata(self.version)
            # The published abs is the source of truth.
            if published:
                source_type = published["source_type"]
                self.source_flags = ""
                for source_flag in source_type:
                    if source_flag in flag_to_source_format:
                        self.source_format = flag_to_source_format[source_flag]
                        continue
                    if source_flag in "SAB":
                        self.source_flags = self.source_flags + source_flag
                        continue

        # is this a single source submission?
        self.single_source = self.src_ext != ".tar.gz"

        if not self.single_source:
            # It the source format isn't decided, it's probably tex submission
            if not self.source_format:
                self.source_format = "tex"
        else:
            if self.src_ext in src_ext_to_source_format:
                maybe_source_format = src_ext_to_source_format[self.src_ext]
                if isinstance(maybe_source_format, dict):
                    source_format = maybe_source_format.get(self.source_format)
                    if source_format is None:
                        self.source_format = maybe_source_format[None]
                    else:
                        self.source_format = source_format
                else:
                    self.source_format = maybe_source_format

    @property
    def is_tex_submission(self) -> bool:
        """is a tex submssion"""
        assert(self.src_ext)
        assert(self.source_format)
        return self.source_format in ["tex", "pdftex"]

    @property
    def is_html_submission(self) -> bool:
        """is a HTML submission"""
        assert(self.src_ext)
        assert(self.source_format)
        return self.source_format == "html"

    @property
    def is_ps_submission(self) -> bool:
        """is a PostScript submission"""
        assert(self.src_ext)
        assert(self.source_format)
        return self.source_format == "ps"

    def get_tgz_top_levels(self) -> dict:
        """
        Retrieve the top-level files in the tar.gz file
        """
        if not self._top_levels:
            tgz_source = Path(self.tgz_source)
            if tgz_source.exists():
                try:
                    with tarfile.open(tgz_source, 'r:gz') as submission:
                        self._top_levels = {name: True for name in submission.getnames()}
                except Exception as _exc:
                    logger.warning("bad tgz: %s", self.xid.ids, extra=self.log_extra,
                                   exc_info=True, stack_info=False)
        return self._top_levels


    def get_expected_files(self):
        """
        The source may not have a consistent .tar.gz name.
        Some other possibilities:

        {paperidv}.pdf pdf only submission
        {paperidv}.gz single file submisison
        {paperidv}.html.gz html source submission

        NOTE: This cannot handle this special case.
        I think there is one case in the system where there is a submission with two source files
        that the admins manually crafted. It would have: {paperidv}.pdf and {paperidv}.tar.gz
        This was to get a pdf only submission with ancillary files.
        """

        self.update_metadata()
        metadata = self.get_version_metadata(self.version)
        if not metadata:
            # This means - the publishing - daily.sh posted the event, but .abs not on the CIT
            # disk. .abs must be created for it ond sitting on the SFS so it's a bad situation.
            logger.warning("no metadata found.", extra=self.log_extra)

        def current(t, cit): # macro!? It's just easier to read code being here
            return {"type": t, "cit": cit, "status": "current"}

        files = [current("abstract", self.source_path(".abs"))]

        if self.is_removed():
            # When a submission is removed, .abs, and the "removed" marker should be in ftp/
            files.append(current("submission", self.tgz_source))
        elif self.is_ignored():
            # When a submission is ignored, .abs, and the "removed" marker should be in ftp/
            files.append(current("submission", self.gz_source))
        elif self.publish_type == "wdr":
            # no new file uploaded. (well, .abs is uploaded)
            pass
        else:
            # Live submission - the latest uploaded
            self.submission_source = self.source_path(self.src_ext)
            files.append(current("submission", self.submission_source))

            if self.is_tex_submission:
                if self.cache_upload:
                    files.append(current("pdf-cache", self.ps_cache_pdf_file))
            elif self.is_html_submission:
                # Since this is a root dir of HTML submission, no need to "upload".
                # This is just a "marker" to initiate the html file expand.
                # Later (in submission_message_to_file_state()), this triggers to ask a web node
                # for the html, and it populates the files under the self.html_root_dir
                if self.cache_upload:
                    files.append(current("html-cache", self.html_root_dir))
                pass
            elif self.is_ps_submission:
                # Turn PS into PDF
                if self.cache_upload:
                    files.append(current("pdf-cache", self.ps_cache_pdf_file))

            pass

        if self.publish_type in ["rep", "wdr"]:
            # For these, version-1 needs to move around
            def obsolete(t, cit, obsolete_obj_on_gcp, original):
                return {"type": t, "cit": cit,
                        "status": "obsolete",
                        "version": self.prev_version,
                        "obsoleted": obsolete_obj_on_gcp, # This is the current announced.
                        "original": original  # The value should be the same as "gcp" in the end
                        }

            files.append(obsolete("abstract",
                                  self.prev_source_path(".abs"),
                                  path_to_bucket_key(self.source_path(".abs")),
                                  path_to_bucket_key(self.prev_source_path(".abs"))))

            for dotext in self.submission_exts:
                prev_source_path = self.prev_source_path(dotext)
                if os.path.exists(prev_source_path):
                    files.append(obsolete("submission",
                                          self.prev_source_path(dotext),
                                          path_to_bucket_key(self.source_path(dotext)),
                                          path_to_bucket_key(self.prev_source_path(dotext))))
                    break
            else:
                # I'm in a bind here. I have to take a guess...
                # There is some chance that it may not exist to begin with?
                # fortunately, I can assume that if the source type doesn't change, I can
                # use the same source file extent.
                this_meta = self.get_version_metadata(self.version)
                prev_meta = self.get_version_metadata(self.prev_version)
                prev_src_ext = self.src_ext
                single = False
                if prev_meta.get("source_type") != this_meta.get("source_type"):
                    prev_src_ext = ".gz"
                    for flag in prev_meta.get("source_type", ""):
                        if flag in ["A", "D"]:
                            prev_src_ext = ".tar.gz"
                            break
                        elif flag == "X":
                            prev_src_ext = ".docx.gz"
                        elif flag == "P":
                            prev_src_ext = ".ps.gz"
                        elif flag == "H":
                            prev_src_ext = ".html.gz"
                        elif flag == "I":
                            prev_src_ext = None
                        elif flag == "1":
                            single = True
                        else:
                            logger.error("unknown source flag: %s", flag, extra=self.log_extra)

                if prev_src_ext is not None:
                    if single:
                        if prev_src_ext == ".tar.gz":
                            prev_src_ext = ".gz"
                    files.append(obsolete("submission",
                                          self.prev_source_path(prev_src_ext),
                                          path_to_bucket_key(self.source_path(prev_src_ext)),
                                          path_to_bucket_key(self.prev_source_path(prev_src_ext))))

        for file_entry in files:
            file_entry["gcp"] = path_to_bucket_key(file_entry["cit"])

        return files + self._extras

    def register_files(self,
                       file_type: str,
                       files: typing.Union[typing.List[Path], typing.List[str]]) -> None:
        """
        Used for HTML submission. The actual files uploaded to the gcp bucket is unknown until
        webnode untars it. When ensure_html gets the file list, register them for the upload.
        """
        for filename in files:
            self._extras.append( {
                'type': file_type,
                'cit': str(filename),
                'gcp': path_to_bucket_key(str(filename)),
                'status': "current",
            } )

    def is_ignored(self) -> bool:
        """Is this a ignored file?

        when the gzipped source has %auto-ignored, it is an ignored.
        """
        # Ignored submission
        gz_source = Path(self.gz_source)
        if gz_source.exists():
            # Open the gzip file in read mode with text encoding set to ASCII
            try:
                with gzip.open(gz_source, 'rt', encoding='ascii') as f:
                    needle = "%auto-ignore"
                    content = f.read(len(needle))
                    if content.startswith(needle):
                        return True

            except UnicodeDecodeError:
                logger.info("Unparsable source, but no worries. if it's more than auto-ignore, it should not be ignored.: %s ext %s",
                               self.xid.ids, str(self.src_ext), extra=self.log_extra)
                return False
            except Exception as _exc:
                logger.warning("bad .gz: %s ext %s",
                               self.xid.ids, str(self.src_ext), extra=self.log_extra,
                               exc_info=True, stack_info=False)
                raise
        return False


    def is_removed(self) -> bool:
        """Is this a removed submission?
        This is done by the tar.gz toplevels and if it has the removed.txt in it, this is a
        removed submission.
        """
        # Removed submission
        return "removed.txt" in self.get_tgz_top_levels()


    def to_payloads(self):
        return [(entry["cit"], entry["gcp"]) for entry in self.get_expected_files()]

    def get_submission_mtime(self) -> float:
        """
        Get the mtime of the submission.
        """
        if self.submission_source:
            source = Path(self.submission_source)
            return source.stat().st_mtime if source.exists() else 0
        return 0


class ErrorStateFile:
    def __init__(self, paper_id: str):
        self.paper_id = paper_id

    @property
    def error_state_filename(self):
        # squish "/" in pater ID.
        return os.path.join(ERROR_STATE_DIR, self.paper_id.replace('/', '__'))

    def error_reported(self) -> bool:
        return os.path.exists(self.error_state_filename)

    def report(self):
        if not os.path.exists(self.error_state_filename):
            # touch
            try:
                with open(self.error_state_filename, "w", encoding="utf-8") as fd:
                    fd.write(str(self.paper_id))
            except Exception as exc:
                logger.warning("Report flag file %s is not made with %s", (self.error_state_filename, str(exc)))
                pass

    def clear(self):
        try:
            if os.path.exists(self.error_state_filename):
                os.remove(self.error_state_filename)
        except:
            pass


def submission_message_to_file_state(data: dict, log_extra: dict, ask_webnode: bool = True, cache_upload=True) -> SubmissionFilesState:
    """
    Parse the submission_published message, map it to CIT files and returns the list of files.
    The schema is
    https://console.cloud.google.com/cloudpubsub/schema/detail/submission-publication?project=arxiv-production
    however, this only cares paper_id and version.
    """
    publish_type = data.get('type') # cross | jref | new | rep | wdr
    paper_id = data.get('paper_id')
    version = data.get('version')
    src_ext = data.get('src_ext')
    if src_ext and len(src_ext) > 0 and src_ext[0] != ".":
        src_ext = "." + src_ext
    source_format = data.get('source_format', '')

    logger.info("submission_message_to_file_state: %s.v%s:%s", paper_id, str(version), str(src_ext), extra=log_extra)

    file_state = SubmissionFilesState(paper_id, version, publish_type, src_ext, source_format, log_extra, cache_upload=cache_upload)

    if ask_webnode:
        ask_caches_to_webnode(file_state, log_extra)
    else:
        logger.debug("Not asking web node means, you are not getting PDF or HTML populated.", extra=log_extra)

    return file_state


def ask_caches_to_webnode(file_state: SubmissionFilesState, log_extra: typing.Dict[str, typing.Any]) -> None:
    global WEBNODE_REQUEST_COUNT
    my_tag = WEBNODE_REQUEST_COUNT

    # If asked for PDF, make sure it exits on web node, or else signal NoPDF
    for entry in file_state.get_expected_files():
        if entry["type"] == "pdf-cache":
            # If the submission needs a PDF generated, make sure it exists at CIT
            # If not, raise NoPDF
            pdf_path = Path(entry["cit"])
            if not pdf_path.exists():
                n_webnodes = len(CONCURRENCY_PER_WEBNODE)
                WEBNODE_REQUEST_COUNT = (WEBNODE_REQUEST_COUNT + 1) % n_webnodes
                host, n_para = CONCURRENCY_PER_WEBNODE[min(n_webnodes - 1, max(0, my_tag))]
                protocol = "http" if host.startswith("localhost:") else "https"
                log_extra['webnode'] = host
                log_extra['paper_id'] = file_state.vxid
                try:
                    _pdf_file, _url, _1, _duration_ms = \
                        ensure_pdf(thread_data.session, host, file_state.vxid, timeout=PDF_TIMEOUT(),
                                   protocol=protocol,
                                   source_mtime=file_state.get_submission_mtime())

                except sync_published_to_gcp.WebnodeException as exc:
                    logger.warning("Webnode exception: %s", exc, extra=log_extra)
                    raise MissingGeneratedFile("Failed to generate %s" % pdf_path) from exc

                except ReadTimeout as exc:
                    # This happens when failed to talk to webnode
                    logger.info("Timeout for %s", pdf_path, extra=log_extra)
                    raise MissingGeneratedFile("Failed to retrieve pdf: %s") from exc

                except RetryError as exc:
                    # This happens when failed to talk to webnode
                    logger.info("Retry for %s", pdf_path, extra=log_extra)
                    raise MissingGeneratedFile("Failed to retrieve pdf: %s") from exc

                except Exception as _exc:
                    logger.warning("ensure_pdf: %s - %s", file_state.vxid.ids, str(_exc),
                                   extra=log_extra, exc_info=True, stack_info=False)
                    raise

            if not pdf_path.exists():
                raise MissingGeneratedFile(f"GDF: {file_state.ps_cache_pdf_file} does not exist")
            pass

        if entry["type"] == "html-cache":
            # When the submission is html, web node needs to okay. ensure_html() talks to
            # a web node, and when it gets 200, it returns the list of files in it.
            # The file state (self here) registers files for upload.
            html_path: Path = Path(entry["cit"])
            n_webnodes = len(CONCURRENCY_PER_WEBNODE)
            WEBNODE_REQUEST_COUNT = (WEBNODE_REQUEST_COUNT + 1) % n_webnodes
            host, n_para = CONCURRENCY_PER_WEBNODE[min(n_webnodes - 1, max(0, my_tag))]
            protocol = "http" if host.startswith("localhost:") else "https"
            try:
                html_files, html_root, url, outcome, duration_ms = \
                    ensure_html(thread_data.session, host, file_state.vxid, timeout=HTML_TIMEOUT(),
                                protocol=protocol,
                                source_mtime=file_state.get_submission_mtime())
                logger.info("ensure_html %s / %s: [%1.2f sec] %s (%d) -> %s", file_state.vxid.ids,
                            str(outcome), float(duration_ms) / 1000.0,
                            html_root, len(html_files), url,
                            extra=log_extra)
                file_state.register_files('html-files', html_files)

            except sync_published_to_gcp.WebnodeException as _exc:
                raise MissingGeneratedFile("Failed to generate %s" % html_path) from _exc

            except Exception as _exc:
                logger.warning("ensure_html: %s", file_state.vxid.ids, extra=log_extra,
                               exc_info=True, stack_info=False)
                raise

            if not html_path.exists():
                raise MissingGeneratedFile(f"{file_state.ps_cache_pdf_file} does not exist")
            pass


def decode_message(message: Message) -> typing.Union[dict, None]:
    """Decodes the GCP pub/sub message"""
    log_extra = {"message_id": str(message.message_id), "app": "pubsub-test"}
    try:
        json_str = message.data.decode('utf-8')
    except UnicodeDecodeError:
        logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
        return None

    try:
        data = json.loads(json_str)
    except Exception as _exc:
        logger.warning(f"bad({message.message_id}): {json_str[:1024]}", extra=log_extra)
        return None

    return data


class SyncVerdict:

    def __init__(self) -> None:
        self.verdicts = []

    def add_verdict(self, decision: bool, reason: str, copying: dict) -> None:
        self.verdicts.append((decision, reason, copying))
        pass

    def good(self) -> bool:
        return reduce(lambda result, verdict: result and verdict[0],  self.verdicts, True)

    pass


@STORAGE_RETRY
def list_bucket_objects(gs_client, gcp_path) -> typing.List[str]:
    """
    List the objects in the gcp bucket
    """
    from sync_published_to_gcp import GS_BUCKET
    bucket: Bucket = gs_client.bucket(GS_BUCKET)
    blobs = bucket.list_blobs(prefix=str(gcp_path))
    blob: Blob
    prefix = f'/b/{GS_BUCKET}/o/'
    pl = len(prefix)
    return [ unquote(blob.path[pl:]) for blob in blobs]


@STORAGE_RETRY
def trash_bucket_objects(gs_client, objects: typing.List[str], log_extra: dict):
    """
    Delete the bucket objects.
    """
    from sync_published_to_gcp import GS_BUCKET
    bucket: Bucket = gs_client.bucket(GS_BUCKET)
    for obj in objects:
        blob = bucket.blob(obj)
        logger.debug("%s is being deleted", obj, extra=log_extra)
        blob.delete()
        logger.info("%s is deleted", obj, extra=log_extra)
    return


@STORAGE_RETRY
def retire_bucket_objects(gs_client, objects: typing.List[(str, str, str)], verdict: SyncVerdict, log_extra: dict):
    """
    Retire object - apparently, you have to copy blob
    """
    from sync_published_to_gcp import GS_BUCKET
    bucket: Bucket = gs_client.bucket(GS_BUCKET)
    for from_obj, to_obj, obj_type in objects:
        logger.debug("%s: %s is being renamed to %s", obj_type, from_obj, to_obj, extra=log_extra)
        from_blob: Blob = bucket.blob(from_obj)
        to_blob: Blob = bucket.blob(to_obj)
        if not from_blob.exists():
            logger.warning("%s: FROM %s does not exist", obj_type, from_obj, extra=log_extra)
            if to_blob.exists():
                verdict.add_verdict(True, "Destination Exists", (from_obj, to_blob, obj_type))
            else:
                verdict.add_verdict(True, "None Exists", (from_obj, to_blob, obj_type))
            continue

        if to_blob.exists():
            # When the destination of retired object exists, you do nothing.
            # IOW, You cannot retire object twice.
            to_blob.reload(projection='full')
            if to_blob.md5_hash == from_blob.md5_hash and to_blob.size == from_blob.size:
                # The object is already in the orig, and should not be in /ftp
                from_blob.delete()
                logger.warning("%s: from: %s  <---> to: %s are identical - md5[%s]", obj_type, from_obj, to_obj, from_blob.md5_hash, extra=log_extra)
                verdict.add_verdict(True, "Both Exists", (from_obj, to_blob, obj_type))
            else:
                logger.warning("%s (%s) --> %s exists (NOT COPIED). FROM %s / %s --> TO %s / %s",
                               from_obj,
                               obj_type,
                               to_obj,
                               from_blob.size,
                               from_blob.md5_hash,
                               to_blob.size,
                               to_blob.md5_hash,
                               extra=log_extra)
                verdict.add_verdict(True, "Both exists but contents not the same!", (from_obj, to_blob, obj_type))
            continue

        try:
            copied_blob = bucket.copy_blob(from_blob, bucket, to_obj)
            logger.debug("%s: %s is copied to %s md5:[%s]", obj_type, from_obj, to_obj, copied_blob.md5_hash, extra=log_extra)
            try:
                from_blob.delete()
                verdict.add_verdict(True, "Object moved successfully", (from_obj, to_blob, obj_type))
                logger.info("%s: %s is moved to %s md5:[%s]", obj_type, from_obj, to_obj, copied_blob.md5_hash,
                            extra=log_extra)
            except Exception as _exc:
                verdict.add_verdict(True, "Object moved but source remains", (from_obj, to_blob, obj_type))
                logger.info("%s: %s is moved to %s md5:[%s]", obj_type, from_obj, to_obj, copied_blob.md5_hash,
                            extra=log_extra)
                pass
        except:
            verdict.add_verdict(False, "Object copy failed", (from_obj, to_blob, obj_type))
            logger.warning("%s: %s failed to copy to %s md5:[%s]", obj_type, from_obj, to_obj, copied_blob.md5_hash,
                        extra=log_extra)
            pass

    return


def list_missing_cit_files(file_state: SubmissionFilesState) -> typing.List[str]:
    missing_cit_files = [entry["cit"] for entry in file_state.get_expected_files() if not os.path.exists(entry["cit"])]
    return missing_cit_files


def submission_callback(message: Message) -> None:
    """Pub/sub event handler to upload the submission tarball and .abs files to GCP.

    Since upload() looks at the size of bucket object / CIT file to decide copy or not
    copy, this will attempt to upload the versioned and latest at the same time but the uploading
    may or may not happen.

    """
    # Make sure the message is legible
    data = decode_message(message)
    if data is None:
        message.nack()
        return

    # The action has 5 distinct parts
    # 1 - Plan
    # 2 - Prep
    # 3 - Execution
    # 4 - Verdict
    # 5 - Missing Deadline

    # Plan - Figure out what to copy to GCP

    global WEBNODE_REQUEST_COUNT

    publish_type = data.get('type') # cross | jref | new | rep | wdr
    paper_id = data.get('paper_id')
    version = data.get('version')
    log_extra = {
        "message_id": str(message.message_id), "app": "pubsub", "tag": "%d" % WEBNODE_REQUEST_COUNT,
        "publish_type": str(publish_type), "arxiv_id": str(paper_id), "version": str(version)
    }

    message_age: timedelta = datetime.utcnow().replace(tzinfo=timezone.utc) - message.publish_time
    if not isinstance(message_age, timedelta):
        # sanity check
        raise ValueError

    message_total_seconds = int(message_age.total_seconds())
    message_hours, message_remainder = divmod(message_total_seconds, 3600)
    message_minutes, _ = divmod(message_remainder, 60)
    if message_hours > 0:
        message_age_text = f"{message_hours} hour{'s' if message_hours != 1 else ''}, {message_minutes} minute{'s' if message_minutes != 1 else ''}"
    else:
        message_age_text = f"{message_minutes} minute{'s' if message_minutes != 1 else ''}"

    compilation_timeout = int(os.environ.get("TEX_COMPILATION_TIMEOUT_MINUTES", "720"))
    first_notification_time = int(os.environ.get("TEX_COMPILATION_FAILURE_FIRST_NOTIFICATION_TIME", "90"))

    file_state = submission_message_to_file_state(data, log_extra, ask_webnode=False)
    desired_state = file_state.get_expected_files()
    if not desired_state:
        # No plan? Weird
        logger.warning(f"There is no associated files? xid: {file_state.xid.ids}, mid: {str(message.message_id)}",
                       extra=log_extra)
        message.nack()
        return

    # Prep
    #
    # Now we have the plan. Ask web node to make/prep the caches (PDF and HTML)
    # Ignore the prep error. The status will be captured in the execution verdict
    #
    try:
        ask_caches_to_webnode(file_state, log_extra)

    except MissingGeneratedFile as exc:
        logger.info(str(exc), extra=log_extra)
        pass

    except Exception as _exc:
        logger.warning(
            f"Unknown error xid: {paper_id}, mid: {str(message.message_id)}",
            extra=log_extra, exc_info=True, stack_info=False)

    # Execute
    #  With the plan, copy everything in the file state.
    #  Rather than burf and die, keep going to copy and record the result in the verdict
    verdict = SyncVerdict()
    try:
        sync_to_gcp(file_state, verdict, log_extra)
        logger.info("sync_to_gcp finished: %s", file_state.xid.ids, extra=log_extra)

    except Exception as _exc:
        logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)

    id_v = f"{paper_id}v{version}"
    error_state_file = ErrorStateFile(id_v)

    # Verdict
    #  If good, ack message and we are done.
    if verdict.good():
        error_state_file.clear()
        message.ack()
        logger.info(f"Sync complete.  ack message", extra=log_extra)
        return

    # Report error to slack if it's not there
    if message_age > timedelta(minutes=first_notification_time):
        if not error_state_file.error_reported():
            try:
                missing_files = repr(list_missing_cit_files(file_state))
                id_v_message = "Notification at %s. Following file(s) missing: %s" % (
                    message_age_text, missing_files)

                returncode = subprocess.call(
                    ['/users/e-prints/bin/tex-compilation-problem-notification',
                     id_v, id_v_message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if returncode != 0:
                    logger.warning("Failed to send notification: %s", id_v, extra=log_extra)
            except:
                logger.warning('Slacking for %s did not work', id_v)
                pass
            error_state_file.report()

    # Deadline exceeded?
    if message_age > timedelta(minutes=compilation_timeout):
        try:
            missing_files = repr(list_missing_cit_files(file_state))
            id_v_message = "Notification at %s. Following file(s) missing: %s" % (
                message_age_text, missing_files)
            returncode = subprocess.call(
                ['/users/e-prints/bin/tex-compilation-problem-notification',
                 id_v, id_v_message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if returncode != 0:
                logger.error("Failed to send notification: %s", id_v, extra=log_extra)
        except:
            logger.error('Slacking for %s did not work', id_v)
            pass

        help_needed = os.environ.get("TEX_COMPILATION_RECIPIENT", "help@arxiv.org")
        subject = f"Uploading of {paper_id}v{version} failed"
        mail_body = f"Hello EUST,\nSubmission uploading for {paper_id}v{version} has failed. Please resolve the issue.\n\nThis message is generated by a bot on arxiv-sync.serverfarm.cornell.edu.\n"
        SENDER = os.environ.get("SENDER", "developers@arxiv.org")
        SMTP_SERVER = os.environ.get("SMTP_SERVER", "mail.arxiv.org")
        SMTP_PORT = os.environ.get("SMTP_PORT", "25")
        cmd = ["/usr/local/bin/arxiv-mail",
               "-t", help_needed,
               "-f", SENDER,
               "-m", SMTP_SERVER,
               "-p", SMTP_PORT,
               "-s", subject,
               ]
        # using sendmail
        # cmd = ["/usr/bin/mail", "-r", "developers@arxiv.org", "-s", subject, help_needed]

        mail = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            mail.communicate(mail_body.encode('utf-8'), timeout=60)
            if mail.returncode == 0:
                # Once the email message is sent, done here.
                error_state_file.clear()
                message.ack()
                logger.warning(f"Alart mail sent: {subject}", extra=log_extra)
                return
            else:
                logger.error("Failed to send mail: %s", shlex.join(cmd), extra=log_extra)
        except Exception as exc:
            logger.error(f"Failed: %s", shlex.join(cmd), extra=log_extra, exc_info=True)
            pass

    # Did not complete the sync. Nack and retry later.
    message.nack()
    return


def sync_to_gcp(state: SubmissionFilesState, verdict: SyncVerdict, log_extra: dict) -> None:
    """
    From the submission file state, copy the ones that should bu uploaded.
    When you come here, PDF/HTML files are already made. (by ask_caches_to_webnode)

    If the /ftp's submission contains extra files, they are removed.
    """
    gs_client = thread_data.storage
    desired_state = state.get_expected_files()
    xid = state.xid
    log_extra["arxiv_id"] = xid.ids
    logger.info("sync_to_gcp: Processing %s", xid.idv, extra=log_extra)

    # Are all the ducks in place? (except obsolete ones.)
    for entry in desired_state:
        if entry["status"] == "obsolete":
            continue
        local = entry["cit"]
        local_path = Path(local)
        if not local_path.exists():
            return verdict.add_verdict(False, "Missing file", entry)

    # Existing blobs on GCP
    cit_source_root_path = state.source_path("")
    bucket_objects: typing.List[str] = \
        list_bucket_objects(gs_client, path_to_bucket_key(cit_source_root_path))

    # Obsolete blobs are moved to /orig first
    retired = []
    for entry in desired_state:
        if entry["status"] != "obsolete":
            continue
        obsoleted = entry["obsoleted"]
        original = entry["original"]
        entry_type = entry['type']
        retired.append((obsoleted, original, entry_type))

    if retired:
        # Move blobs from /ftp to /orig
        retire_bucket_objects(gs_client, retired, verdict, log_extra)
        # Obsoleted objects are gone
        for obsoleted, _original, _entry_type in retired:
            if obsoleted in bucket_objects:
                bucket_objects.remove(obsoleted)

    # Objects synced to GCP
    for entry in desired_state:
        if entry["status"] == "obsolete":
            continue

        local = entry["cit"]
        remote = entry["gcp"]
        entry_type = entry['type']

        if entry_type == "html-cache":
            # "html-cache" is needed on CIT as it is the root dir of HTML submission, but
            # it is NOT a bucket object, and nothing to upload. Subsequent object copy becomes
            # effectively creating the "directory" on GCP.
            logger.debug("Skipping [%s]: %s -> %s", entry_type, local, remote, extra=log_extra)
            continue

        logger.info("uploading [%s]: %s -> %s", entry_type, local, remote, extra=log_extra)
        local_path = Path(local)
        if local_path.exists() and local_path.is_file():
            upload(gs_client, local_path, remote, upload_logger=logger)
            verdict.add_verdict(True, "Uploaded", entry)
        else:
            verdict.add_verdict(False, "No local file to copy", entry)
            logger.warning("No local file for uploading [%s]: %s -> %s",
                           entry_type, local, remote, extra=log_extra)

        # Uploaded files are good ones. Subtract the valid one from the bucket objects
        if remote in bucket_objects:
            bucket_objects.remove(remote)

    # If extra exists, they are removed.
    if bucket_objects:
        # If the obsoleting is working correctly, this warning should not trigger.
        # It may be a good idea to tie this to paging
        for gcp_obj in bucket_objects:
           logger.warning("Extra bucket object %s. You should rename/remove it",
                          gcp_obj, extra=log_extra)


def test_callback(message: Message) -> None:
    """Stand in callback to handle the pub/sub message. gets used for --test."""
    data = decode_message(message)
    if data is None:
        message.nack()
        return

    log_extra = {"message_id": str(message.message_id), "app": "pubsub-test"}
    state = submission_message_to_file_state(data, log_extra)
    logger.debug(state.xid.ids)
    sync = state.get_expected_files()
    for entry in sync:
        logger.debug(f'{entry["cit"]} -> {entry["gcp"]}')
    message.nack()
    sys.exit(0)


running = True

def signal_handler(_signal: int, _frame: typing.Any):
    """Graceful shutdown request"""
    global running
    running = False

# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def submission_pull_messages(project_id: str, subscription_id: str, test: bool = False) -> None:
    """
    Create a subscriber client and pull messages from a Pub/Sub subscription.

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        test (bool): Test - get one message, print it, nack, and exit
    """
    subscriber_client = SubscriberClient()
    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    callback = test_callback if test else submission_callback
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=callback)
    log_extra = {"app": "pubsub"}
    logger.info("Starting %s %s", project_id, subscription_id, extra=log_extra)
    with subscriber_client:
        try:
            while running:
                sleep(0.2)
            streaming_pull_future.cancel()  # Trigger the shutdown
            streaming_pull_future.result(timeout=30)  # Block until the shutdown is complete
        except TimeoutError:
            logger.info("Timeout")
            streaming_pull_future.cancel()
        except Exception as e:
            logger.error("Subscribe failed: %s", str(e), exc_info=True, extra=log_extra)
            streaming_pull_future.cancel()
    logger.info("Exiting", extra=log_extra)


if __name__ == "__main__":
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project',
                    help='GCP project name. Default is arxiv-production',
                    dest="project", default="arxiv-production")
    ad.add_argument('--topic',
                    help='GCP pub/sub name. The default matches with arxiv-production',
                    dest="topic", default="submission-published")
    ad.add_argument('--subscription',
                    help='Subscription name. Default is the one in production', dest="subscription",
                    default="sync-submission-from-cit-to-gcp")
    ad.add_argument('--json-log-dir',
                    help='JSON logging directory. The default is correct on the sync-node',
                    default='/var/log/e-prints')
    ad.add_argument('--debug', help='Set logging to debug. Does not invoke testing',
                    action='store_true')
    ad.add_argument('--test', help='Test reading the queue but not do anything',
                    action='store_true')
    ad.add_argument('--bucket',
                    help='The bucket name. The default is mentioned in sync_published_to_gcp so for the production, you do not need to provide this - IOW it automatically uses the same bucket as sync-to-gcp',
                    dest="bucket", default="")
    args = ad.parse_args()

    project_id = args.project
    subscription_id = args.subscription

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "submissions.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.debug else logging.INFO)
        logger.addHandler(json_logHandler)
        pass

    # Ensure the environment is authenticated
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        logger.error("Environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is not set.")
        sys.exit(1)
    if args.bucket:
        import sync_published_to_gcp
        sync_published_to_gcp.GS_BUCKET = args.bucket

    from sync_published_to_gcp import GS_BUCKET
    logger.info("GCP bucket %s", GS_BUCKET)
    submission_pull_messages(project_id, subscription_id, test=args.test)
