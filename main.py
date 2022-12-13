"""Simple file to run flask app.

Run as `python main.py`"""
import os

from arxiv.dissemination import app

if __name__ == "__main__":
    os.environ['TRACE']='0' # Turns off logging and trace to GCP
    app.run(debug=True)
