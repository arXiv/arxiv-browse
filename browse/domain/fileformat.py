"""Format for use with an ItemSource"""
"""
tar.gz, gzipped postscript, gzipped html, a single PDF
        file, a gzip that is not tarred, a single dox file, a single odt file.
"""

from typing import Optional


class FileFormat():
    def __init__(self, id:str, content_encoding:Optional[str], content_type:str)->None:
        self.id = id
        self.content_encoding = content_encoding
        self.content_type = content_type


targz = FileFormat("targz", "x-gzip", "application/x-eprint-tar")
psgz = FileFormat("psgz", "x-gzip", "application/postscript")
dvigz = FileFormat("psgz", "x-gzip", "application/x-dvi")
htmlgz = FileFormat("htmlgz", "x-gzip", "text/html")
pdf = FileFormat("pdf", None, "application/pdf")
ps = FileFormat("ps", None, "application/postscript")
gz = FileFormat("gz", "x-gzip", "application/x-eprint")
docx = FileFormat("docx", "TODO", "TODO")
odf = FileFormat("odf", "TODO", "TODO")

fromats = {
    "targz":targz,
    "psgz":psgz,
    "htmlgz":htmlgz,
    "pdf":pdf,
    "gz":gz,
    "docx":docx,
    "odf":odf,
    }
