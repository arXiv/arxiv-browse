"""Simple file to run arxiv-browse in debug mode.

Run as `python main.py`"""
import os
from browse.factory import create_web_app

if __name__ == "__main__":
    os.environ['TEMPLATES_AUTO_RELOAD'] = "1"
    os.environ['DEBUG'] = "1"
    app = create_web_app()
    if os.environ.get('PROFILE', False):
        from werkzeug.middleware.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir="./profs")
        print("WARNING: Profiling, will be slower. Writing to ./profs ")
    app.run(debug=True, port=8080)
