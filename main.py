"""Simple file to run flask app.

Run as `python main.py`"""
from browse.factory import create_web_app


if __name__ == "__main__":
    app = create_web_app()
    app.run(debug=True, port=8080)
