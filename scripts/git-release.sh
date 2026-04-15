#!/bin/sh
# Called by @semantic-release/exec publishCmd.
# Args: $1 = tag name, $2 = release notes
# Required env: GIT_RELEASE_TOKEN, GIT_RELEASE_URL, CI_REPO
set -e

TAG=$1
NOTES=$2

curl -sf -X POST "$GIT_RELEASE_URL/api/v1/repos/$CI_REPO/releases" \
  -H "Authorization: token $GIT_RELEASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg tag "$TAG" --arg body "$NOTES" '{tag_name: $tag, name: $tag, body: $body}')"