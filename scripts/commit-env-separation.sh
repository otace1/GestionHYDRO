#!/bin/bash
# =============================================================================
# Atomic Commits Script for Dev/Prod Separation Feature
# =============================================================================
# Run this script to create atomic commits for the configuration changes.
# Review each commit before pushing.
# =============================================================================

set -e

cd "$(dirname "$0")/.."

echo "📦 Creating atomic commits for dev/prod separation..."
echo ""

# First, let's see what we're working with
echo "📋 Current status:"
git status --short
echo ""

# Commit 1: CI/CD workflow separation (most critical change)
echo "1️⃣  Committing: Separate CI/CD workflows for staging and production"
git add .github/workflows/build.yaml
git add .github/workflows/deploy-production.yaml
git add .github/workflows/test-django.yaml
git commit -m "ci: separate staging build from production deployment

- Modify build.yaml to only build staging images (no deploy)
- Create deploy-production.yaml for main branch deploys only
- Add deployment confirmation for manual triggers
- Update test-django.yaml to run on both Dockerized and main
- Production deploys now require merge to 'main' branch

BREAKING: Production deployment no longer triggers on Dockerized push" || echo "  ⚠️  No changes or already committed"

# Commit 2: Environment samples
echo ""
echo "2️⃣  Committing: Add development environment sample"
git add .env.sample
git commit -m "docs: add .env.sample for local development setup

- Add ready-to-use development environment configuration
- Include safe defaults for docker-compose-dev.yml
- Document optional S3 settings (falls back to local storage)" || echo "  ⚠️  No changes or already committed"

# Commit 3: Validation scripts
echo ""
echo "3️⃣  Committing: Add pre-commit validation scripts"
git add scripts/validate_config.py
git add scripts/pre-commit
git commit -m "feat: add pre-commit validation for configuration safety

- Add validate_config.py to check for hardcoded secrets
- Prevent staging .env files with production settings
- Verify settings import pattern is correct
- Add installable pre-commit hook script" || echo "  ⚠️  No changes or already committed"

# Commit 4: Documentation
echo ""
echo "4️⃣  Committing: Add configuration separation documentation"
git add docs/
git commit -m "docs: add comprehensive guide for dev/prod separation

- Document split settings architecture
- Explain git branching strategy
- Provide local development setup instructions
- Include troubleshooting section" || echo "  ⚠️  No changes or already committed"

# Commit 5: Gitignore fix
echo ""
echo "5️⃣  Committing: Fix .gitignore to allow docs folder"
git add .gitignore
git commit -m "fix: allow docs/ folder in git tracking

- Remove 'docs' from .gitignore exclusions
- Keep other volume-related exclusions" || echo "  ⚠️  No changes or already committed"

# Commit 6: Tests for settings separation
echo ""
echo "6️⃣  Committing: Tests for environment isolation"
git add hydrocarbures/tests_settings.py
git commit -m "test: add comprehensive tests for environment isolation

- Add TestEnvironmentIsolation class for dev/prod separation
- Add tests for CSRF origins parsing
- Add tests for Celery broker configuration
- Add tests for settings module importability
- Validate that dev and prod have different defaults" || echo "  ⚠️  No changes or already committed"

# Commit remaining changes
echo ""
echo "7️⃣  Committing: Remaining configuration updates"
git add -A
git commit -m "chore: update project configuration

- Update base settings
- Update requirements
- Update commit script" || echo "  ⚠️  No remaining changes"

echo ""
echo "✅ Commit process complete!"
echo ""
echo "📋 Commit log:"
git log --oneline -8
echo ""
echo "⚠️  Next steps:"
echo "   1. Review commits: git log -p"
echo "   2. Push to remote: git push origin feature/split-settings-env-separation"
echo "   3. Create PR to Dockerized for review"
echo "   4. After merge to Dockerized, create PR from Dockerized to main"

