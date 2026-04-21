"""
Simple script to install image handling dependencies.
Run this with: python install_image_deps.py
"""

import subprocess
import sys

def install_packages():
    """Install Pillow and imagehash from public PyPI."""

    packages = [
        'Pillow==10.1.0',
        'imagehash==4.3.1'
    ]

    print("=" * 50)
    print("Installing Image Handling Dependencies")
    print("=" * 50)
    print()
    print("Source: Public PyPI (NOT CodeArtifact)")
    print("Installing:")
    for pkg in packages:
        print(f"  - {pkg}")
    print()

    try:
        # Install using public PyPI explicitly
        cmd = [
            sys.executable,
            '-m',
            'pip',
            'install',
            '--index-url', 'https://pypi.org/simple/',
            '--no-cache-dir'
        ] + packages

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print(result.stdout)

        print()
        print("=" * 50)
        print("✅ Installation Complete!")
        print("=" * 50)
        print()
        print("Installed packages:")
        print("  - Pillow (image processing)")
        print("  - imagehash (visual deduplication)")
        print()
        print("Note: Packages installed in .venv ONLY")
        print("Your other projects remain unaffected")

        return True

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 50)
        print("❌ Installation Failed")
        print("=" * 50)
        print()
        print("Error:", e)
        print()
        print("Output:", e.stdout)
        print("Error:", e.stderr)

        return False

if __name__ == '__main__':
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print()
        print("⚠️  WARNING: Virtual environment not activated!")
        print()
        print("Please activate the virtual environment first:")
        print()
        print("  Command Prompt:")
        print("    .venv\\Scripts\\activate.bat")
        print()
        print("  PowerShell:")
        print("    .\\.venv\\Scripts\\activate.bat")
        print()
        sys.exit(1)

    success = install_packages()
    sys.exit(0 if success else 1)
