# Contributing to AutoAttendance

Thank you for your interest in contributing to AutoAttendance! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome all skill levels
- Focus on code quality and user experience
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Virtual environment (venv or conda)
- Basic understanding of face recognition concepts

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies with dev tools
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b bugfix/issue-description
```

### 2. Make Your Changes

- Keep commits atomic and descriptive
- Follow PEP 8 style guide
- Add type hints to functions
- Write docstrings for classes and methods
- Add unit tests for new functionality

### 3. Code Quality Checks

```bash
# Format code
black .

# Check style
flake8 --max-line-length=100

# Type checking
mypy .

# Run tests
pytest tests/ -v --cov
```

### 4. Commit Guidelines

```bash
# Good commit message format
git commit -m "feat: add face anti-spoofing improvements"
git commit -m "fix: resolve camera initialization error"
git commit -m "docs: update installation guide"
git commit -m "test: add unit tests for recognition module"
```

**Types**: feat, fix, docs, style, refactor, test, chore

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with:
- Clear title describing the change
- Detailed description of what changed and why
- Reference to any related issues (#123)
- Screenshots if UI-related
- Test results

## Contribution Areas

### High Priority
- ✅ Performance optimizations
- ✅ Bug fixes
- ✅ Documentation improvements
- ✅ Unit test coverage
- ✅ Error handling improvements

### Medium Priority
- 📦 New features
- 📦 API enhancements
- 📦 UI/UX improvements
- 📦 Multi-language support

### Low Priority
- 🎨 Code style improvements
- 🎨 Logging enhancements
- 🎨 Example scripts

## Testing Requirements

- Write unit tests for new features
- Minimum 70% code coverage
- All tests must pass before PR merge
- Include integration tests for critical paths

```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings following Google style
- Update ARCHITECTURE.md for structural changes
- Include inline comments for complex logic

## Pull Request Process

1. ✅ Update documentation
2. ✅ Add/update tests
3. ✅ Pass code quality checks
4. ✅ Ensure no merge conflicts
5. ✅ Provide clear PR description
6. ✅ Wait for review approval
7. ✅ Squash commits if requested

## Reporting Issues

### Bug Reports
Include:
- OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Error logs/tracebacks
- Screenshots if applicable

### Feature Requests
Include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any relevant examples

## Questions?

- Open an issue for discussion
- Check existing issues first
- Review documentation
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Project documentation

Thank you for making AutoAttendance better! 🎉
