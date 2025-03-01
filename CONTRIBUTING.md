# Contributing to PsychoPy Gaze Tracking

Thank you for considering contributing to PsychoPy Gaze Tracking! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/PsychoPy_GazeTracking.git`
3. Set up the development environment:
   - On macOS/Linux: `./install_dev.sh`
   - On Windows: `install_dev.bat`
4. Create a new branch for your feature: `git checkout -b feature/your-feature-name`

## Development Workflow

### Running Tests

Before submitting a pull request, make sure all tests pass:

```bash
./tests/run_tests.py
```

### Code Style

We follow PEP 8 style guidelines for Python code. You can use tools like `black` and `flake8` to ensure your code follows these guidelines:

```bash
# Format code with black
black .

# Check code style with flake8
flake8 .
```

### Adding New Features

1. Create a new branch for your feature
2. Implement your feature
3. Add tests for your feature
4. Update documentation if necessary
5. Submit a pull request

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

If you have an idea for an enhancement, please create an issue with the following information:
- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant examples or mockups

## Pull Request Process

1. Update the README.md or documentation with details of changes if necessary
2. Update the tests to cover your changes
3. Make sure all tests pass
4. Submit your pull request with a clear description of the changes

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License. 