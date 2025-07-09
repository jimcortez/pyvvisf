#!/bin/bash
# Development installation script for pure Python pyvvisf

set -e

echo "Installing development dependencies for pyvvisf..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Install the package in development mode
echo "Installing pyvvisf in development mode..."
pip install -e ".[dev]"

# Install additional dependencies for testing
echo "Installing additional test dependencies..."
pip install pytest-cov pytest-mock

echo "Development installation complete!"
echo ""
echo "You can now:"
echo "  - Run tests: pytest"
echo "  - Run the example: python examples/pure_python_demo.py"
echo "  - Format code: black src/ tests/"
echo "  - Check types: mypy src/" 