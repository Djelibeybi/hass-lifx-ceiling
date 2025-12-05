# Suggested Development Commands

## Linting & Formatting

### Check code with Ruff
```bash
ruff check .
```

### Format code with Ruff
```bash
ruff format .
```

### Check formatting without changes
```bash
ruff format . --check
```

## Testing

### Run Home Assistant with test configuration
```bash
hass -c config
```
The `config/` directory contains a minimal Home Assistant setup for testing the integration.

## Installation

### Install dependencies (preferred: use uv)
```bash
uv pip install -r requirements.txt
```

### Alternative with pip
```bash
pip install -r requirements.txt
```

## Git Operations

### Commit changes (use --no-gpg-sign per user preference)
```bash
git commit --no-gpg-sign -m "commit message"
```

## Home Assistant Validation

### Hassfest validation (run via GitHub Actions)
Validates Home Assistant integration structure and manifest

### HACS validation (run via GitHub Actions)  
Validates HACS integration requirements

## CI/CD
The project uses GitHub Actions for:
- Linting (on push/PR to main)
- Validation (hassfest, HACS)
- Release automation

See `.github/workflows/` for workflow definitions.
