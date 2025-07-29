# Contributing to Git Onboard

Thank you for your interest in contributing to Git Onboard! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a new branch** for your feature/fix
4. **Make your changes**
5. **Test your changes**
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.7+
- Git
- pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/git-onboard.git
cd git-onboard

# Install in development mode
pip install -e .

# Run tests
python3 git_onboard.py test
```
```

## Code Style

### Python

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions small and focused

### Git Commits

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, etc.)
- Keep commits atomic and focused

Example:
```
Add support for custom .gitignore patterns
Fix branch detection in push_to_remote function
Update README with new features
```

## Testing

### Running Tests

```bash
# Run all tests
python3 git-onboard.py test

# Run specific test file
python3 -m pytest tests/test_git_onboard.py -v
```

### Writing Tests

- Write tests for new features
- Ensure all tests pass before submitting
- Use descriptive test names
- Mock external dependencies

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** if applicable
5. **Submit pull request** with clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test update

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes
```

## Reporting Issues

When reporting issues, please include:

- **Operating system** and version
- **Python version**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Error messages** (if any)

## Feature Requests

For feature requests:

- **Describe the feature** clearly
- **Explain the use case**
- **Consider implementation complexity**
- **Check if it aligns with project goals**

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Be patient with newcomers

## License

By contributing to Git Onboard, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Git Onboard! 