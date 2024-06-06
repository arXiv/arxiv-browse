import pytest
import requests_mock
from unittest.mock import patch

GENPDF_API_URL = "https://api.example.com"
GENPDF_SERVICE_URL = "https://service.example.com"

@pytest.fixture(scope="function")
def client_and_mock(app_with_test_fs):
    with requests_mock.Mocker() as req_m:
        app_with_test_fs.config["GENPDF_API_URL"] = GENPDF_API_URL
        app_with_test_fs.config["GENPDF_SERVICE_URL"] = GENPDF_SERVICE_URL
        with patch("browse.services.dissemination.article_store.GcpIdentityToken") as gcptoken:
            gcptoken.token.return_value = "mocked-20adk2349"
            with app_with_test_fs.app_context():
                yield (app_with_test_fs.test_client(), req_m)

def test_basic_genpdf(client_and_mock):
    client, req_mock = client_and_mock


    req_mock.get(f"{GENPDF_API_URL}/pdf/0704.0002v1",
                 status_code=302,
                 headers={"location": "gs://fakebucket/fake.pdf"},
                 )

    resp = client.get("/pdf/0704.0002v1")
    assert resp.status_code == 200
