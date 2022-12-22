"""Simple file to run flask app.

Run as `python main.py`"""
import os


if __name__ == "__main__":
    os.environ['TRACE']='0' # Turns off logging and trace to GCP
    from arxiv_dissemination import app
    app.run(debug=True, port=8080)
