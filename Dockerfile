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
    LC_ALL=en_US.utf8 \
    LANG=en_US.utf8

WORKDIR /app

RUN apt-get -y install default-libmysqlclient-dev

COPY README.md uv.lock pyproject.toml ./

ADD app.py /app/

ADD browse /app/browse
ADD wsgi.py /app/

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -U pip uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-dev

RUN echo $git_commit > /git-commit.txt

ENV PATH "/app:${PATH}"

EXPOSE 8080
ENV LOGLEVEL 40

RUN useradd e-prints
USER e-prints

# Why is this command in an env var and not just run in CMD?  So it can be used
# to start a docker instance during an integration test. See
# cicd/cloudbuild-master-pr.yaml for how it is used

ENV GUNICORN gunicorn --bind :8080 \
    --workers 5 --threads 10 --timeout 0 \
     "browse.factory:create_web_app()"

CMD exec $GUNICORN
