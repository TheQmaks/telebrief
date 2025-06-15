"""
Entry point for running Telebrief as a module.

Usage:
    uv telebrief analyze bloomberg
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
