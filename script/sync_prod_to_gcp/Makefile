.PHONY: test stanza sync-to-gcp-queue sync-to-gcp-sub
SHELL=/bin/bash
APP_CRED=${HOME}/.config/gcloud/application_default_credentials.json
ARXIV_PROJECT_ID := arxiv-production

SYNC_TO_GCP_TOPIC := submission-published
SYNC_TO_GCP_SUB_ID := sync-submission-from-cit-to-gcp

default: sync.venv/bin/uwsgi

sync.venv:
	-[[ -x /opt/rh/rh-python38/root/bin/python3.8 ]] && /opt/rh/rh-python38/root/bin/python3.8 -m venv sync.venv
	-[[ -d sync.venv ]] || [[ -x /usr/local/bin/python3.8 ]] && /usr/local/bin/python3.8 -m venv sync.venv
	-[[ -d sync.venv ]] || [[ -x /usr/bin/python3.8 ]] && /usr/bin/python3.8 -m venv sync.venv

sync.venv/bin/uwsgi: sync.venv 
	. sync.venv/bin/activate && pip install --upgrade pip
	. sync.venv/bin/activate && pip install -r requirements.txt

test: sync.venv  test/arxiv-development_sync-test.json
	. sync.venv/bin/activate && python3 -m test.test_sync_prod_to_gcp

stanza.local:
	-rm -f test/stanza.db
	stanza --config stanza/config.test-local.yaml --database test/stanza.db --plugin_dir stanza/plugins

stanza.gcp.dev: test/arxiv-development_arxiv-stanza.json
	-rm -f test/stanza.db
	stanza --config stanza/config.test-to-gcp.yaml --database test/stanza.db --plugin_dir stanza/plugins

test/arxiv-development_arxiv-stanza.json:
	op read "op://hs3xn7ldhg3pgrql5j524rgpee/grvumhkt4kc47f53t7qjntpg3q/j3msyqb2pa5wec7hbsr3cirnky" > $@

test/arxiv-development_sync-test.json:
	op read "op://hs3xn7ldhg3pgrql5j524rgpee/w2wtsf5v7kahbngr64m43mciou/qrdfsd5gbnatjpv7zof6vwca4q" > $@

sync-to-gcp-queue: CURRENT_PROJECT := $(shell gcloud config get project)

sync-to-gcp-queue:
	-gcloud pubsub topics create ${SYNC_TO_GCP_TOPIC} --message-retention-duration=31d --message-encoding=json --project ${ARXIV_PROJECT_ID} --schema p2p

sync-to-gcp-sub: 
	gcloud pubsub subscriptions create ${SYNC_TO_GCP_SUB_ID} --topic=${SYNC_TO_GCP_TOPIC} --ack-deadline=10 --min-retry-delay=60 --max-retry-delay=600 --max-delivery-attempts=100

install-sync-to-gcp-service:
	sudo -H install -m 0644 resource/systemd/submissions-to-gcp.service /etc/systemd/system/
	sudo systemctl daemon-reload
	@echo "Please run sudo systemctl enable submissions-to-gcp@sync-node.service"
