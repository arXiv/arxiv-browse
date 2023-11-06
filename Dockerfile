# arxiv/browse
#
# Defines the runtime for the arXiv browse service, which provides the main
# UIs for browse.

FROM python:3.10.8-buster
RUN apt-get update && apt-get -y upgrade

ARG git_commit


ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    TRACE=1 \
    LC_ALL=en_US.utf8 \
    LANG=en_US.utf8 \
    APP_HOME=/app

WORKDIR /app


RUN apt-get -y install default-libmysqlclient-dev

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -U pip "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

RUN pip install "gunicorn==20.1.0"

ADD app.py /app/

ENV PATH "/app:${PATH}"

ADD browse /app/browse
ADD tests /app/tests
ADD wsgi.py /app/

RUN echo $git_commit > /git-commit.txt

EXPOSE 8080
ENV LC_ALL en_US.utf8
ENV LANG en_US.utf8
ENV LOGLEVEL 40
ENV FLASK_DEBUG 1
ENV FLASK_APP /opt/arxiv/app.py

RUN useradd e-prints
RUN chown e-prints:e-prints /app/tests/data/
RUN chmod 775 /app/tests/data/
USER e-prints

# Why is this command in an env var and not just run in CMD?  So it can be used
# to start a docker instance during an integration test. See
# cicd/cloudbuild-master-pr.yaml for how it is used

ENV GUNICORN gunicorn --bind :8080 \
    --workers 1 --threads 8 --timeout 0 \
     "browse.factory:create_web_app()"

CMD exec $GUNICORN