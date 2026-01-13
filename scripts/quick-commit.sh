#!/bin/bash
# =============================================================================
# Quick commit script - Run this after reviewing changes
# =============================================================================

cd "$(dirname "$0")/.."

echo "📋 Files to be committed:"
echo "========================="
git status --short
echo ""

read -p "Proceed with commits? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Add all changes
git add -A

# Single comprehensive commit
git commit -m "feat: implement dev/prod environment separation

## Changes:
- Separate CI/CD workflows (staging build vs production deploy)
- Production deployment only triggers on 'main' branch push
- Add .env.sample for local development
- Add pre-commit validation scripts
- Add CONFIG_SEPARATION.md documentation
- Fix .gitignore to allow docs/ folder
- Add comprehensive tests for environment isolation

## Security:
- Staging builds no longer deploy to production
- Manual confirmation required for workflow_dispatch deploys
- Pre-commit hook prevents hardcoded secrets

BREAKING CHANGE: Production deployment no longer triggers on Dockerized push.
Merge to 'main' branch required for production deployment."

echo ""
echo "✅ Done! Push with:"
echo "   git push origin feature/split-settings-env-separation"

