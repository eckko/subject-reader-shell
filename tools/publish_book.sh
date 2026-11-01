#!/usr/bin/env bash
# Publish one private book repo into this subject site and push.
#
#   tools/publish_book.sh BOOK_REPO_CHECKOUT FOLDER_NAME
#
# Run from a checkout of this repo, by the workflow in
# templates/publish-to-subject.yml. The logic lives here, so a book repo
# only needs the small workflow file. Two books may publish at the same
# moment; when the push is refused the script starts again from the newest
# commit, which is safe because add_book.py is repeatable.
set -euo pipefail

BOOK_DIR="$1"
NAME="$2"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

for attempt in 1 2 3 4 5; do
  python3 tools/add_book.py "$BOOK_DIR" --name "$NAME" --subject-root .
  git add -A
  if git diff --cached --quiet; then
    echo "Nothing changed for $NAME"
    exit 0
  fi
  git commit -m "Update $NAME"
  if git push origin "HEAD:$BRANCH"; then
    exit 0
  fi
  echo "Push refused (attempt $attempt); starting again from the newest commit"
  git fetch origin "$BRANCH"
  git reset --hard "origin/$BRANCH"
  sleep $((attempt * 3))
done
echo "Could not push after 5 attempts" >&2
exit 1
