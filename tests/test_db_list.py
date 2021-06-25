
# There's something wrong with this it because it causes
# other tests to fail.
# I think it has to do with the app getting loaded only once
# and then getting reused during the run of all the tests.

def test_basic_db_lists(dbclient):
    rv = dbclient.get('/list/hep-ph/1102')
    assert rv.status_code == 200
    assert rv.headers.get('Expires', None)

