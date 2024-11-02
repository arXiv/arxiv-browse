.PHONY: default run proxy gcp.dev.env.standard gcp.dev.env.integration

TAG := arxiv-browse
NAME := arxiv-browse
DOCKERPORT := 8080
PROD_DB_PROXY_PORT := 2021
LOCALPORT := 6200
DBPROXYPORT := 6201
BROWSE_DOCKER_RUN := docker run --cpus 2 --rm -p ${LOCALPORT}:${DOCKERPORT} -e PORT=${DOCKERPORT} -v  ${HOME}/arxiv/arxiv-browse/tests:/tests  --name ${NAME} --env-file "${PWD}/tests/docker.env"  --security-opt="no-new-privileges=true" 

default: venv

venv: .prerequisit
	python3 -c 'import sys; assert sys.hexversion >= 0x030a0000'
	python3 -m venv ./venv
	. venv/bin/activate && pip install pip --upgrade
	. venv/bin/activate && pip install poetry==1.3.2
	. venv/bin/activate && poetry install

/usr/local/bin/cloud-sql-proxy:
	curl -o ./cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.linux.amd64
	sudo install -m 755 cloud-sql-proxy /usr/local/bin
	rm -f ./cloud-sql-proxy

.prerequisit: /usr/local/bin/cloud-sql-proxy
	sudo apt install -y libmysqlclient-dev
	touch .prerequisit

run:	venv
	. venv/bin/activate && python main.py

proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${PROD_DB_PROXY_PORT} arxiv-production:us-central1:arxiv-production-rep9 > /dev/null 2>&1 &

dev-proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${DBPROXYPORT} arxiv-development:us-east4:arxiv-db-dev > /dev/null 2>&1 &

tests/.env: ~/.arxiv/browse.env
	cp $< $@ 

docker:
	@if [ -n "$$INSIDE_EMACS" ]; then \
	  echo "Detected Emacs shell mode, stopping. Run it from a terminal, or else you'd be swamped."; \
	  exit 1; \
	fi
	docker build -f Dockerfile -t ${TAG} .

tests/docker.env: ${HOME}/.arxiv/browse-docker.env
	cp $< $@ 

tests/arxiv-development-38ce4ed90aae.json: ${HOME}/.arxiv/arxiv-development-38ce4ed90aae.json
	cp $< $@ 

docker.run: tests/docker.env tests/arxiv-development-38ce4ed90aae.json
	${BROWSE_DOCKER_RUN} -it ${TAG}

docker.sh: tests/docker.env tests/arxiv-development-38ce4ed90aae.json
	${BROWSE_DOCKER_RUN} -it ${TAG} /bin/bash

gcp.dev.env.standard:
	gcloud run services --project arxiv-development update arxiv-browse --region=us-central1 --platform managed --env-vars-file=cicd/env.arxiv-browse.arxiv-development.yaml

gcp.dev.env.integration:
	gcloud run services --project arxiv-development update arxiv-browse --region=us-central1 --platform managed --env-vars-file=cicd/env.arxiv-browse-integration.arxiv-development.yaml
