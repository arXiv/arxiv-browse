#!/bin/bash
SRCDOCS=`pwd`/docs/source/_build/html
REPO=arXiv/arxiv-browse
echo $SRCDOCS

cd `pwd`/docs
make html

cd $SRCDOCS
MSG="Adding gh-pages docs for `git log -1 --pretty=short --abbrev-commit`"

TMPREPO=/tmp/docs/$REPO
rm -rf $TMPREPO
mkdir -p -m 0755 $TMPREPO
echo $MSG

git clone git@github.com:$REPO.git $TMPREPO
cd $TMPREPO

## checkout the branch if it exists, if not then create it and detach it from the history
if ! git checkout gh-pages; then
    git checkout --orphan gh-pages
    git rm -rf .
    touch .nojekyll
    git add .nojekyll
else
    git checkout gh-pages  ###gh-pages has previously one off been set to be nothing but html
fi

cp -r $SRCDOCS/* $TMPREPO
git add -A
git commit -m "$MSG" && git push origin gh-pages
