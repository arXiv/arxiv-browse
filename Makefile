.PHONY: default run proxy

default: venv

venv: .prerequisit
	python3 -c 'import sys; assert sys.hexversion >= 0x030a0000'
	python3 -m venv ./venv
	. venv/bin/activate && pip install pip --upgrade
	. venv/bin/activate && pip install poetry
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
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port 1234 arxiv-production:us-east4:arxiv-production-rep4 > /dev/null 2>&1 &

tests/.env: ~/.arxiv/browse.env
	cp $< $@ 
