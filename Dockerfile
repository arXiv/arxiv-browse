# arxiv/browse
#
# Defines the runtime for the arXiv browse service, which provides the main
# UIs for browse.
FROM python:3.8-buster
ARG git_commit

WORKDIR /opt/arxiv

# add python application and configuration
ADD app.py /opt/arxiv/
ADD pyproject.toml /opt/arxiv/
ADD poetry.lock /opt/arxiv/

ENV VIRTUAL_ENV=/opt/arxiv/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install -U pip poetry
RUN poetry install --no-root

ENV PATH "/opt/arxiv:${PATH}"

ADD browse /opt/arxiv/browse
ADD tests /opt/arxiv/tests
ADD wsgi.py uwsgi.ini /opt/arxiv/
ADD bin/start_browse.sh /opt/arxiv/

RUN chmod +x /opt/arxiv/start_browse.sh
RUN echo $git_commit > /git-commit.txt

ENV LC_ALL en_US.utf8
ENV LANG en_US.utf8
ENV LOGLEVEL 40
ENV FLASK_DEBUG 1
ENV FLASK_APP /opt/arxiv/app.py

EXPOSE 8000
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
