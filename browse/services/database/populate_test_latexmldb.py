from typing import Optional
from browse.services.database.models import db, DBLaTeXMLDocuments
from arxiv.base import logging

logger = logging.getLogger(__name__)

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
    'paper_id': '2303.00763',
    'document_version': 1,
    'conversion_status': 1,
    'latexml_version': 'test_latexml_version',
    'tex_checksum': 'test_checksum',
    'conversion_start_time': 0,
    'conversion_end_time': 1
}

doc3 = {
    'paper_id': '0704.0526',
    'document_version': 1,
    'conversion_status': 1,
    'latexml_version': 'test_latexml_version',
    'tex_checksum': 'test_checksum',
    'conversion_start_time': 0,
    'conversion_end_time': 1
}

def _insert_latexml_doc (
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

def populate_test_latexmldb ():
    logger.warning('CREATING LATEXML TABLES')
    db.create_all('latexml')
    _insert_latexml_doc(**doc1)
    _insert_latexml_doc(**doc2)
    _insert_latexml_doc(**doc3)

