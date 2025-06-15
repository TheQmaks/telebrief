# Justfile for Telebrief project

# Set shell for Windows compatibility
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Show available commands
default:
    @just --list

# Install dependencies using uv
install:
    @echo "📦 Installing dependencies with uv..."
    uv sync

# Install development dependencies
install-dev:
    @echo "🛠️  Installing development dependencies with uv..."
    uv sync --all-extras

# Sync dependencies (install exact versions from lock file)
sync:
    @echo "🔄 Syncing dependencies..."
    uv sync

# Sync with all extras (dev dependencies)
sync-dev:
    @echo "🔄 Syncing with development dependencies..."
    uv sync --all-extras

# Generate/update lock file
lock:
    @echo "🔒 Updating lock file..."
    uv lock

# Code quality check
lint:
    @echo "🔍 Running ruff linter..."
    uv run ruff check telebrief/

# Code formatting
format:
    @echo "🎨 Formatting code..."
    uv run ruff format telebrief/

# Auto-fix issues
fix:
    @echo "🛠️  Auto-fixing with ruff..."
    uv run ruff check telebrief/ --fix

# Type checking
type-check:
    @echo "🔬 Type checking with mypy..."
    uv run mypy telebrief/

# Run tests
test:
    @echo "🧪 Running tests..."
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    @echo "🧪 Running tests with coverage..."
    uv run pytest tests/ -v --cov=telebrief --cov-report=html --cov-report=term

# Full check (lint + type-check)
check: lint type-check
    @echo "✅ All checks completed!"

# Prepare for commit (format + fix + type-check)
pre-commit: format fix type-check
    @echo "🚀 Code ready for commit!"

# Clean up temporary files
clean:
    @echo "🧹 Cleaning temporary files..."
    @Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Get-ChildItem -Path . -Recurse -Name ".mypy_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Get-ChildItem -Path . -Recurse -Name ".ruff_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Get-ChildItem -Path . -Recurse -Name ".pytest_cache" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    @Get-ChildItem -Path . -Recurse -Name "*.pyc" -File | Remove-Item -Force -ErrorAction SilentlyContinue
    @if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }

# Build package
build:
    @echo "📦 Building package..."
    uv build

# Update dependencies
update:
    @echo "⬆️  Updating dependencies..."
    uv sync --upgrade --all-extras

# Create virtual environment
venv:
    @echo "🐍 Creating virtual environment..."
    uv venv

# Activate virtual environment (show command)
activate:
    @echo "To activate virtual environment, run:"
    @echo "source .venv/bin/activate  # Linux/Mac"
    @echo ".venv\\Scripts\\activate   # Windows"

# Run example
example:
    @echo "🚀 Running example..."
    uv run python examples/example_usage.py

# Analyze a channel (example usage)
analyze channel="bloomberg" days="30":
    @echo "📊 Analyzing @{{channel}} for {{days}} days..."
    uv run telebrief {{channel}} --days {{days}}

# Show project info
info:
    @echo "📋 Project Information:"
    @echo "  Name: telebrief"
    @echo "  Python: $(python --version)"
    @echo "  UV: $(uv --version)"
    @echo "  Virtual env: $VIRTUAL_ENV"

# Help with detailed descriptions
help:
    @echo "🔧 Telebrief Development Commands:"
    @echo ""
    @echo "📦 Installation:"
    @echo "  install      - Install main dependencies"
    @echo "  install-dev  - Install with development dependencies"
    @echo "  sync         - Sync dependencies from lock file"
    @echo "  sync-dev     - Sync with development dependencies"
    @echo "  lock         - Update dependency lock file"
    @echo "  venv         - Create virtual environment"
    @echo ""
    @echo "🔍 Code Quality:"
    @echo "  lint         - Check code with ruff"
    @echo "  format       - Format code with ruff"
    @echo "  fix          - Auto-fix issues with ruff"
    @echo "  type-check   - Type check with mypy"
    @echo "  check        - Full check (lint + type-check)"
    @echo "  pre-commit   - Prepare for commit (format + fix + type-check)"
    @echo ""
    @echo "🧪 Testing:"
    @echo "  test         - Run tests"
    @echo "  test-cov     - Run tests with coverage"
    @echo ""
    @echo "🚀 Usage:"
    @echo "  example      - Run example script"
    @echo "  analyze      - Analyze channel (just analyze bloomberg 30)"
    @echo ""
    @echo "🛠️  Maintenance:"
    @echo "  clean        - Clean temporary files"
    @echo "  build        - Build package"
    @echo "  update       - Update dependencies"
    @echo "  info         - Show project info" 