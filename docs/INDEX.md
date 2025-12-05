# LIFX Ceiling Integration Documentation Index

Welcome to the LIFX Ceiling custom integration documentation. This index will help you find the information you need.

## Documentation Overview

### For Users

📘 **[README](../README.md)** - Start here
- What is LIFX Ceiling integration
- Installation instructions (HACS)
- Fresh install vs upgrade guide
- Using the `set_state` service
- Reporting issues

### For Developers

🔧 **[DEVELOPMENT](DEVELOPMENT.md)** - Development guide
- Quick start and environment setup
- Architecture deep dive (object casting, zone mapping, framebuffers)
- Common development tasks
- Testing and debugging strategies
- Contributing guidelines
- Advanced topics (migration, performance)

📖 **[API Reference](API.md)** - Complete API documentation
- Core classes (LIFXCeiling, Coordinator, Entities)
- All properties and methods with parameters
- Utility functions
- Constants and service definitions
- Integration flow diagrams
- Cross-references

🤖 **[CLAUDE.md](../CLAUDE.md)** - For AI assistants
- Project overview and architecture
- Development commands
- High-level architectural patterns
- LIFX protocol details
- Common code patterns

### For Contributors

✍️ **[CONTRIBUTING](../CONTRIBUTING.md)** - Contribution guidelines
- How to report bugs
- How to propose features
- Pull request process
- Code style requirements
- License information

---

## Quick Links by Topic

### Architecture & Design

| Topic | Document | Section |
|-------|----------|---------|
| Object casting pattern | [DEVELOPMENT](DEVELOPMENT.md#object-casting-pattern) | Architecture |
| Zone mapping (64 vs 128) | [DEVELOPMENT](DEVELOPMENT.md#zone-mapping) | Architecture |
| Framebuffer operations | [DEVELOPMENT](DEVELOPMENT.md#framebuffer-operations) | Architecture |
| Coordinator pattern | [DEVELOPMENT](DEVELOPMENT.md#coordinator-pattern) | Architecture |
| Entity state flow | [DEVELOPMENT](DEVELOPMENT.md#entity-state-flow) | Architecture |
| Color conversions | [DEVELOPMENT](DEVELOPMENT.md#color-scale-conversions) | Architecture |
| Integration flow | [API](API.md#integration-flow) | Reference |

### API Reference

| Component | Document | Section |
|-----------|----------|---------|
| LIFXCeiling class | [API](API.md#lifxceiling) | Core Classes |
| LIFXCeilingUpdateCoordinator | [API](API.md#lifxceilingupdatecoordinator) | Core Classes |
| Light entities | [API](API.md#light-entities) | Core Classes |
| Utility functions | [API](API.md#utility-functions) | Reference |
| Constants | [API](API.md#constants) | Reference |
| Service API | [API](API.md#service-api) | Reference |

### Development Tasks

| Task | Document | Section |
|------|----------|---------|
| Setup environment | [DEVELOPMENT](DEVELOPMENT.md#setup-development-environment) | Quick Start |
| Add new property | [DEVELOPMENT](DEVELOPMENT.md#adding-a-new-property-to-lifxceiling) | Common Tasks |
| Add new service | [DEVELOPMENT](DEVELOPMENT.md#adding-a-new-service) | Common Tasks |
| Modify zone control | [DEVELOPMENT](DEVELOPMENT.md#modifying-zone-control-logic) | Common Tasks |
| Handle 128-zone devices | [DEVELOPMENT](DEVELOPMENT.md#handling-128-zone-devices) | Common Tasks |
| Debug issues | [DEVELOPMENT](DEVELOPMENT.md#debugging) | Testing |
| Submit PR | [DEVELOPMENT](DEVELOPMENT.md#before-submitting-pr) | Contributing |

### User Guide

| Topic | Document | Section |
|-------|----------|---------|
| Installation | [README](../README.md#fresh-install) | Setup |
| Upgrading | [README](../README.md#upgrading-from-the-pre-release-version) | Setup |
| Using set_state service | [README](../README.md#the-set_state-action) | Features |
| Service parameters | [API](API.md#service-api) | Reference |
| Reporting issues | [README](../README.md#issues-bugs) | Support |

---

## Documentation Structure

```
docs/
├── INDEX.md           # This file - navigation hub
├── API.md             # Complete API reference
└── DEVELOPMENT.md     # Development guide

Root level:
├── README.md          # User documentation
├── CLAUDE.md          # AI assistant guide
├── CONTRIBUTING.md    # Contribution guidelines
└── ruff.toml          # Code style configuration
```

---

## Common Questions

### Where do I find...?

**...installation instructions?**
→ [README - Fresh Install](../README.md#fresh-install)

**...how to use the set_state service?**
→ [README - Service Documentation](../README.md#the-set_state-action)
→ [API - Service API](API.md#service-api)

**...development setup?**
→ [DEVELOPMENT - Quick Start](DEVELOPMENT.md#quick-start)

**...architecture explanations?**
→ [DEVELOPMENT - Architecture Deep Dive](DEVELOPMENT.md#architecture-deep-dive)
→ [CLAUDE.md - Architecture](../CLAUDE.md#architecture)

**...API reference for a class?**
→ [API - Core Classes](API.md#core-classes)

**...how zone control works?**
→ [DEVELOPMENT - Zone Mapping](DEVELOPMENT.md#zone-mapping)
→ [API - LIFXCeiling Methods](API.md#methods)

**...color conversion formulas?**
→ [DEVELOPMENT - Color Scale Conversions](DEVELOPMENT.md#color-scale-conversions)
→ [API - hsbk_for_turn_on](API.md#hsbk_for_turn_on)

**...how to contribute?**
→ [CONTRIBUTING](../CONTRIBUTING.md)
→ [DEVELOPMENT - Contributing](DEVELOPMENT.md#contributing)

**...debugging tips?**
→ [DEVELOPMENT - Debugging](DEVELOPMENT.md#debugging)

---

## Document Purpose Summary

### README.md
**Audience**: End users
**Purpose**: Installation, usage, features
**When to read**: First time using the integration

### DEVELOPMENT.md
**Audience**: Developers and contributors
**Purpose**: In-depth architecture, common tasks, testing
**When to read**: Contributing code or understanding internals

### API.md
**Audience**: Developers needing reference
**Purpose**: Complete API documentation with parameters and types
**When to read**: Looking up specific classes/methods/functions

### CLAUDE.md
**Audience**: AI assistants (Claude Code)
**Purpose**: High-level architecture and common patterns
**When to read**: AI-assisted development

### CONTRIBUTING.md
**Audience**: Contributors
**Purpose**: Contribution process and guidelines
**When to read**: Before submitting PR or issue

---

## Version Information

- **Minimum Home Assistant**: 2025.8.0
- **Python Version**: 3.12+
- **Current Integration Version**: See [manifest.json](../custom_components/lifx_ceiling/manifest.json)

---

## External Resources

### Home Assistant
- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Home Assistant Community](https://community.home-assistant.io/)

### LIFX
- [LIFX Developer Documentation](https://lan.developer.lifx.com/)
- [aiolifx Library](https://github.com/aiolifx/aiolifx)
- [LIFX Multizone Protocol](https://lan.developer.lifx.com/docs/multizone-messages)

### Development Tools
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [HACS Documentation](https://hacs.xyz/)
- [Git Conventional Commits](https://www.conventionalcommits.org/)

---

## Getting Help

### For Users
- Check [README](../README.md) first
- Search [GitHub Issues](https://github.com/Djelibeybi/hass-lifx-ceiling/issues)
- Create new issue if needed

### For Developers
- Read [DEVELOPMENT.md](DEVELOPMENT.md)
- Check [API.md](API.md) for reference
- Ask in [GitHub Discussions](https://github.com/Djelibeybi/hass-lifx-ceiling/discussions)

---

## Contributing to Documentation

Documentation improvements are welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

When updating documentation:
1. Keep `API.md` in sync with code
2. Update `DEVELOPMENT.md` for architectural changes
3. Update `CLAUDE.md` for new patterns
4. Update this `INDEX.md` for new sections
5. Keep `README.md` user-focused

---

*Last updated: 2025-12-05*