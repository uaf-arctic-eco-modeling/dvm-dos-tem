#!/usr/bin/env bash
#
# scripts/ci/ensure-dev-image.sh
#
# Ensures that locally-tagged `cpp-dev:$V_TAG` and `dvmdostem-dev:$V_TAG`
# images exist (the tags docker-compose.yml expects), reusing a cached image
# from GHCR keyed on the content of the files that actually affect the image
# (Dockerfile, requirements) instead of rebuilding from scratch on every CI
# run. $V_TAG itself (git describe output) changes on nearly every commit, so
# it is unsuitable as a cache key -- that's what this script works around.
#
# Required env vars:
#   V_TAG             - tag docker-compose.yml expects locally (git describe)
#   GITHUB_REPOSITORY - "owner/repo", set automatically in GitHub Actions
#   GITHUB_ACTOR      - set automatically in GitHub Actions
#   GITHUB_TOKEN      - needs packages:write to push, packages:read to pull

set -euo pipefail

REGISTRY="ghcr.io/${GITHUB_REPOSITORY,,}"
HOSTUID="$(id -u)"
HOSTGID="$(id -g)"

# The image bakes in the container user's UID/GID, which must match the host
# user for the bind-mounted /work to be writable, so they are part of the key.
DEPS_TAG="deps-$( (cat Dockerfile requirements_general_dev.txt requirements_mapping.txt; echo "${HOSTUID}:${HOSTGID}") | sha256sum | cut -c1-16)"

echo "Dependency (cache) tag: ${DEPS_TAG}"

echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

if docker pull "${REGISTRY}/dvmdostem-dev:${DEPS_TAG}"; then
  echo "Cache hit -- reusing published image, skipping build."
  docker tag "${REGISTRY}/dvmdostem-dev:${DEPS_TAG}" "dvmdostem-dev:${V_TAG}"
else
  echo "Cache miss -- building cpp-dev and dvmdostem-dev images."

  # The Dockerfile's dvmdostem-dev stage does `FROM cpp-dev:$GIT_VERSION`, a
  # cross-image reference rather than an internal multi-stage build name, so
  # cpp-dev must be built and tagged first under the same tag value.
  docker build --build-arg GIT_VERSION="${DEPS_TAG}" \
               --build-arg UID="${HOSTUID}" --build-arg GID="${HOSTGID}" \
               --target cpp-dev --tag "cpp-dev:${DEPS_TAG}" .
  docker build --progress plain \
               --build-arg GIT_VERSION="${DEPS_TAG}" \
               --build-arg UID="${HOSTUID}" --build-arg GID="${HOSTGID}" \
               --target dvmdostem-dev --tag "dvmdostem-dev:${DEPS_TAG}" .

  docker tag "cpp-dev:${DEPS_TAG}" "${REGISTRY}/cpp-dev:${DEPS_TAG}"
  docker tag "dvmdostem-dev:${DEPS_TAG}" "${REGISTRY}/dvmdostem-dev:${DEPS_TAG}"
  docker push "${REGISTRY}/cpp-dev:${DEPS_TAG}"
  docker push "${REGISTRY}/dvmdostem-dev:${DEPS_TAG}"

  docker tag "dvmdostem-dev:${DEPS_TAG}" "dvmdostem-dev:${V_TAG}"
fi
