# Development Guide

This guide is for contributors who want to work on pyvvisf development, testing, and maintenance.

## Getting Started

### Prerequisites

1. **Python Environment**: Use pyenv with Python 3.11.7
2. **System Dependencies**: Install platform-specific build tools
3. **Git**: For version control
4. **Development Tools**: Code formatting, linting, and testing tools

See [Building Guide](BUILDING.md) for detailed setup instructions.

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/jimcortez/pyvvisf.git
cd pyvvisf

# Initialize submodules
git submodule update --init --recursive

# Set up Python environment
pyenv local 3.11.7

# Install in development mode with all tools
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Project Structure

```
pyvvisf/
├── src/pyvvisf/           # Python package
│   ├── __init__.py        # Package initialization
│   └── vvisf_bindings.cpp # C++ bindings source
├── external/              # External dependencies
│   └── VVISF-GL/         # VVISF-GL submodule
├── scripts/              # Build and utility scripts
├── tests/                # Test files
├── examples/             # Usage examples
├── docs/                 # Documentation
├── patches/              # VVISF-GL patches
├── CMakeLists.txt        # CMake configuration
├── setup.py              # Python setup
├── pyproject.toml        # Project configuration
└── Makefile              # Build automation
```

## Development Workflow

### Using Makefile (Recommended)

The project includes a Makefile for common development tasks:

```bash
# Set up development environment
make setup

# Build the project
make build

# Run tests
make test

# Run linting and formatting
make lint
make format

# Clean build artifacts
make clean

# Check dependencies
make check-deps

# Build wheel
make wheel
```

### Manual Development Commands

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=pyvvisf tests/

# Build wheel
./scripts/build_wheel.sh

# Test wheel installation
pip install dist/pyvvisf-*.whl
python scripts/test_wheel.py
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=pyvvisf --cov-report=html

# Run specific test file
pytest tests/test_pyvvisf.py

# Run tests in parallel
pytest -n auto
```

### Test Structure

- `tests/test_pyvvisf.py`: Main test suite
- `tests/test_*.py`: Additional test modules
- `scripts/test_wheel.py`: Wheel installation tests
- `scripts/test_architecture.sh`: Architecture detection tests

### Writing Tests

Follow these guidelines for writing tests:

1. **Use pytest**: All tests should use pytest framework
2. **Descriptive names**: Test function names should describe what they test
3. **Isolation**: Each test should be independent
4. **Coverage**: Aim for high test coverage
5. **Fixtures**: Use pytest fixtures for common setup

Example test:

```python
import pytest
import pyvvisf

def test_platform_info():
    """Test that platform info is returned correctly."""
    info = pyvvisf.get_platform_info()
    assert isinstance(info, str)
    assert len(info) > 0

def test_vvisf_availability():
    """Test that VVISF is available."""
    assert pyvvisf.is_vvisf_available() is True
```

## Code Quality

### Code Formatting

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Code Style Guidelines

1. **Python**: Follow PEP 8 with Black formatting
2. **C++**: Follow project C++ style guidelines
3. **Documentation**: Use docstrings and type hints
4. **Comments**: Write clear, concise comments

## Building and Testing

### Development Builds

For development, use the development installation:

```bash
# Install in development mode
pip install -e ".[dev]"

# This allows you to modify code and see changes immediately
```

### Testing Builds

Test different build configurations:

```bash
# Test development build
pip install -e .

# Test wheel build
./scripts/build_wheel.sh

# Test architecture detection
./scripts/test_architecture.sh

# Test wheel installation
pip install dist/pyvvisf-*.whl
python scripts/test_wheel.py
```

### Cross-Platform Testing

Test on different platforms:

```bash
# Test on current platform
./scripts/build_wheel.sh

# Test with different architectures
export ARCH=arm64
./scripts/build_wheel.sh

export ARCH=x86_64
./scripts/build_wheel.sh
```

## Contributing Code

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**: `make test`
6. **Check code quality**: `make lint`
7. **Commit your changes**: Use descriptive commit messages
8. **Push to your fork**
9. **Submit a pull request**

### Commit Message Guidelines

Use conventional commit messages:

```
feat: add new feature
fix: fix a bug
docs: update documentation
test: add or update tests
refactor: refactor code
style: formatting changes
chore: maintenance tasks
```

### Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] No new warnings or errors
- [ ] Changes are tested on target platforms
- [ ] Commit messages are descriptive

## Debugging

### Common Development Issues

1. **Import errors**: Ensure the C++ extension is built
2. **OpenGL context issues**: Try `reinitialize_glfw_context()`
3. **Build failures**: Check system dependencies
4. **Test failures**: Verify test environment

### Debug Information

```python
import pyvvisf

# Get detailed system information
print(f"Platform: {pyvvisf.get_platform_info()}")
print(f"OpenGL Info: {pyvvisf.get_gl_info()}")
print(f"VVISF Available: {pyvvisf.is_vvisf_available()}")
```

### Debug Mode

Enable debug output during builds:

```bash
# Set debug environment
export CMAKE_VERBOSE_MAKEFILE=ON
export VVISF_BUILD_TYPE=wheel

# Build with debug output
python -m build --wheel --verbose
```

## Release Process

### Preparing a Release

1. **Update version**: Update version in `pyproject.toml`
2. **Update changelog**: Document changes
3. **Test thoroughly**: Run full test suite
4. **Build wheels**: Test wheel builds on all platforms
5. **Create release**: Tag and create GitHub release

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] Wheels build successfully
- [ ] Examples work correctly
- [ ] Version is updated
- [ ] Changelog is updated

## Maintenance

### Regular Tasks

1. **Update dependencies**: Keep dependencies up to date
2. **Monitor CI/CD**: Ensure automated builds work
3. **Review issues**: Address user issues and feature requests
4. **Update documentation**: Keep docs current
5. **Security updates**: Monitor for security vulnerabilities

### Dependency Management

```bash
# Check for outdated dependencies
pip list --outdated

# Update development dependencies
pip install -U black isort flake8 mypy pytest

# Update runtime dependencies
pip install -U pillow
# Optional: pip install -U numpy
```

## Getting Help

### Resources

- **[API Reference](API_REFERENCE.md)**: Complete API documentation
- **[Building Guide](BUILDING.md)**: Detailed build instructions
- **[Wheel Build Guide](WHEEL_BUILD_GUIDE.md)**: Wheel building details
- **[Architecture Improvements](ARCHITECTURE_IMPROVEMENTS.md)**: Architecture details

### Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Pull Requests**: Submit code changes via pull requests

## Related Documentation

- **[Building Guide](BUILDING.md)** - Detailed build instructions
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Wheel Build Guide](WHEEL_BUILD_GUIDE.md)** - Wheel building information
- **[Architecture Improvements](ARCHITECTURE_IMPROVEMENTS.md)** - Architecture details 