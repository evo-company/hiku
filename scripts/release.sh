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

if [[ "${VERSION}" == "rc" ]]; then
  uv version --bump rc
  VERSION=$(uv version --short)
else
  uv version ${VERSION}
fi

echo "Releasing ${VERSION}"

git add pyproject.toml
git commit -m "release ${version}"
git tag -a v${VERSION} -m "${MESSAGE}"
git push origin master --tags
