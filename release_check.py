#!/usr/bin/env python3
"""
PyPI Release Readiness Checker

Verifies that your project is ready for PyPI release.
Run this before publishing to make sure everything is configured correctly.

Usage:
    python release_check.py
"""

import os
import sys
from pathlib import Path

try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def check_file_exists(path, description):
    """Check if file exists"""
    exists = Path(path).exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {path}")
    return exists

def check_content(path, content, description):
    """Check if file contains specific content"""
    if not Path(path).exists():
        print(f"  ✗ {description}: File not found")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        file_content = f.read()
        has_content = content in file_content
        status = "✓" if has_content else "✗"
        print(f"  {status} {description}")
        return has_content

def main():
    """Run all checks"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PyPI Release Readiness Check".center(68) + "║")
    print("║" + "  AutoAttendance".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    all_good = True
    
    # Check package configuration
    print_header("Package Configuration")
    all_good &= check_file_exists("pyproject.toml", "pyproject.toml exists")
    all_good &= check_content("pyproject.toml", 'name = "auto-attendance"', 
                              "Package name configured")
    all_good &= check_content("pyproject.toml", 'version = "1.0.0"', 
                              "Version defined")
    all_good &= check_content("pyproject.toml", "[project.scripts]", 
                              "CLI entry points defined")
    
    # Check build files
    print_header("Build Files")
    all_good &= check_file_exists("setup.py", "setup.py exists")
    all_good &= check_file_exists("MANIFEST.in", "MANIFEST.in exists")
    all_good &= check_file_exists("README.md", "README.md exists")
    all_good &= check_file_exists("LICENSE", "LICENSE file exists")
    
    # Check documentation
    print_header("Documentation")
    all_good &= check_file_exists("PUBLISHING.md", "PUBLISHING.md exists")
    all_good &= check_file_exists("PYPI_SETUP.md", "PYPI_SETUP.md exists")
    all_good &= check_file_exists("RELEASE_READY.md", "RELEASE_READY.md exists")
    
    # Check publishing setup
    print_header("Publishing Setup")
    all_good &= check_file_exists("publish.py", "publish.py script exists")
    all_good &= check_file_exists(".github/workflows/publish-to-pypi.yml", 
                                  "GitHub Actions workflow exists")
    
    # Check distribution
    print_header("Distribution Packages")
    dist_exists = Path("dist").exists()
    if dist_exists:
        dist_files = list(Path("dist").glob("*.whl")) + list(Path("dist").glob("*.tar.gz"))
        if dist_files:
            print(f"  ✓ Distribution packages built ({len(dist_files)} files)")
            for f in dist_files:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"    - {f.name} ({size_mb:.2f} MB)")
        else:
            print(f"  ✗ No distribution packages found in dist/")
            all_good = False
    else:
        print(f"  ⚠ dist/ directory not found")
        print(f"    Run: python -m build")
    
    # Check project structure
    print_header("Project Structure")
    all_good &= check_file_exists("auto_attendance/__init__.py", "Package __init__.py")
    all_good &= check_file_exists("auto_attendance/cli.py", "CLI module")
    all_good &= check_file_exists("auto_attendance/api.py", "API module")
    all_good &= check_file_exists("auto_attendance/face_recognition.py", 
                                  "Face recognition module")
    
    # Requirements
    print_header("Requirements")
    all_good &= check_file_exists("requirements.txt", "requirements.txt exists")
    
    # Final summary
    print_header("Summary")
    
    if all_good:
        print("""
  ✓ ALL CHECKS PASSED! 🎉
  
  Your project is ready for PyPI release!
  
  Next steps:
  
  1. Read: RELEASE_READY.md
  2. Choose publishing method:
     a) Automated: Push to GitHub + create release
     b) Manual: Run python publish.py
  3. Enter your PyPI API token when prompted
  4. Wait 2-3 minutes for PyPI to process
  5. Verify at: https://pypi.org/project/auto-attendance/
  
  For detailed instructions, see PUBLISHING.md
        """)
        return 0
    else:
        print("""
  ⚠ SOME CHECKS FAILED
  
  Issues found:
  - Review the checks above (marked with ✗)
  - Make necessary corrections
  - Rerun this script
  
  Common fixes:
  - Build packages: python -m build
  - Check pyproject.toml syntax
  - Verify all files are in place
  
  For help, see PUBLISHING.md
        """)
        return 1

if __name__ == "__main__":
    sys.exit(main())
