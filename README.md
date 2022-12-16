# Dissemination for arXiv

A Service to download PDFs and other article formats from a GCP
storage bucket.

# Install and run

```

git clone git@github.com:arXiv/dissemination.git
cd dissemination
python3.10 -m venv ./venv  # or use pyenv or poetry
source ./venv/bin/activate
poetry install --sync
export GOOGLE_APPLICATION_CREDENTIALS=~/{your_cred_json_file}
python main.py

# open in browser: http://localhost:5000/pdf/1105.0010v3.pdf

```

# Run locally in docker

```

export GOOGLE_APPLICATION_CREDENTIALS=~/Downloads/{your_cred_file}
export GIT_V=$(git rev-parse --short HEAD)

docker build . --build-arg git_commit=${GIT_V} -t arxiv/dissemination:$GIT_V

docker run \
    -p 8080:8080 \
    -e TRACE=0 \
    -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
    -v $GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro \
    arxiv/dissemination:$GIT_V

# open in browser: http://localhost:8080/pdf/1105.0010v3.pdf
# or run integration tests with
# pytest --runintegration
```

# To run tests
To run the unit tests:
```
pytest --cov=arxiv_dissemination
```

To run integration tests against localhost:8080:
```
# first start docker as described in 'Run locally in docker'
# then run
pytest --runintegration
```

To run integration tests against downloads.arxiv.org:
```
HOST=https://download.arxiv.org pytest --runintegration
```
