"""Class that represents a single category."""

from typing import Union, List
from dataclasses import dataclass, field

from arxiv import taxonomy


@dataclass(eq=True, order=True)
class Category:
    """Represents an arXiv category.

    arXiv categories are arranged in a hierarchy where there are archives
    (astro-ph, cs, math, etc.) that contain subject classes (astro-ph has
    subject classes CO, GA, etc.). We now use the term category to refer
    to any archive or archive.subject_class that one can submit to (so
    hep-th and math.IT are both categories). No subject class can be in
    more than one archive. However, our scientific advisors identify some
    categories that should appear in more than one archive because they
    bridge major subject areas. Examples include math.MP == math-ph and
    stat.TH = math.ST. These are called category aliases and the idea is
    that any article classified in one of the aliases categories also appears
    in the other (canonical), but that most of the arXiv code for display,
    search, etc. does not need to understand the break with hierarchy.
    """

    id: str = field(compare=True)
    """The category identifier (e.g. cs.DL)."""

    name: str = field(init=False, compare=False)
    """The name of the category (e.g. Digital Libraries)."""

    #TODO should probably be changed to get_canonical to avoid confusion
    canonical: Union['Category', None] = field(init=False, compare=False)

    def __hash__(self)->int:
        """Hash."""
        return id.__hash__()

    def __post_init__(self) -> None:
        """Get the full category name."""
        if self.id in taxonomy.definitions.CATEGORIES:
            self.name = taxonomy.definitions.CATEGORIES[self.id]['name']

        if self.id in taxonomy.definitions.ARCHIVES_SUBSUMED:
            self.canonical = Category(id=taxonomy.definitions.ARCHIVES_SUBSUMED[self.id])
        else:
            self.canonical = None

    def unalias(self) -> 'Category':
        """Follow any EQUIV or SUBSUMED to get the current category."""
        if self.id in taxonomy.definitions.CATEGORY_ALIASES:
            return Category(taxonomy.definitions.CATEGORY_ALIASES[self.id])
        if self.id in taxonomy.definitions.ARCHIVES_SUBSUMED:
            return Category(taxonomy.definitions.ARCHIVES_SUBSUMED[self.id])
        return self

    def display_str(self)->str:
        """String to use in display of a category.

        Ex:
        Earth and Planetary Astrophysics (astro-ph.EP)
        """
        if self.id in taxonomy.definitions.CATEGORIES:
            catname = taxonomy.definitions.CATEGORIES[self.id]['name']
            return f'{catname} ({self.id})'
        sp = _split_cat_str(self.id)
        hassub = len(sp) == 2
        if hassub:
            (arc, _) = sp
            if arc in taxonomy.definitions.ARCHIVES:
                arcname = taxonomy.definitions.ARCHIVES[arc]['name']
                return f'{arcname} ({self.id})'
            else:
                return self.id
        else:
            return self.id


def _split_cat_str(cat: str)-> List[str]:
    return cat.split('.', 2)
