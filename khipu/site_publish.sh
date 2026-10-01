#!/bin/sh
# Обновляет ветку `site` (только готовый сайт, без истории main) для Vercel, подключённого к GitHub.
# В Vercel: Import Project → этот репозиторий → Production Branch = site, Framework = Other, без команды сборки.
#   sh khipu/site_publish.sh https://<project>.vercel.app
set -e
cd "$(dirname "$0")/.."
URL="${1:?usage: sh khipu/site_publish.sh https://<project>.vercel.app}"
python3 khipu/site_export.py "$URL"
WT=$(mktemp -d)
if git ls-remote --exit-code --heads origin site >/dev/null 2>&1; then
  git fetch -q origin site
  git worktree add -q "$WT" -B site origin/site
else
  git worktree add -q --detach "$WT"
  git -C "$WT" checkout -q --orphan site
  git -C "$WT" rm -rq . >/dev/null 2>&1 || true
fi
find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R dist/. "$WT"/
git -C "$WT" add -A
if git -C "$WT" diff --cached --quiet; then echo "site: no changes"; else
  if git -C "$WT" diff --cached | grep -q "meera.me\|/Users/"; then echo "private string in site diff, stopping"; exit 1; fi
  git -C "$WT" commit -qm "Site build $(git rev-parse --short HEAD)"
  git -C "$WT" push -q origin site
  echo "site: pushed"
fi
git worktree remove --force "$WT"
