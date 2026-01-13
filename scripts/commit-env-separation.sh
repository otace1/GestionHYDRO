#!/bin/bash
# =============================================================================
# Atomic Commits Script for Dev/Prod Separation Feature
# =============================================================================
# Run this script to create atomic commits for the configuration changes.
# Review each commit before pushing.
# =============================================================================

set -e

echo "📦 Creating atomic commits for dev/prod separation..."

# Commit 1: Tests for settings separation
echo ""
echo "1️⃣  Committing: Tests for environment isolation"
git add hydrocarbures/tests_settings.py
git commit -m "test: add comprehensive tests for environment isolation

- Add TestEnvironmentIsolation class for dev/prod separation
- Add tests for CSRF origins parsing
- Add tests for Celery broker configuration
- Add tests for settings module importability
- Validate that dev and prod have different defaults"

# Commit 2: CI/CD workflow separation
echo ""
echo "2️⃣  Committing: Separate CI/CD workflows for staging and production"
git add .github/workflows/build.yaml
git add .github/workflows/deploy-production.yaml
git add .github/workflows/test-django.yaml
git commit -m "ci: separate staging build from production deployment

- Rename build.yaml to only build staging images (no deploy)
- Create deploy-production.yaml for main branch deploys only
- Add deployment confirmation for manual triggers
- Update test-django.yaml to run on both Dockerized and main
- Production deploys now require merge to 'main' branch

BREAKING: Production deployment no longer triggers on Dockerized push"

# Commit 3: Environment samples
echo ""
echo "3️⃣  Committing: Add development environment sample"
git add .env.sample
git commit -m "docs: add .env.sample for local development setup

- Add ready-to-use development environment configuration
- Include safe defaults for docker-compose-dev.yml
- Document optional S3 settings (falls back to local storage)"

# Commit 4: Validation scripts
echo ""
echo "4️⃣  Committing: Add pre-commit validation scripts"
git add scripts/validate_config.py
git add scripts/pre-commit
git commit -m "feat: add pre-commit validation for configuration safety

- Add validate_config.py to check for hardcoded secrets
- Prevent staging .env files with production settings
- Verify settings import pattern is correct
- Add installable pre-commit hook script"

# Commit 5: Documentation
echo ""
echo "5️⃣  Committing: Add configuration separation documentation"
git add docs/CONFIG_SEPARATION.md
git commit -m "docs: add comprehensive guide for dev/prod separation

- Document split settings architecture
- Explain git branching strategy
- Provide local development setup instructions
- Include troubleshooting section"

# Commit 6: Gitignore fix
echo ""
echo "6️⃣  Committing: Fix .gitignore to allow docs folder"
git add .gitignore
git commit -m "fix: allow docs/ folder in git tracking

- Remove 'docs' from .gitignore exclusions
- Keep other volume-related exclusions"

echo ""
echo "✅ All commits created successfully!"
echo ""
echo "📋 Commit log:"
git log --oneline -6
echo ""
echo "⚠️  Next steps:"
echo "   1. Review commits: git log -p"
echo "   2. Push to remote: git push origin feature/split-settings-env-separation"
echo "   3. Create PR to Dockerized for review"
echo "   4. After merge to Dockerized, create PR from Dockerized to main"

