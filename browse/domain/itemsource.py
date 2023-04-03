"""Domain object for source of an item."""

from .fileformat import FileFormat

# TODO should this be refactored for both src and pdfs?

class ItemSource():
    """Represents source blob for an item."""

    #TODO Make this a context manager that can be opened?

    @property
    def format(self)-> FileFormat:
        pass
