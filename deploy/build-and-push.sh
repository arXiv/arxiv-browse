set -e

if [ -n "${GITHUB_SHA}" ] ; then
    echo "Using GITHUB_SHA"
    GIT_V=${GITHUB_SHA}
else
    echo "Getting git version for HEAD"
    GIT_V=$(git rev-parse --short HEAD)
fi

TAG=gcr.io/$PROJ/browse:$GIT_V

docker build --build-arg git_commit=${GIT_V} -t ${TAG} .
docker push ${TAG}

echo ${TAG} > TAG.txt
