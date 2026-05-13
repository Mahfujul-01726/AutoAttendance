"""
AutoAttendance Setup Configuration

This is a minimal setup.py for compatibility with older build tools.
All configuration is defined in pyproject.toml.

Usage:
  - For modern builds: python -m build
  - For development: pip install -e .
  - For PyPI release: python publish.py
  - For setup wizard: python setup_wizard.py
"""

from setuptools import setup, find_packages

# All configuration is in pyproject.toml
# This file exists for backward compatibility with older tools
setup(
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
)
