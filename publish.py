#!/usr/bin/env python3
"""
PyPI Publishing Script for AutoAttendance

This script guides you through publishing your package to PyPI.
It handles building, testing, and uploading your package.

Usage:
    python publish.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"▶ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error: {result.stderr}")
            return False
        print(f"✓ {description} complete!")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print_header("CHECKING PREREQUISITES")
    
    required_tools = {
        "python": "python --version",
        "pip": "pip --version",
        "git": "git --version"
    }
    
    all_installed = True
    for tool, cmd in required_tools.items():
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {tool}: {result.stdout.strip()}")
            else:
                print(f"✗ {tool}: NOT INSTALLED")
                all_installed = False
        except:
            print(f"✗ {tool}: NOT INSTALLED")
            all_installed = False
    
    return all_installed

def install_build_tools():
    """Install necessary build tools"""
    print_header("INSTALLING BUILD TOOLS")
    
    tools = ["build", "twine", "wheel"]
    cmd = f"pip install {' '.join(tools)}"
    
    return run_command(cmd, "Installing build tools (build, twine, wheel)")

def clean_build_artifacts():
    """Remove old build artifacts"""
    print_header("CLEANING BUILD ARTIFACTS")
    
    dirs_to_remove = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_remove:
        for item in Path(".").glob(pattern):
            if item.is_dir():
                print(f"Removing {item}...")
                shutil.rmtree(item)
            else:
                print(f"Removing {item}...")
                item.unlink()
    
    print("✓ Build artifacts cleaned!")

def build_package():
    """Build the distribution packages"""
    print_header("BUILDING PACKAGE")
    
    success = run_command("python -m build", "Building distribution packages")
    
    if success:
        print("\n📦 Build artifacts created:")
        dist_path = Path("dist")
        if dist_path.exists():
            for file in dist_path.glob("*"):
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  - {file.name} ({size_mb:.2f} MB)")
    
    return success

def validate_package():
    """Validate the package using twine"""
    print_header("VALIDATING PACKAGE")
    
    return run_command("twine check dist/*", "Validating package with twine")

def get_pypi_credentials():
    """Get PyPI credentials from user"""
    print_header("PyPI CREDENTIALS")
    
    print("You need to upload to PyPI. Choose one option:\n")
    print("1. Use API Token (RECOMMENDED)")
    print("   - Create token at: https://pypi.org/manage/account/tokens/")
    print("   - Username: __token__")
    print("   - Password: <your-token>\n")
    
    print("2. Use Username & Password")
    print("   - PyPI account credentials\n")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        token = input("Enter your PyPI API token: ").strip()
        if token:
            return "__token__", token
    elif choice == "2":
        username = input("Enter your PyPI username: ").strip()
        password = input("Enter your PyPI password: ").strip()
        if username and password:
            return username, password
    
    return None, None

def upload_to_pypi(username, password, test=False):
    """Upload package to PyPI"""
    repo = "--repository testpypi" if test else ""
    cmd = f'twine upload dist/* {repo} -u "{username}" -p "{password}"'
    
    description = "Uploading to TestPyPI" if test else "Uploading to PyPI"
    return run_command(cmd, description)

def test_installation():
    """Test installation from PyPI"""
    print_header("TESTING INSTALLATION")
    
    print("Install from PyPI in a fresh environment to verify:")
    print("\n  pip install auto-attendance\n")
    
    print("Then test the CLI:")
    print("\n  auto-attendance --help\n")
    print("  auto-attendance-api --help\n")

def main():
    """Main publishing workflow"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AutoAttendance PyPI Publisher" + " " * 25 + "║")
    print("║" + " " * 20 + "Version 1.0.0" + " " * 36 + "║")
    print("╚" + "=" * 68 + "╝\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites are missing. Please install them first.")
        sys.exit(1)
    
    # Install build tools
    if not install_build_tools():
        print("\n✗ Failed to install build tools")
        sys.exit(1)
    
    # Clean old artifacts
    clean_build_artifacts()
    
    # Build package
    if not build_package():
        print("\n✗ Failed to build package")
        sys.exit(1)
    
    # Validate package
    if not validate_package():
        print("\n⚠️  Package validation failed. Check the errors above.")
        response = input("\nContinue anyway? (y/N): ").strip().lower()
        if response != "y":
            sys.exit(1)
    
    # Ask about test upload
    print_header("OPTIONAL: TEST UPLOAD")
    test_choice = input("Would you like to test upload to TestPyPI first? (y/N): ").strip().lower()
    
    if test_choice == "y":
        test_user, test_pass = get_pypi_credentials()
        if test_user and test_pass:
            if not upload_to_pypi(test_user, test_pass, test=True):
                response = input("Test upload failed. Continue to production? (y/N): ").strip().lower()
                if response != "y":
                    sys.exit(1)
        else:
            print("✗ No credentials provided")
            sys.exit(1)
    
    # Upload to PyPI
    print_header("FINAL UPLOAD TO PyPI")
    username, password = get_pypi_credentials()
    
    if not username or not password:
        print("\n✗ No credentials provided. Aborting.")
        sys.exit(1)
    
    if not upload_to_pypi(username, password, test=False):
        print("\n✗ Upload to PyPI failed")
        sys.exit(1)
    
    # Success
    print_header("✓ PUBLISHING COMPLETE!")
    print("""
📦 Your package is now available on PyPI!

🎉 Next Steps:

1. Share the package:
   pip install auto-attendance

2. View on PyPI:
   https://pypi.org/project/auto-attendance/

3. Update documentation with installation instructions

4. Create a GitHub release:
   git tag v1.0.0
   git push origin v1.0.0
   
""")
    
    test_installation()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Publishing cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
