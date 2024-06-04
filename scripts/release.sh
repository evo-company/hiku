# /bin/env bash

set -e
USAGE="Usage: release.sh 0.1.1 'Release message'"

VERSION=$1
MESSAGE=$2

if [ -z "${VERSION}" ]; then
    echo $USAGE
    echo "VERSION is not set"
    exit 1
fi
if [ -z "${MESSAGE}" ]; then
    echo $USAGE
    echo "MESSAGE is not set"
    exit 1
fi
echo "Releasing ${VERSION}"

echo "__version__ = \"${VERSION}\"" > hiku/__init__.py
git add hiku/__init__.py
git commit -m "Release ${VERSION}"
git tag -a v${VERSION} -m "${MESSAGE}"
git push origin master --tags