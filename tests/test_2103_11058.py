def test_2103_11058(client_with_test_fs):
    rv = client_with_test_fs.get('/abs/2103.11058')
    assert rv.status_code == 200
