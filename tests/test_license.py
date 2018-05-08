from unittest import TestCase
from browse.domain.license import ASSUMED_LICENSE_URI


class TestLicense(TestCase):
    def test_new_license(self):
        from browse.domain.license import License

        r_uri = 'http://bogus/license/uri'
        lic = License(r_uri)
        assert lic is not None
        assert lic.recorded_uri == r_uri
        assert lic.effectiveLicenseUri == r_uri

        lic = License(None)
        assert lic is not None
        assert lic.recorded_uri is None
        assert lic.effectiveLicenseUri == ASSUMED_LICENSE_URI

        with self.assertRaises(TypeError):
            lic = License(23)
