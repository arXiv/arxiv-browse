#!/bin/bash

PYLINT_SCORE=$( pipenv run pylint browse | tail -2 | grep -Eo '[0-9\.]+/10' | tail -1 | sed s/\\/10// );
PYLINT_PASS=$(echo $PYLINT_SCORE">="$MIN_PYLINT_SCORE | bc -l);
if [ "$TRAVIS_PULL_REQUEST_SHA" = "" ];  then SHA=$TRAVIS_COMMIT; else SHA=$TRAVIS_PULL_REQUEST_SHA; fi;
if [ "$PYLINT_PASS" ]; then PYLINT_STATE="success" &&  echo "pylint passed with score "$PYLINT_SCORE" for sha "$SHA; else PYLINT_STATE="failure" &&  echo "pylint failed with score "$PYLINT_SCORE" for sha "$SHA; fi;
curl -u $USERNAME:$GITHUB_TOKEN -d '{"state": "'$PYLINT_STATE'", "target_url": "https://travis-ci.org/'$TRAVIS_REPO_SLUG'/builds/'$TRAVIS_BUILD_ID'", "description": "'$PYLINT_SCORE'/10", "context": "code-quality/pylint"}' -XPOST https://api.github.com/repos/$TRAVIS_REPO_SLUG/statuses/$SHA > /dev/null 2>&1
