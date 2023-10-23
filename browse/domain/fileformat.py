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

    def __repr__(self) -> str:
        return self.id



targz = FileFormat("targz", "x-gzip", "application/x-eprint-tar")
tex = FileFormat("tex", "x-gzip",  "application/x-eprint-tar")
psgz = FileFormat("psgz", "x-gzip", "application/postscript")
dvigz = FileFormat("psgz", "x-gzip", "application/x-dvi")
htmlgz = FileFormat("htmlgz", "x-gzip", "text/html")
pdf = FileFormat("pdf", None, "application/pdf")
pdftex = FileFormat("pdftex", "x-gzip", "application/x-eprint-tar")
ps = FileFormat("ps", None, "application/postscript")
gz = FileFormat("gz", "x-gzip", "application/x-eprint")
docx = FileFormat("docx", "TODO", "TODO")
odf = FileFormat("odf", "TODO", "TODO")
html_source=FileFormat("html_source","x-gzip", "text/html or application/x-eprint-tar")

formats = {
    "targz": targz,
    "tex": tex,
    "psgz": psgz,
    "htmlgz": htmlgz,
    "pdf": pdf,
    "pdftex": pdftex,
    "gz": gz,
    "docx": docx,
    "odf": odf,
    "html_source":html_source
    }
