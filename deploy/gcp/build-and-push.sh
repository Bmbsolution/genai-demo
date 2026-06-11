#!/usr/bin/env bash
# Build the Gatherly backend image and push it to Artifact Registry.
# Usage: ./build-and-push.sh <project_id> <region> [tag]
set -euo pipefail

PROJECT="${1:?usage: build-and-push.sh PROJECT_ID REGION [TAG]}"
REGION="${2:?usage: build-and-push.sh PROJECT_ID REGION [TAG]}"
TAG="${3:-latest}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/gatherly/gatherly-api:${TAG}"
HERE="$(cd "$(dirname "$0")" && pwd)"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker build -t "${IMAGE}" "${HERE}/../../gatherly-be"
docker push "${IMAGE}"

echo
echo "Pushed: ${IMAGE}"
echo "Deploy it:  terraform apply -var=\"image=${IMAGE}\""
