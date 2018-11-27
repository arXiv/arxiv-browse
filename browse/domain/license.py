"""Representations of the license on a document metadata."""
from typing import Optional
from dataclasses import dataclass, field

from arxiv.license import ASSUMED_LICENSE_URI, LICENSES


def license_for_recorded_license(recorded_uri: Optional[str]) -> str:
    """Get the license for the value recorded in the abs file.

    This represents an important encoding of policy in code:

    The submitters of articles between 1991 and 2003 aggreed to the
    assumed license. These have no license in the abs files becasue
    the authors could only submit papers if they accepted this
    license.

    After the submission system in Perl and catalyst was put into
    production 2009, the author selected from several licenses. If the
    author selected the arXiv assumed license, the abs file would have
    no license field. If the author selected a license other than the
    assumed license, it would be recorded in the .abs file in the
    field license. If the author did not select a license or sent an
    unexpected request they were shown the license page with an error
    message that they needed to select a license. It was designed to
    make it impossible for a submittion to be accepted without a
    license.  Submissions via the SWORD system required users to
    record a license for all their submissions as part of their user
    account data.

    A lack of a license in arXiv's records did not mean the author
    failed to select a license. The classic submission system was
    explicitly written to not permit submitters to submit without
    selecting a license.

    """
    if recorded_uri is None:
        return str(ASSUMED_LICENSE_URI)

    if not isinstance(recorded_uri, str):
        raise TypeError(
            "License recorded_uri must be str or None, but it was "
            f"{type(recorded_uri).__name__}")
    else:
        return recorded_uri


@dataclass
class License:
    """Represents an arXiv article license."""

    recorded_uri: Optional[str] = None
    """URI of a license if one is in the article record."""

    effective_uri: str = field(init=False)
    """
    License that is in effect.

    When the submitter uploaded this paper to arXiv, they agreed to
    arXiv using the paper under the terms of this license. This takes
    into account assumed license.
    """

    icon_uri_path: Optional[str] = field(init=False)
    """Path to license icon."""

    label: Optional[str] = field(init=False)
    """The license label."""

    def __post_init__(self) -> None:
        """Set the effective license URI."""
        self.effective_uri = license_for_recorded_license(
            self.recorded_uri)
        self.icon_uri_path = None
        self.label = None
        if self.effective_uri in LICENSES:
            if 'icon_uri' in LICENSES[self.effective_uri]:
                self.icon_uri_path = LICENSES[self.effective_uri]['icon_uri']
            if 'label' in LICENSES[self.effective_uri]:
                self.label = LICENSES[self.effective_uri]['label']
