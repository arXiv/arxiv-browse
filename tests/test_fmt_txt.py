import pytest


def test_fmt_txt_2112(dbclient, client_with_test_fs):
        """Test abs/nnn?fmt=txt."""
        fsclient = client_with_test_fs
        # db lacks jref in the data
        # and we want to use UTC not GMT going forward
        assert fsclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8').replace(" GMT ", " UTC ")\
            .replace("Journal-ref: Transactions of the AMS 363 (2011), 4263--4283\n","") == \
            dbclient.get('/abs/0906.2112?fmt=txt').data.decode('utf-8').replace(" 14G40;", " 14G40,")


def test_fmt_txt_5132(dbclient, client_with_test_fs):
    """Test abs/nnn?fmt=txt."""
    fsclient = client_with_test_fs
    assert fsclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8').replace(" GMT ", " UTC ") == \
           dbclient.get('/abs/0906.5132?fmt=txt').data.decode('utf-8')
