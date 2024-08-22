#!/bin/bash
set -e

if [ ! -f .venv ]; then
   echo "No longer using pipenv."
   echo "Virtual Env for browse must be at .venv"
   echo "See README"
   exit 1
fi

/usr/bin/uwsgi -H .venv "$@"
