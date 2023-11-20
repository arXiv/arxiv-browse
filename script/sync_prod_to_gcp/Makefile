.PHONY: test stanza
SHELL=/bin/bash
APP_CRED=${HOME}/.config/gcloud/application_default_credentials.json

default: sync.venv/bin/uwsgi

sync.venv:
	-[[ -x /opt/rh/rh-python38/root/bin/python3.8 ]] && /opt/rh/rh-python38/root/bin/python3.8 -m venv sync.venv
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

${APP_CRED}:
	gcloud auth application-default login
