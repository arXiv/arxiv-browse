from typing import Optional
from flask_sqlalchemy import SQLAlchemy

from .models import DBLaTeXMLDocuments

doc1 = {
    'paper_id': '2012.02205',
    'document_version': 1,
    'conversion_status': 1,
    'latexml_version': 'test_latexml_version',
    'tex_checksum': 'test_checksum',
    'conversion_start_time': 0,
    'conversion_end_time': 1
}

doc2 = {
    'paper_id': '2306.00022',
    'document_version': 1,
    'conversion_status': 1,
    'latexml_version': 'test_latexml_version',
    'tex_checksum': 'test_checksum',
    'conversion_start_time': 0,
    'conversion_end_time': 1
}

def _insert_latexml_doc (db: SQLAlchemy,
    paper_id: int, document_version: int,
    conversion_status: int, latexml_version: str, 
    tex_checksum: str, conversion_start_time: int,
    conversion_end_time: Optional[int] = None) -> bool:
        
    db.session.add(
        DBLaTeXMLDocuments(
            paper_id=paper_id,
            document_version=document_version,
            conversion_status=conversion_status,
            latexml_version=latexml_version,
            tex_checksum=tex_checksum,
            conversion_start_time=conversion_start_time,
            conversion_end_time=conversion_end_time
        )
    )
    db.session.commit()

def populate_test_latexmldb (db: SQLAlchemy):
    db.create_all()
    _insert_latexml_doc(db, **doc1)
    _insert_latexml_doc(db, **doc2)
