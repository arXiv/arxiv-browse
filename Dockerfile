# arxiv/browse
#
# Defines the runtime for the arXiv browse service, which provides the main
# UIs for browse.

FROM arxiv/base:0.16.7
ARG git_commit

WORKDIR /opt/arxiv

# remove conflicting mariadb-libs from arxiv/base
RUN yum remove -y mariadb-libs

# install MySQL
RUN yum install -y which mysql mysql-devel
RUN pip install uwsgi

# add python application and configuration
ENV PIPENV_VENV_IN_PROJECT 1
ADD app.py /opt/arxiv/
ADD Pipfile /opt/arxiv/
ADD Pipfile.lock /opt/arxiv/
RUN pip install -U pip pipenv
RUN pipenv sync

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
# ENV DEBUG yes

EXPOSE 8000
ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
