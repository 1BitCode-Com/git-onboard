# Changelog

All notable changes to Git Onboard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflow
- Comprehensive project structure
- Package distribution setup
- Development tools and documentation

### Changed
- Improved build system with pyproject.toml
- Enhanced test coverage
- Better error handling in CI/CD

### Fixed
- Python packaging issues
- Entry point configuration
- Module naming conventions

## [1.0.0] - 2025-07-29

### Added
- **Core Features**:
  - Automated Git repository initialization
  - SSH key generation and management
  - Interactive .gitignore configuration
  - Commit and push automation
  - Cross-platform package manager detection

- **Recovery Features**:
  - Detached repository detection (missing .git folder)
  - Remote repository verification with shallow clone
  - File comparison using SHA256 checksums
  - Selective staging of modified/new files only
  - Conflict resolution with pull/force push options
  - Support for both remote-exists and local-only scenarios

- **Configuration**:
  - JSON/YAML configuration file support
  - Command-line argument parsing
  - Environment variable support
  - Custom log file paths

- **Testing**:
  - Comprehensive unit test suite
  - Mocked Git operations
  - Error scenario testing
  - Recovery workflow testing

### Changed
- Renamed from "GitHub Onboarding Automation" to "Git Onboard"
- Removed rich dependency for simpler installation
- Updated all documentation and references
- Improved error messages and user prompts
- Enhanced .gitignore pattern filtering

### Fixed
- Branch detection and management issues (master vs main)
- Push conflict resolution with user choice
- .gitignore pattern filtering during file comparison
- File comparison accuracy with proper filtering
- Duplicate .gitignore prompts
- Missing .git folder creation when no changes detected

### Technical Details
- **Language**: Python 3.7+
- **Dependencies**: Standard library only (no external dependencies)
- **License**: MIT
- **Platforms**: Linux, macOS, Windows (with Git)
- **Entry Point**: `git-onboard` command

### Documentation
- Complete README with usage examples
- Contributing guidelines (CONTRIBUTING.md)
- License file (LICENSE)
- Setup and installation instructions
- Security policy (SECURITY.md)
- Code of conduct (CODE_OF_CONDUCT.md)
- Issue and pull request templates
- GitHub Actions workflow for CI/CD 
