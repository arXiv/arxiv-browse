FROM python:3.10-slim

ARG git_commit

ENV YOUR_ENV=${YOUR_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    TRACE=1

RUN pip install "gunicorn==20.1.0"
RUN pip install "poetry==$POETRY_VERSION"

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

COPY . ./

RUN echo $git_commit > ./git-commit.txt

EXPOSE 8080

# Why is this command in an env var and not just run in CMD?
# So it can be used to start the server during an integration test.
# See cicd/cloudbuild-master-pr.yaml for how it is used
ENV GUNICORN gunicorn --bind :8080 \
    --workers 1 --threads 8 --timeout 0 \
     "arxiv_dissemination.app:factory()"

CMD exec $GUNICORN
