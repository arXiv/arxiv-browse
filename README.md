# Dissemination for arXiv

A Service to download PDFs and other article formats from a GCP
storage bucket.

# Install and run

    git clone git@github.com:arXiv/dissemination.git
    cd dissemination
    python3.10 -m venv ./venv  # or use pyenv or poetry
    source ./venv/bin/activate
    poetry install --sync
    export GOOGLE_APPLICATION_CREDENTIALS=~/{your_cred_json_file}
    python main.py

    # open in browser: http://localhost:5000/pdf/1105.0010v3.pdf

# Run locally in docker

    GOOGLE_APPLICATION_CREDENTIALS=~/Download/{your_gcp_cred_file}
    DIS_PORT=5000
    GIT_V=$(git rev-parse --short HEAD)
    
    docker build . --build-arg git_commit=${GIT_V} -t arxiv/dissemination:$GIT_V

    docker run \
        -p $DIS_PORT:$DIS_PORT -e PORT=$DIS_PORT \
        -e TRACE=0 \
        -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
        -v $GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro \
        arxiv/dissemination:$GIT_V

    # open in browser: http://localhost:5000/pdf/1105.0010v3.pdf
# To run tests
Test were simplified to use fixtures for a test db. Running the tests
is just:

    pytest

