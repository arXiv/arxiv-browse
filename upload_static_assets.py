"""Use this to upload static content to S3."""

import flask_s3

from browse.factory import create_web_app


app = create_web_app()

# TODO: need a better way to exclude sass directories at every level
flask_s3.create_all(app, filepath_filter_regex=r'(css|images|js)')
