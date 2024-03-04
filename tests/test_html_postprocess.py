from browse.services.html_processing import post_process_html
def test_post_process_html_basic(app_with_test_fs):
    """Test the post_process_html()."""
    with app_with_test_fs.app_context():
        assert post_process_html(b"") == b""
        html = b"<body><h1>YES!</h1><p>some thing or other.</p>"
        assert post_process_html(html) == html

def test_post_process_html(app_with_test_fs):
    """Test the post_process_html()."""

    with app_with_test_fs.test_request_context():
        # Now this context it is as if it is running in a flask app
        # setup with tests/data/abs_files as the abs files
        pphtml = post_process_html(b"LIST:0705.0001")
        assert b"/abs/0705.0001" in pphtml
        assert b"""[<a href="/pdf/0705.0001" title="Download PDF" id="pdf-0705.0001" aria-labelledby="pdf-0705.0001">pdf</a>, <a href="/ps/0705.0001" title="Download PostScript" id="ps-0705.0001" aria-labelledby="ps-0705.0001">ps</a>, <a href="/format/0705.0001" title="Other formats" id="oth-0705.0001" aria-labelledby="oth-0705.0001">other</a>]\n""" \
               in pphtml
