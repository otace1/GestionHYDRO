# Configuration Dev/Prod Separation Guide

## Architecture Overview

This project uses a **split settings** pattern to separate development and production configurations:

```
hydrocarbures/
├── settings/
│   ├── __init__.py    # Settings module selector
│   ├── base.py        # Shared settings
│   ├── development.py # Dev-specific settings
│   ├── production.py  # Prod-specific settings  
│   └── test.py        # Test-specific settings
└── config.py          # Pydantic validation
```

## Environment Selection

The environment is selected via `DJANGO_ENV` variable:

```bash
# Development (default)
export DJANGO_ENV=development

# Production
export DJANGO_ENV=production

# Testing
export DJANGO_ENV=test
```

## Git Branching Strategy

```
main (production)
  ↑ PR + Review required
  │
Dockerized (staging/dev)
  ↑ PR from feature branches
  │
feature/* (development)
```

### Workflows:

| Workflow | Trigger | Action |
|----------|---------|--------|
| `test-django.yaml` | Push/PR to any branch | Run tests only |
| `build.yaml` | Push/PR to `Dockerized` | Build staging image (no deploy) |
| `deploy-production.yaml` | Push to `main` | Deploy to production |

## Local Development Setup

1. **Copy the environment sample:**
   ```bash
   cp .env.sample .env
   ```

2. **Start services with Docker Compose:**
   ```bash
   docker-compose -f docker-compose-dev.yml up -d
   ```

3. **Or run locally:**
   ```bash
   export DJANGO_ENV=development
   python manage.py runserver
   ```

## Safety Checks

### Pre-commit Validation
```bash
python scripts/validate_config.py
```

### Install as Git Hook
```bash
echo '#!/bin/sh
python scripts/validate_config.py || exit 1
' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Production Deployment

1. **Merge to `main` branch** - This triggers automatic deployment
2. **Or manual deployment:**
   - Go to GitHub Actions
   - Select "Deploy to Production" workflow
   - Click "Run workflow"
   - Type "deploy" to confirm

## Security Notes

- `.env` files are **never committed** (see `.gitignore`)
- Production secrets are stored in **GitHub Secrets**
- Kubernetes secrets are created during deployment
- `DEBUG=True` is **impossible** in production (enforced by Pydantic)

## Testing Configuration

Run configuration tests:
```bash
DJANGO_ENV=test python -m unittest hydrocarbures.tests_settings -v
```

## Troubleshooting

### "Configuration errors for production environment"
- Ensure all required environment variables are set
- Check `DJANGO_SECRET_KEY` is at least 50 characters
- Verify `ALLOWED_HOSTS` is not empty
- Confirm AWS credentials are provided

### Wrong environment loaded
- Check `DJANGO_ENV` value: `echo $DJANGO_ENV`
- Verify `.env` file exists and has correct `DJANGO_ENV`
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`

