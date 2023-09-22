.PHONY: test
SHELL=/bin/bash

default: sync.venv

sync.venv:
	-[[ -x /opt/rh/rh-python38/root/bin/python3.8 ]] && /opt/rh/rh-python38/root/bin/python3.8 -m venv sync.venv
	[[ -d sync.venv ]] || [[ -x /usr/bin/python3.8 ]] && /usr/bin/python3.8 -m venv sync.venv
	. sync.venv/bin/activate && pip install --upgrade pip
	. sync.venv/bin/activate && pip install -r requirements.txt

test:
	. sync.venv/bin/activate && python3 -m test.test_sync_prod_to_gcp
