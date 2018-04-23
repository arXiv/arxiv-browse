# arxiv-browse

### Flask dev server

You can run the browse app directly. Using virtualenv:

```bash
virtualenv ~/.venv/arxiv-browse
source ~/.venv/arxiv-browse/bin/activate
cd /path/to/arxiv-browse
pip install -r requirements/dev.txt
FLASK_APP=app.py FLASK_DEBUG=1 flask run
```

This will monitor for any changes to the Python code and restart the server.
Unfortunately static files and templates are not monitored, so you'll have to
manually restart to see those changes take effect.

If all goes well, http://127.0.0.1:5000/ should render the basic abs page
