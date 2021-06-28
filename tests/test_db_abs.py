
def test_should_be_db_abs(dbclient):
    from browse.services.documents import db_docs, get_doc_service
    assert dbclient and dbclient.application.config['DOCUMENT_ABSTRACT_SERVICE'] == db_docs

    assert 'db_abs' in str(get_doc_service())
    
def test_basic_db_abs(dbclient):
    rt = dbclient.get('/abs/0906.2112')
    assert rt.status_code == 200
    assert rt.headers.get('Expires')
