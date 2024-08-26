# arxiv/browse
#
# Defines the runtime for the arXiv browse service, which provides the main
# UIs for browse.

FROM python:3.11.8-bookworm

# Do not update+upgrade. The base image is kept up to date.  Also destroys
# ability to cache.

ARG git_commit

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.3.2 \
    LC_ALL=en_US.utf8 \
    LANG=en_US.utf8

WORKDIR /app

RUN apt-get -y install default-libmysqlclient-dev

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="/app:$VIRTUAL_ENV/bin:$PATH"
RUN pip install -U pip "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi \
    --without dev

ADD browse /app/browse
ADD wsgi.py /app/

RUN echo $git_commit > /git-commit.txt

EXPOSE 8080
ENV LOGLEVEL 40

RUN useradd e-prints
USER e-prints

# Why is this command in an env var and not just run in CMD?  So it can be used
# to start a docker instance during an integration test. See
# cicd/cloudbuild-master-pr.yaml for how it is used

ENV GUNICORN gunicorn --bind :8080 \
    --workers 4 --threads 8 --timeout 0 \
     "browse.factory:create_web_app()"

CMD exec $GUNICORN
