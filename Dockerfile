# arxiv/browse
#
# Defines the runtime for the arXiv browse service, which provides the main
# UIs for browse.

# FROM arxiv/base:0.16.7
FROM python:3.6-slim as compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends mysql-devel



# remove conflicting mariadb-libs from arxiv/base
# RUN yum remove -y mariadb-libs



# install MySQL
#RUN yum install -y which mysql mysql-devel
RUN pip install uwsgi

# add python application and configuration
ADD app.py /opt/arxiv/
ADD Pipfile /opt/arxiv/
ADD Pipfile.lock /opt/arxiv/
RUN pip install -U pip pipenv
RUN pipenv sync

########## STAGE 2 ##############
FROM python:3.6-slim as build-image
ARG git_commit

ENV PATH "/opt/arxiv:${PATH}"
ENV LC_ALL en_US.utf8
ENV LANG en_US.utf8
ENV LOGLEVEL 40
ENV FLASK_DEBUG 1
ENV FLASK_APP /opt/arxiv/app.py

WORKDIR /opt/arxiv

ADD browse /opt/arxiv/browse
ADD tests /opt/arxiv/tests
ADD wsgi.py uwsgi.ini /opt/arxiv/
ADD bin/start_browse.sh /opt/arxiv/

RUN chmod +x /opt/arxiv/start_browse.sh
RUN echo $git_commit > /git-commit.txt

EXPOSE 8000
ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
