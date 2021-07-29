set -e

if [ -n "${GITHUB_SHA}" ] ; then
    echo "Using GITHUB_SHA for image tag"
    GIT_V=${GITHUB_SHA}
else
    echo "Getting git version for HEAD to use for image tag"
    GIT_V=$(git describe --exact-match --tags 2> /dev/null || git rev-parse --short HEAD)
fi

TAG=gcr.io/$PROJ/browse:$GIT_V
echo "Using tag $TAG"

docker build --build-arg git_commit=${GIT_V} -t ${TAG} .
docker push ${TAG}

echo ${TAG} > TAG.txt
echo "Build and pushed to $TAG"
