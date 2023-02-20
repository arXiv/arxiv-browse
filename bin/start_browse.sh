#!/bin/bash
set -e

#TODO Change from piepnv to not using pipenv, make sure this still works if you are using it
if [ ! -f .venv ]; then
   echo "No longer using pipenv."
   echo "Virtual Env for browse must be at .venv"
   echo "See README"
   exit 1
fi

/usr/bin/uwsgi -H .venv "$@"
