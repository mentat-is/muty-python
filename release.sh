#!/usr/bin/env bash
set -euo pipefail

# release.sh: helpers to trigger test/publish workflows for muty-python
# Usage:
#   ./release.sh test 1.2.3
#   ./release.sh publish 1.2.3

cd "$(dirname "$0")"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <test|publish> <version>"
  exit 1
fi

MODE=$1
VERSION=$2

function check_clean_worktree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is dirty. Commit or stash changes first."
    exit 1
  fi
}

function check_branch() {
  local branch
  branch=$(git rev-parse --abbrev-ref HEAD)
  echo "Current branch: $branch"
}

check_clean_worktree
check_branch

function cleanup_tag() {
  local tag="$1"
  if git tag --list "$tag" >/dev/null 2>&1; then
    echo "Local tag $tag exists, deleting local copy."
    git tag -d "$tag" || true
  fi
  if git ls-remote --tags origin "$tag" | grep -q "$tag"; then
    echo "Remote tag $tag exists, deleting remote copy."
    git push --delete origin "$tag" || true
  fi
}

if [[ "$MODE" == "test" ]]; then
  TAG="test-v${VERSION}"
  echo "[test] preparing temporary tag $TAG"
  cleanup_tag "$TAG"
  echo "[test] creating temporary tag $TAG"
  git tag -a "$TAG" -m "Test release $VERSION"
  git push origin "$TAG"
  echo "Tag pushed: $TAG"
  echo "Workflow triggered; wait for GitHub Actions to complete and inspect logs." 

  read -p "Press ENTER after test run is complete to remove the temporary tag from origin and local" dummy

  echo "Removing temporary tag $TAG from remote and local"
  git push --delete origin "$TAG" || true
  git tag -d "$TAG" || true
  echo "Temporary test tag removed."
  exit 0
fi

if [[ "$MODE" == "publish" ]]; then
  TAG="v${VERSION}"
  echo "[publish] preparing release tag $TAG"
  cleanup_tag "$TAG"
  echo "[publish] creating release tag $TAG"
  git tag -a "$TAG" -m "Release $VERSION"
  git push origin "$TAG"
  echo "Release tag pushed. GitHub Actions will run publish workflow."
  exit 0
fi

echo "Unknown mode: $MODE. Use 'test' or 'publish'."
exit 1
