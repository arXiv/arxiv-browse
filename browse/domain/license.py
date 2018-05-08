"""Representations of the license on a document metadata."""
from typing import Optional
from dataclasses import dataclass, field

"""Assumed license from 1991-2003, but also used after 2003. """
ASSUMED_LICENSE_URI = 'http://arxiv.org/licenses/assumed-1991-2003/'


def licenseForRecoredLicense(recorded_uri: Optional[str]) -> str:
    """Get the license for a license recorded in an abs file

    This represents an important encoding of policy in code:

    The submitters of articles between 1991 and 2003 aggreed to the
    assumed license. These have no license in the abs files becasue
    the authors could only submit papers if they accepted this
    license.

    After the submission system in Perl and catalyst was put into
    production, the author selected from several licenses. If the
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
    explicitly written to not premit submitters to submit without
    selecting a license.

    """

    if recorded_uri is None:
        return ASSUMED_LICENSE_URI
    else:
        if not isinstance(recorded_uri, str):
            raise TypeError("Licnese recorded_uri must be str or None")
        else:
            return recorded_uri


@dataclass
class License(object):
    """Represents an arXiv article license."""

    """URI of a license if one is in the article record."""
    recorded_uri: Optional[str] = field()

    """License that is in effect.

    When the submitter uploaded this paper to arXiv, they agreed to
    arXiv using the paper under the terms of this license. This takes
    into account assumed license."""
    effectiveLicenseUri: str = field(init=False)

    def __post_init__(self) -> None:
        self.effectiveLicenseUri = licenseForRecoredLicense(
            self.recorded_uri)

#     # TODO: need licenses?
#     # TODO: needs to be moved to common libraries
#     # TODO: need validation?
#     # TODO: the License class would be the best place to put knowledge
#     # about any un-obivious behavior of the licenses. Ex. Licenses before YYYY
#     # are the assumed-1991-2003 license

#     # TODO Maybe make a class like Licenses to encode what licenses can
#     # be used in arXiv. when licenses were the default, what license
#     # was the default during some time period so a abs without a specified
#     # license can be assigned the default for that time period.
